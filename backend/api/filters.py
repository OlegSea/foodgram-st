import django_filters
from django.db.models import Q

from recipes.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method="filter_is_favorited")
    is_in_shopping_cart = django_filters.NumberFilter(
        method="filter_is_in_shopping_cart"
    )
    author = django_filters.NumberFilter(field_name="author__id")

    class Meta:
        model = Recipe
        fields = ["is_favorited", "is_in_shopping_cart", "author"]

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset

        if value == 1:
            return queryset.filter(favorited_by__user=user)
        elif value == 0:
            return queryset.exclude(favorited_by__user=user)

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset

        if value == 1:
            return queryset.filter(in_shopping_cart__user=user)
        elif value == 0:
            return queryset.exclude(in_shopping_cart__user=user)

        return queryset
