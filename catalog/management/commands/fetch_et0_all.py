from django.core.management.base import BaseCommand
from catalog.models import Field
from catalog.services import store_et0_for_field


class Command(BaseCommand):
    help = "Stiahne ET0 a zrážky za posledných 14 dní pre všetky polia"
    def handle(self, *args, **options):
        fields = Field.objects.all()

        if not fields.exists():
            self.stdout.write(self.style.WARNING("Nie sú evidované žiadne polia."))
            return

        total_saved = 0
        total_updated = 0

        for field in fields:
            try:
                result = store_et0_for_field(field.id, days=14)

                saved = result.get("saved", 0)
                updated = result.get("updated", 0)

                total_saved += saved
                total_updated += updated

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Pole '{field.name}' → saved={saved}, updated={updated}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Pole '{field.name}' → chyba: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Hotovo. Celkom saved={total_saved}, updated={total_updated}"
            )
        )