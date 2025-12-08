import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов из JSON файла"

    def handle(self, *args, **options):
        json_file_path = os.path.join(
            settings.BASE_DIR.parent, "data", "ingredients.json"
        )

        try:
            if not os.path.exists(json_file_path):
                self.stdout.write(self.style.ERROR(f"Файл {json_file_path} не найден!"))
                return

            with open(json_file_path, "r", encoding="utf-8") as file:
                ingredients_data = json.load(file)

            ingredients_to_create = []
            for item in ingredients_data:
                if not Ingredient.objects.filter(
                    name=item["name"], measurement_unit=item["measurement_unit"]
                ).exists():
                    ingredients_to_create.append(
                        Ingredient(
                            name=item["name"],
                            measurement_unit=item["measurement_unit"],
                        )
                    )

            if ingredients_to_create:
                Ingredient.objects.bulk_create(ingredients_to_create)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Успешно загружено {len(ingredients_to_create)} ингредиентов"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("Все ингредиенты уже загружены в базу данных")
                )

        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при парсинге JSON файла: {e}"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Произошла ошибка при загрузке данных: {e}")
            )
