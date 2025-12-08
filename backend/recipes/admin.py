from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)
    ordering = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "cooking_time",
        "pub_date",
        "get_favorites_count",
    )
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("pub_date",)
    readonly_fields = ("pub_date",)
    ordering = ("-pub_date",)
    inlines = [RecipeIngredientInline]

    def get_favorites_count(self, obj):
        return obj.favorited_by.count()

    get_favorites_count.short_description = "В избранном"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "added_at")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("added_at",)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "added_at")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("added_at",)
