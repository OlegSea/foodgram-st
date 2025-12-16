from datetime import datetime

from django.db.models import Sum

from recipes.models import RecipeIngredient, ShoppingCart


def generate_shopping_list(user):
    ingredients = (
        RecipeIngredient.objects.filter(recipe__shoppingcarts__user=user)
        .values("ingredient__name", "ingredient__measurement_unit")
        .annotate(total_amount=Sum("amount"))
        .order_by("ingredient__name")
    )

    recipes = (
        ShoppingCart.objects.filter(user=user)
        .select_related("recipe__author")
        .values("recipe__name", "recipe__author__username")
        .distinct()
        .order_by("recipe__name")
    )

    current_date = datetime.now().strftime("%d.%m.%Y")

    return "\n".join(
        [
            f"Список покупок от {current_date}",
            "",
            "Продукты:",
            *[
                f"{i + 1}. {item['ingredient__name'].capitalize()} ({item['ingredient__measurement_unit']}) — {item['total_amount']}"
                for i, item in enumerate(ingredients)
            ],
            "",
            "Рецепты:",
            *[
                f"• {recipe['recipe__name']} (автор: {recipe['recipe__author__username']})"
                for recipe in recipes
            ],
        ]
    )
