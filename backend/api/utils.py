from django.db.models import Sum

from recipes.models import RecipeIngredient, ShoppingCart


def generate_shopping_list(user):
    shopping_cart_recipes = ShoppingCart.objects.filter(user=user).values_list(
        "recipe_id", flat=True
    )

    ingredients = (
        RecipeIngredient.objects.filter(recipe_id__in=shopping_cart_recipes)
        .values("ingredient__name", "ingredient__measurement_unit")
        .annotate(total_amount=Sum("amount"))
        .order_by("ingredient__name")
    )

    shopping_list_lines = ["Список покупок:\n"]

    for item in ingredients:
        name = item["ingredient__name"]
        measurement_unit = item["ingredient__measurement_unit"]
        amount = item["total_amount"]
        shopping_list_lines.append(f"{name} ({measurement_unit}) — {amount}\n")

    return "".join(shopping_list_lines)
