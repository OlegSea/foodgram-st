import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из JSON файла в базу данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            type=str,
            default="data/ingredients.json",
            help="Путь к JSON файлу с ингредиентами (по умолчанию: data/ingredients.json)",
        )

    def handle(self, *args, **options):
        file_path = Path(options["path"])

        if not file_path.is_absolute():
            file_path = Path(__file__).resolve().parents[4] / file_path

        if not file_path.exists():
            raise CommandError(f"Файл не найден: {file_path}")

        self.stdout.write(f"Загрузка ингредиентов из {file_path}...")

        with open(file_path, encoding="utf-8") as f:
            ingredients_data = json.load(f)

        created_count = 0
        skipped_count = 0

        for item in ingredients_data:
            _, created = Ingredient.objects.get_or_create(
                name=item["name"],
                measurement_unit=item["measurement_unit"],
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Загрузка завершена. "
                f"Создано: {created_count}, пропущено (уже существуют): {skipped_count}"
            )
        )
