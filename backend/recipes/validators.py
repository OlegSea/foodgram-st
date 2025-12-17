from collections import Counter

from rest_framework import serializers


def validate_ingredients_uniqueness(ingredients_data):
    if not ingredients_data:
        raise serializers.ValidationError(
            "Необходимо добавить хотя бы один ингредиент."
        )

    ingredient_ids = [item["id"].id for item in ingredients_data]
    unique_ids = set(ingredient_ids)

    if len(ingredient_ids) != len(unique_ids):
        duplicates = [
            str(id) for id, count in Counter(ingredient_ids).items() if count > 1
        ]
        raise serializers.ValidationError(
            f"Ингредиенты не должны повторяться. Дубли: {duplicates}"
        )

    return ingredients_data
