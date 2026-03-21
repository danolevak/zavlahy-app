from decimal import Decimal
from datetime import date, timedelta, datetime
from catalog.models import Field, ET0Daily
import requests

def get_et0(latitude, longitude, days=14):
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": f"{latitude}",
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
    
def store_et0_for_field(field_id, fallback_days=14):
    field = Field.objects.get(id=field_id)
    today = date.today()

    if field.sowing_date:
        days = (today - field.sowing_date).days + 1
        if days < 1:
            days = 1
        from_sowing = True
    else:
        days = fallback_days
        from_sowing = False

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

    if not from_sowing:
        cutoff = today - timedelta(days=fallback_days - 1)
        ET0Daily.objects.filter(
            field=field,
            date__lt=cutoff
        ).delete()

    return {
        "saved": saved,
        "updated": updated,
        "count": len(et0_list),
        "days_used": days,
        "from_sowing": from_sowing,
        "sowing_date": field.sowing_date.isoformat() if field.sowing_date else None,
    }

def get_latest_et0_from_db(field_id):
    row = (
        ET0Daily.objects
        .filter(field_id=field_id, et0_mm__isnull=False)
        .order_by("-date")
        .first()
    )

    if not row:
        return None

    return {
        "date": row.date,
        "et0": row.et0_mm,
        "rain": row.rain_mm,
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
        effective_rain = rain * Decimal("0.80")

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

        # HLAVNÁ ROVNICA (kumulatívny deficit)
        dr = dr + etc - effective_rain

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

def calculate_irrigation_for_field(field_id, crop_override_id=None):
    # načítaj pole
    try:
        field = Field.objects.get(id=field_id)
    except Field.DoesNotExist:
        return JsonResponse({"error": "Neznáme pole"}, status=404)
    
    day_of_season = get_day_of_season(field.sowing_date)

    # crop_id môže prísť z Reactu cez query parameter
    crop_id = request.GET.get("crop_id")

    if crop_id:
        try:
            crop = Crop.objects.get(id=crop_id)
        except Crop.DoesNotExist:
            return JsonResponse({"error": "Neznáma plodina"}, status=404)
    else:
        if not field.crop_id:
            return JsonResponse({"error": "Pole nemá priradenú plodinu"}, status=400)
        crop = field.crop

    # pôda ostáva zatiaľ z poľa
    if not field.soil_type_id:
        return JsonResponse({"error": "Pole nemá priradený typ pôdy"}, status=400)

    soil = field.soil_type

    # posledné ET0 z DB
    row = ET0Daily.objects.filter(field_id=field_id).order_by("-date").first()
    if not row:
        return JsonResponse({"error": "Nemám ET0 dáta pre toto pole"}, status=404)

    et0 = Decimal(str(row.et0_mm))
    kc = get_kc_for_day(crop, day_of_season)
    etc = et0 * kc

    # efektívne hodnoty pre pole
    zr = crop.root_depth_default()
    p = field.p_effective()

    if zr is None:
        return JsonResponse({"error": "Nie je určená hĺbka zakorenenia"}, status=400)

    if p is None:
        return JsonResponse({"error": "Nie je určená hodnota p"}, status=400)

    # FAO-56 TAW/RAW
    taw = (soil.theta_fc_default() - soil.theta_wp_default()) * zr * Decimal("1000")
    raw = p * taw
    rain = Decimal(str(row.rain_mm or 0))

    history_rows = (
        ET0Daily.objects
        .filter(field_id=field_id, date__gte=field.sowing_date)
        .order_by("date")
        .values("date", "et0_mm", "rain_mm")
    )

    depletion_history = calculate_cumulative_depletion(history_rows, crop, taw, field.sowing_date)

    current_deficit = Decimal("0")
    if depletion_history:
        current_deficit = Decimal(str(depletion_history[-1]["depletion_mm"]))

    irrigate = current_deficit > raw
    recommended_dose = Decimal("0")

    if irrigate:
        recommended_dose = current_deficit - raw

    sprava = "Odporúčanie: nezavlažovať."
    if irrigate:
        sprava = f"Odporúčanie: zavlažovať. Dávka ~{recommended_dose:.2f} mm (≈{recommended_dose:.2f} l/m²)."

    result = {
        "Zavlazovat": irrigate,
        "Odporucana_davka_mm": recommended_dose,
        "Odporucana_davka_l_na_m2": recommended_dose,
        "Aktualny_vodny_deficit_mm": current_deficit,
        "Hranica_bez_stresu_mm": raw,
        "Zasoba_dostupnej_vody_v_korenoch_mm": taw,
        "Sprava": sprava,
    }

    latest_soil_measurement = (
        SoilMoistureMeasurement.objects
        .filter(sensor__field_id=field_id)
        .order_by("-measured_at")
        .first()
    )

    sensor_adjustment_note = None

    if latest_soil_measurement and latest_soil_measurement.vwc_percent is not None:
        vwc = Decimal(str(latest_soil_measurement.vwc_percent)) / Decimal("100")
        theta_fc = soil.theta_fc_default()
        theta_wp = soil.theta_wp_default()

        if vwc >= theta_fc:
            dr_sensor = Decimal("0")
        elif vwc <= theta_wp:
            dr_sensor = taw
        else:
            dr_sensor = (theta_fc - vwc) * zr * Decimal("1000")

        if dr_sensor < 0:
            dr_sensor = Decimal("0")

        if dr_sensor > taw:
            dr_sensor = taw

        current_deficit = dr_sensor
        irrigate = current_deficit > raw
        recommended_dose = Decimal("0")

        if irrigate:
            recommended_dose = current_deficit - raw

        sprava = "Odporúčanie: nezavlažovať."
        if irrigate:
            sprava = f"Odporúčanie: zavlažovať. Dávka ~{recommended_dose:.2f} mm (≈{recommended_dose:.2f} l/m²)."

        result = {
            "Zavlazovat": irrigate,
            "Odporucana_davka_mm": recommended_dose,
            "Odporucana_davka_l_na_m2": recommended_dose,
            "Aktualny_vodny_deficit_mm": current_deficit,
            "Hranica_bez_stresu_mm": raw,
            "Zasoba_dostupnej_vody_v_korenoch_mm": taw,
            "Sprava": sprava,
        }

        sensor_adjustment_note = (
            f"Výpočet bol korigovaný podľa senzora. "
            f"Odhadnutý deficit zo senzora: {round(float(dr_sensor), 2)} mm."
        )
    

    return {
        "field_id": field_id,
        "date": row.date.isoformat(),

        "crop": {
            "id": crop.id,
            "name": crop.name,
            "kc": round(float(kc), 3)
        },
        "soil": {
            "id": soil.id,
            "name": soil.name
        },

        "et0_mm": round(float(et0), 3),
        "etc_mm": round(float(etc), 3),
        "rain_mm": float(rain),
        "day_of_season": day_of_season,

        "zr_m": float(zr),
        "taw_mm": float(taw),
        "raw_mm": float(raw),

        "zavlazovat": irrigate,
        "doporucana_davka_mm": float(recommended_dose),
        "vodny_deficit_mm": round(float(current_deficit), 2),

        "sprava": sprava,
        "sensor_adjustment_note": sensor_adjustment_note,
        "sensor_deficit_mm": round(float(dr_sensor), 2) if latest_soil_measurement and latest_soil_measurement.vwc_percent is not None else None,
    }