import django_filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method="filter_is_favorited")
    is_in_shopping_cart = django_filters.NumberFilter(
        method="filter_is_in_shopping_cart"
    )
    author = django_filters.NumberFilter(field_name="author__id")

    class Meta:
        model = Recipe
        fields = ("is_favorited", "is_in_shopping_cart", "author")

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset

        if value == 1:
            return queryset.filter(favorites__user=user)
        elif value == 0:
            return queryset.exclude(favorites__user=user)

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset

        if value == 1:
            return queryset.filter(shoppingcarts__user=user)
        elif value == 0:
            return queryset.exclude(shoppingcarts__user=user)

        return queryset


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name", lookup_expr="startswith"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)
