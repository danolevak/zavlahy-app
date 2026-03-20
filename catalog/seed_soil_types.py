from decimal import Decimal
from .models import SoilType

def seed_soil_types():

    soil_types = [
        ("Piesočnatá", 0.07, 0.17, 0.02, 0.07),
        ("Hlinito-piesočnatá", 0.11, 0.19, 0.03, 0.10),
        ("Piesočnato-hlinitá", 0.18, 0.28, 0.06, 0.16),
        ("Hlinitá", 0.20, 0.30, 0.07, 0.17),
        ("Prachovito-hlinitá", 0.22, 0.36, 0.09, 0.21),
        ("Prachovitá", 0.28, 0.36, 0.12, 0.22),
        ("Prachovito-ílovo-hlinitá", 0.30, 0.37, 0.17, 0.24),
        ("Prachovito-ílová", 0.30, 0.42, 0.17, 0.29),
        ("Ílová", 0.32, 0.40, 0.20, 0.24),
    ]

    for name, fc_min, fc_max, wp_min, wp_max in soil_types:

        SoilType.objects.update_or_create(
            name=name,
            defaults={
                "theta_fc_min": Decimal(str(fc_min)),
                "theta_fc_max": Decimal(str(fc_max)),
                "theta_wp_min": Decimal(str(wp_min)),
                "theta_wp_max": Decimal(str(wp_max)),
            }
        )

    print("Soil types imported successfully.")