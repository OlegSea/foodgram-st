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
        user.shoppingcarts.select_related("recipe__author")
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
                f"{i}. {item['ingredient__name'].capitalize()} ({item['ingredient__measurement_unit']}) — {item['total_amount']}"
                for i, item in enumerate(ingredients, start=1)
            ],
            "",
            "Рецепты:",
            *[
                f"• {recipe['recipe__name']} (автор: {recipe['recipe__author__username']})"
                for recipe in recipes
            ],
        ]
    )
