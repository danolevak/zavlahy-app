from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Crop(models.Model):
    name = models.CharField(max_length = 120, unique = True)

    #  Kc hodnoty podľa fenofáz
    kc_ini = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    kc_mid = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    kc_end = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # dĺžka fenofáz
    stage_ini_days = models.PositiveIntegerField(null=True, blank=True)
    stage_dev_days = models.PositiveIntegerField(null=True, blank=True)
    stage_mid_days = models.PositiveIntegerField(null=True, blank=True)
    stage_late_days = models.PositiveIntegerField(null=True, blank=True)

    # hĺbka zakorenenia (Zr) v metroch – môže byť rozsah
    root_depth_min_m = models.DecimalField(max_digits = 4, decimal_places = 2)
    root_depth_max_m = models.DecimalField(max_digits = 4, decimal_places = 2)

    #p (frakcia vyčerpania)
    p = models.DecimalField(
        max_digits = 4, 
        decimal_places = 2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("1.00"))]
    )

    def kc_default(self) -> Decimal:
        values = [v for v in [self.kc_ini, self.kc_mid, self.kc_end] if v is not None]
        if not values:
            return Decimal("0.00")
        return sum(values) / Decimal(len(values))

    def root_depth_default(self) -> Decimal:
        return (self.root_depth_min_m + self.root_depth_max_m) / Decimal("2.0")

    def __str__(self):
        return f"{self.name} (Kc {self.kc_ini} / {self.kc_mid} / {self.kc_end})"
    

class SoilType(models.Model):
    name = models.CharField(max_length = 120, unique = True)

    theta_fc_min = models.DecimalField(max_digits = 5, decimal_places = 3)
    theta_fc_max = models.DecimalField(max_digits = 5, decimal_places = 3)

    theta_wp_min = models.DecimalField(max_digits = 5, decimal_places = 3)
    theta_wp_max = models.DecimalField(max_digits = 5, decimal_places = 3)

    def theta_fc_default(self) -> Decimal:
        return (self.theta_fc_min + self.theta_fc_max) / Decimal("2.0")

    def theta_wp_default(self) -> Decimal:
        return (self.theta_wp_min + self.theta_wp_max) / Decimal("2.0")
    
    def available_water_default(self) -> Decimal:
        "(θFC - θWP) [m3/m3]"
        return self.theta_fc_default() - self.theta_wp_default()

    def __str__(self) -> Decimal:
        return self.name
    
class Field(models.Model):
    name = models.CharField(max_length = 100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    crop = models.ForeignKey(Crop, on_delete=models.PROTECT, null=True, blank=True)
    soil_type = models.ForeignKey(SoilType, on_delete=models.PROTECT, null=True, blank=True)

    sowing_date = models.DateField(null=True, blank=True)

    root_depth_override_m = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    p_override = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    def root_depth_effective(self) -> Decimal | None:
        if self.root_depth_override_m is not None:
            return self.root_depth_override_m
        return self.crop.root_depth_default() if self.crop else None

    def p_effective(self) -> Decimal | None:
        if self.p_override is not None:
            return self.p_override
        return self.crop.p if self.crop else None

    def __str__(self):
        return self.name
    
class SoilMoistureSensor(models.Model):
    SENSOR_OUTPUT_CHOICES = [
        ("analog_mv", "Analóg mV"),
        ("analog_v", "Analóg V"),
        ("api", "API/platforma"),
        ("manual", "Ručný vstup"),
    ]

    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name="soil_sensors"
    )
    name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100, blank=True, null=True)

    output_type = models.CharField(
        max_length=20,
        choices=SENSOR_OUTPUT_CHOICES,
        default="manual"
    )

    installation_depth_cm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.model})"
    
class SoilMoistureMeasurement(models.Model):
    sensor = models.ForeignKey(
        SoilMoistureSensor,
        on_delete=models.CASCADE,
        related_name="measurements"
    )

    measured_at = models.DateTimeField()

    raw_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    raw_unit = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    vwc_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    temperature_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    source = models.CharField(
        max_length=50,
        default="manual"
    )

    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-measured_at",)

    def __str__(self):
        return f"{self.sensor.name} - {self.measured_at}"
    
class ET0Daily(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    date = models.DateField()

    et0_mm = models.FloatField()
    rain_mm = models.FloatField(default=0)

    source = models.CharField(max_length=50, default="open-meteo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("field", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.field.name} - {self.date} - ET0 {self.et0_mm} mm - Rain {self.rain_mm} mm"
    
    
    