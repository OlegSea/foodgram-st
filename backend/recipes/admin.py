from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import mark_safe

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    User,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit", "recipes_count")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)
    ordering = ("name",)

    @admin.display(description="Рецептов")
    def recipes_count(self, obj):
        return obj.recipe_ingredients.count()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "cooking_time",
        "author",
        "get_favorites_count",
        "ingredients_display",
        "image_display",
    )
    search_fields = (
        "name",
        "author__username",
        "author__email",
        "recipe_ingredients__ingredient__name",
    )
    list_filter = ("pub_date", "author")
    readonly_fields = ("pub_date",)
    ordering = ("-pub_date",)
    inlines = [RecipeIngredientInline]

    @admin.display(description="В избранном")
    def get_favorites_count(self, obj):
        return obj.favorited_by.count()

    @admin.display(description="Продукты")
    @mark_safe
    def ingredients_display(self, obj):
        ingredients = obj.recipe_ingredients.select_related("ingredient").all()
        if not ingredients:
            return '<span style="color: #999;">Нет ингредиентов</span>'

        ingredients_list = []
        for recipe_ingredient in ingredients:
            ingredient_name = recipe_ingredient.ingredient.name
            amount = recipe_ingredient.amount
            unit = recipe_ingredient.ingredient.measurement_unit
            ingredients_list.append(f"{ingredient_name} ({amount} {unit})")

        return "<br>".join(ingredients_list)

    @admin.display(description="Картинка")
    @mark_safe
    def image_display(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="60" height="60" style="border-radius: 8px; object-fit: cover;" alt="Изображение рецепта">'
        return '<span style="color: #999;">Нет изображения</span>'


@admin.register(Favorite, ShoppingCart)
class BaseUserRecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "added_at")
    search_fields = ("user__username", "recipe__name")
    list_filter = ("added_at",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "username",
        "full_name",
        "email",
        "avatar_display",
        "recipes_count",
        "subscriptions_count",
        "subscribers_count",
    )
    list_display_links = ("id", "username")
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("id",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Личная информация",
            {"fields": ("first_name", "last_name", "email", "avatar")},
        ),
        (
            "Разрешения",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related()
            .prefetch_related(
                "recipes", "subscriptions", "author_subscriptions"
            )
        )

    @admin.display(description="ФИО")
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    @admin.display(description="Аватар")
    @mark_safe
    def avatar_display(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" alt="Аватар {obj.username}">'
        return '<span style="color: #999;">Нет аватара</span>'

    @admin.display(description="Рецептов")
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description="Подписок")
    def subscriptions_count(self, obj):
        return obj.subscriptions.count()

    @admin.display(description="Подписчиков")
    def subscribers_count(self, obj):
        return obj.author_subscriptions.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
