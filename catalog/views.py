import json
import requests

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from decimal import Decimal
from datetime import datetime, date, timedelta
from datetime import date as dt_date

from .models import Crop, SoilType, Field, ET0Daily, SoilMoistureMeasurement, SoilMoistureSensor

from .services import (
    get_day_of_season,
    get_kc_for_day,
    calculate_cumulative_depletion,
    convert_raw_to_vwc_percent,
    store_et0_for_field
)

from django.shortcuts import render

def irrigation_today(request, field_id):
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
    p = crop.p

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
    

    return JsonResponse(
        {
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

            "zavlazovat": result.get("Zavlazovat", False),
            "doporucana_davka_mm": float(result.get("Odporucana_davka_mm", 0)),
            "vodny_deficit_mm": round(float(result.get("Aktualny_vodny_deficit_mm", 0)), 2),

            "sprava": result.get("Sprava"),
            "sensor_adjustment_note": sensor_adjustment_note,
            "sensor_deficit_mm": round(float(dr_sensor), 2) if latest_soil_measurement and latest_soil_measurement.vwc_percent is not None else None,
            "soil_moisture_sensor": {
                "has_data": latest_soil_measurement is not None,
                "vwc_percent": float(latest_soil_measurement.vwc_percent) if latest_soil_measurement and latest_soil_measurement.vwc_percent is not None else None,
                "measured_at": latest_soil_measurement.measured_at.isoformat() if latest_soil_measurement else None,
                "sensor_name": latest_soil_measurement.sensor.name if latest_soil_measurement else None,
            },
        },
        json_dumps_params={"ensure_ascii": False},
)


@require_http_methods(["GET", "POST"])
def fetch_et0_for_field(request, field_id):
    days = int(request.GET.get("days", 7))
    result = store_et0_for_field(field_id, days)
    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})

def _to_iso(d):
    if hasattr(d, "isoformat"):
        return d.isoformat()
    
    if isinstance(d, str):
        d = d.strip()

        if "-" in d:
            return d
        
        if "." in d:
            parts = d.replace(" ","").split(".")
            if len (parts) >=3:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                return dt_date(year, month, day).isoformat()
    return None

def et0_history(request, field_id):
    days = int(request.GET.get("days", 30))
    since = date.today() - timedelta(days = days -1)

    rows = (
        ET0Daily.objects
        .filter(field_id = field_id, date__gte = since)
        .order_by("date")
        .values("date", "et0_mm","rain_mm", "source")
    )

    data = [
        {
            "date": _to_iso(r["date"]),
            "et0_mm": r["et0_mm"],
            "rain_mm": r["rain_mm"],
            "source": r["source"],
        }
        for r in rows
    ]

    return JsonResponse(
        {"field_id": field_id, "days": days, "count": len(data), "data": data},
        json_dumps_params={"ensure_ascii": False}
    )

def fields_list(request):
    fields = Field.objects.select_related("crop", "soil_type").all()

    data = []
    for f in fields:
        data.append({
            "id": f.id,
            "name": f.name,
            "latitude": f.latitude,
            "longitude": f.longitude,
            "crop_id": f.crop_id,
            "crop_name": f.crop.name if f.crop else None,
            "soil_type_id": f.soil_type_id,
            "soil_type_name": f.soil_type.name if f.soil_type else None,
            "sowing_date": f.sowing_date.isoformat() if f.sowing_date else None,
            "root_depth_override_m": float(f.root_depth_override_m) if f.root_depth_override_m is not None else None,
            "p_override": float(f.p_override) if f.p_override is not None else None,
        })

    return JsonResponse(data, safe=False, json_dumps_params={"ensure_ascii": False})

def crops_list(request):
    rows = Crop.objects.all().order_by("name").values(
        "id", "name", "kc_ini", "kc_mid", "kc_end"
    )
    return JsonResponse(list(rows), safe=False, json_dumps_params={"ensure_ascii": False})

def weather_current (request, field_id):
    field = Field.objects.get(id = field_id)

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={field.latitude}&longitude={field.longitude}"
        "&current=temperature_2m,wind_speed_10m,weather_code"
        "&timezone=auto"
    )

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    j = r.json()

    cur = j.get("current", {})
    return JsonResponse({
        "field_id": field_id,
        "time": cur.get("time"),
        "temperature_c": cur.get("temperature_2m"),
        "wind_m_s": cur.get("wind_speed_10m"),
        "weather_code": cur.get("weather_code"),
    }, json_dumps_params={"ensure_ascii": False})

@csrf_exempt
@require_http_methods(["POST"])
def moisture_sensor_ingest(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Neplatný JSON"},
            status=400,
            json_dumps_params={"ensure_ascii": False}
        )

    sensor_id = data.get("sensor_id")
    if not sensor_id:
        return JsonResponse(
            {"error": "Chýba sensor_id"},
            status=400,
            json_dumps_params={"ensure_ascii": False}
        )

    try:
        sensor = SoilMoistureSensor.objects.select_related("field").get(
            id=sensor_id,
            is_active=True
        )
    except SoilMoistureSensor.DoesNotExist:
        return JsonResponse(
            {"error": "Senzor neexistuje alebo nie je aktívny"},
            status=404,
            json_dumps_params={"ensure_ascii": False}
        )

    measured_at_raw = data.get("measured_at")
    if measured_at_raw:
        try:
            measured_at = datetime.fromisoformat(measured_at_raw)
            if timezone.is_naive(measured_at):
                measured_at = timezone.make_aware(measured_at, timezone.get_current_timezone())
        except ValueError:
            return JsonResponse(
                {"error": "Neplatný formát measured_at. Očakáva sa ISO formát."},
                status=400,
                json_dumps_params={"ensure_ascii": False}
            )
    else:
        measured_at = timezone.now()

    raw_value = data.get("raw_value")
    raw_unit = data.get("raw_unit")
    vwc_percent = data.get("vwc_percent")
    temperature_c = data.get("temperature_c")
    source = data.get("source", "manual")
    note = data.get("note")

    # ak prišlo raw_value ale nie vwc_percent → prepočítaj
    if vwc_percent is None and raw_value is not None:
        converted = convert_raw_to_vwc_percent(sensor, raw_value)
        if converted is not None:
            vwc_percent = converted

    if vwc_percent is None and raw_value is None:
        return JsonResponse(
            {"error": "Musí prísť aspoň vwc_percent alebo raw_value"},
            status=400,
            json_dumps_params={"ensure_ascii": False}
        )

    measurement = SoilMoistureMeasurement.objects.create(
        sensor=sensor,
        measured_at=measured_at,
        raw_value=raw_value,
        raw_unit=raw_unit,
        vwc_percent=vwc_percent,
        temperature_c=temperature_c,
        source=source,
        note=note,
    )

    irrigation_response = irrigation_today(request, sensor.field.id)
    irrigation_data = json.loads(irrigation_response.content.decode("utf-8"))

    return JsonResponse(
        {
            "message": "Meranie bolo uložené",
            "measurement": {
                "id": measurement.id,
                "sensor_id": sensor.id,
                "sensor_name": sensor.name,
                "field_id": sensor.field.id,
                "measured_at": measurement.measured_at.isoformat(),
                "raw_value": float(measurement.raw_value) if measurement.raw_value is not None else None,
                "raw_unit": measurement.raw_unit,
                "vwc_percent": float(measurement.vwc_percent) if measurement.vwc_percent is not None else None,
                "temperature_c": float(measurement.temperature_c) if measurement.temperature_c is not None else None,
                "source": measurement.source,
                "note": measurement.note,
            },
            "irrigation": irrigation_data,
        },
        json_dumps_params={"ensure_ascii": False}
    )

def latest_soil_moisture(request, field_id):
    measurement = (
        SoilMoistureMeasurement.objects
        .filter(sensor__field_id=field_id)
        .order_by("-measured_at")
        .first()
    )

    if not measurement:
        return JsonResponse(
            {"field_id": field_id, "has_data": False},
            json_dumps_params={"ensure_ascii": False}
        )

    return JsonResponse(
        {
            "field_id": field_id,
            "has_data": True,
            "sensor": measurement.sensor.name,
            "vwc_percent": float(measurement.vwc_percent) if measurement.vwc_percent else None,
            "temperature_c": float(measurement.temperature_c) if measurement.temperature_c else None,
            "measured_at": measurement.measured_at.isoformat()
        },
        json_dumps_params={"ensure_ascii": False}
    )

def dashboard(request):
    return render(request, "index.html")
