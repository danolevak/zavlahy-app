from decimal import Decimal
from datetime import date, timedelta, datetime
from catalog.models import Field, ET0Daily
import requests

def get_et0(latitude, longitude, days = 7):
    
    end_date = date.today()
    start_date = end_date - timedelta(days = days-1)
    
    url="https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":f"{latitude}",
        "longitude": f"{longitude}",
        "daily": "et0_fao_evapotranspiration,precipitation_sum",
        "timezone": "UTC",
        "past_days": days - 1,
        "forecast_days": 1,
        "format": "json",
    }

    r = requests.get(url, params=params, timeout=10)
    print("FINAL URL:", r.url)
    if not r.ok:
        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)
        r.raise_for_status()
    data = r.json()

    try:
        dates = data["daily"]["time"]
        et0_values = data["daily"]["et0_fao_evapotranspiration"]
        rain_values = data["daily"]["precipitation_sum"]
    except (KeyError, TypeError):
        return []

    return [
        {"date": d, "et0": e, "rain": r}
        for d, e, r in zip(dates, et0_values, rain_values)
    ]
    
def store_et0_for_field(field_id, days = 7):
    field = Field.objects.get(id = field_id)

    et0_list = get_et0(field.latitude, field.longitude, days)

    saved = 0
    updated = 0

    for item in et0_list:
        d = datetime.fromisoformat(item["date"]).date()
        et0_value = item["et0"]
        rain_value = item.get("rain", 0)

        obj, created = ET0Daily.objects.update_or_create(
        field=field,
        date=d,
        defaults={
            "et0_mm": et0_value,
            "rain_mm": rain_value,
            "source": "open-meteo",
        }
    )

        if created:
            saved += 1
        else:
            updated += 1
    cutoff = date.today() - timedelta(days=13)

    ET0Daily.objects.filter(
        field_id=field_id,
        date__lt=cutoff
    ).delete()
    return {"saved": saved, "updated": updated, "count": len(et0_list)}

def get_latest_et0_from_db(field_id):
    row = ET0Daily.objects.filter(field_id = field_id).order_by("-date").first()
    if not row:
        return None
    return row.et0_mm

def calculate_irrigation(current_deficit, taw, raw):
    if current_deficit < 0:
        current_deficit = Decimal("0")

    if current_deficit > taw:
        current_deficit = taw

    irrigate = current_deficit > raw
    inet = Decimal("0")

    if irrigate:
        inet = current_deficit - raw

    sprava = "Odporúčanie: nezavlažovať."
    if irrigate:
        sprava = f"Odporúčanie: zavlažovať. Dávka ~{inet:.2f} mm (≈{inet:.2f} l/m²)."

    return {
        "Zavlazovat": irrigate,
        "Odporucana_davka_mm": inet,
        "Odporucana_davka_l_na_m2": inet,
        "Aktualny_vodny_deficit_mm": current_deficit,
        "Hranica_bez_stresu_mm": raw,
        "Zasoba_dostupnej_vody_v_korenoch_mm": taw,
        "Sprava": sprava,
    }

def get_day_of_season(sowing_date):
    if not sowing_date:
        return None

    today = date.today()
    day_of_season = (today - sowing_date).days + 1

    if day_of_season < 1:
        return 1

    return day_of_season

def get_kc_for_day(crop, day_of_season):
    if day_of_season is None:
        return crop.kc_default()

    if (
        crop.kc_ini is None or
        crop.kc_mid is None or
        crop.kc_end is None or
        crop.stage_ini_days is None or
        crop.stage_dev_days is None or
        crop.stage_mid_days is None or
        crop.stage_late_days is None
    ):
        return crop.kc_default()

    kc_ini = Decimal(str(crop.kc_ini))
    kc_mid = Decimal(str(crop.kc_mid))
    kc_end = Decimal(str(crop.kc_end))

    ini_end = crop.stage_ini_days
    dev_end = ini_end + crop.stage_dev_days
    mid_end = dev_end + crop.stage_mid_days
    late_end = mid_end + crop.stage_late_days

    if day_of_season <= ini_end:
        return kc_ini

    if day_of_season <= dev_end:
        pos = day_of_season - ini_end
        frac = Decimal(pos) / Decimal(crop.stage_dev_days)
        return kc_ini + (kc_mid - kc_ini) * frac

    if day_of_season <= mid_end:
        return kc_mid

    if day_of_season <= late_end:
        pos = day_of_season - mid_end
        frac = Decimal(pos) / Decimal(crop.stage_late_days)
        return kc_mid + (kc_end - kc_mid) * frac

    return kc_end

def calculate_cumulative_depletion(et0_rows, crop, taw, sowing_date):
    dr = Decimal("0")  # deficit na začiatku (po sejbe = 0)
    history = []

    for row in et0_rows:
        et0 = Decimal(str(row["et0_mm"] or 0))
        rain = Decimal(str(row["rain_mm"] or 0))

        row_date = row["date"]
        if hasattr(row_date, "isoformat"):
            row_date_value = row_date
        else:
            row_date_value = date.fromisoformat(str(row_date))

        if hasattr(row_date_value, "date"):
            row_date_value = row_date_value.date()

        # deň vegetácie
        day_of_season = (row_date_value - sowing_date).days + 1

        # Kc + ETc
        kc = get_kc_for_day(crop, day_of_season)
        etc = et0 * kc

        # 🔥 HLAVNÁ ROVNICA (kumulatívny deficit)
        dr = dr + etc - rain

        # orezanie podľa FAO
        if dr < 0:
            dr = Decimal("0")

        if dr > taw:
            dr = taw

        history.append({
            "date": row_date_value.isoformat(),
            "et0_mm": float(et0),
            "rain_mm": float(rain),
            "kc": float(round(kc, 3)),
            "etc_mm": float(round(etc, 3)),
            "depletion_mm": float(round(dr, 3)),  # toto je kumulatívny deficit
        })

    return history
def convert_raw_to_vwc_percent(sensor, raw_value):
    model = (sensor.model or "").strip().upper()
    raw = Decimal(str(raw_value))

    if model == "TEROS 10":
        vwc = raw * Decimal("0.0003879") - Decimal("0.6956")
        return max(Decimal("0"), min(vwc * Decimal("100"), Decimal("100")))

    if model == "VH400":
        vwc = raw * Decimal("0.1")
        return max(Decimal("0"), min(vwc, Decimal("100")))

    return None