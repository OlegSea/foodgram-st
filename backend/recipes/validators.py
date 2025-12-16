import re

from rest_framework import serializers


def validate_username(value):
    if not re.match(r"^[\w.@+-]+\Z", value):
        raise serializers.ValidationError(
            "Username может содержать только буквы, цифры и символы @/./+/-/_."
        )
    if value.lower() == "me":
        raise serializers.ValidationError(
            "Использовать имя 'me' в качестве username запрещено."
        )
    return value


def validate_ingredients_uniqueness(ingredients_data):
    if not ingredients_data:
        raise serializers.ValidationError(
            "Необходимо добавить хотя бы один ингредиент."
        )

    ingredient_ids = [item["id"] for item in ingredients_data]
    unique_ids = set(ingredient_ids)

    if len(ingredient_ids) != len(unique_ids):
        duplicates = []
        seen = set()
        for ingredient_id in ingredient_ids:
            if ingredient_id in seen and ingredient_id not in duplicates:
                duplicates.append(str(ingredient_id))
            seen.add(ingredient_id)

        raise serializers.ValidationError(
            f"Ингредиенты не должны повторяться. Дубли: {', '.join(duplicates)}"
        )

    return ingredients_data
