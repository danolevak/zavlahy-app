from django.contrib import admin
from .models import Field, Crop, SoilType, ET0Daily, SoilMoistureSensor, SoilMoistureMeasurement

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("name", "crop", "soil_type", "sowing_date", "latitude", "longitude")
    search_fields = ("name",)
    list_filter = ("crop", "soil_type")


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("name", "kc_ini", "kc_mid", "kc_end")
    search_fields = ("name",)


@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "theta_fc_min",
        "theta_fc_max",
        "theta_wp_min",
        "theta_wp_max",
    )
    search_fields = ("name",)


@admin.register(ET0Daily)
class ET0DailyAdmin(admin.ModelAdmin):
    list_display = ("date", "field", "et0_mm", "rain_mm", "source")
    list_filter = ("field",)
    search_fields = ("field__name",)
    ordering = ("-date",)

@admin.register(SoilMoistureSensor)
class SoilMoistureSensorAdmin(admin.ModelAdmin):
    list_display = ("name", "field", "manufacturer", "model", "output_type", "installation_depth_cm", "is_active")
    list_filter = ("output_type", "is_active", "manufacturer")
    search_fields = ("name", "model", "serial_number", "field__name")


@admin.register(SoilMoistureMeasurement)
class SoilMoistureMeasurementAdmin(admin.ModelAdmin):
    list_display = ("measured_at", "sensor", "vwc_percent", "raw_value", "raw_unit", "temperature_c", "source")
    list_filter = ("source", "sensor")
    search_fields = ("sensor__name", "sensor__field__name")
    ordering = ("-measured_at",)
