from rest_framework import serializers


def validate_ingredients_uniqueness(ingredients_data):
    if not ingredients_data:
        raise serializers.ValidationError(
            "Необходимо добавить хотя бы один ингредиент."
        )

    ingredient_ids = [item["id"] for item in ingredients_data]
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise serializers.ValidationError("Ингредиенты не должны повторяться.")

    return ingredients_data


def validate_at_least_one_ingredient(ingredients_data):
    if not ingredients_data:
        raise serializers.ValidationError(
            "Необходимо добавить хотя бы один ингредиент."
        )
    return ingredients_data


def validate_cooking_time(value):
    if value < 1:
        raise serializers.ValidationError(
            "Время приготовления должно быть не менее 1 минуты."
        )
    return value


def validate_ingredient_amount(value):
    if value < 1:
        raise serializers.ValidationError(
            "Количество ингредиента должно быть не менее 1."
        )
    return value


def validate_tag_uniqueness(tags_data):
    if not tags_data:
        raise serializers.ValidationError("Необходимо добавить хотя бы один тег.")

    tag_ids = [tag.id if hasattr(tag, "id") else tag for tag in tags_data]
    if len(tag_ids) != len(set(tag_ids)):
        raise serializers.ValidationError("Теги не должны повторяться.")

    return tags_data
