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

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    full_name.short_description = "ФИО"

    @mark_safe
    def avatar_display(self, obj):
        if obj.avatar:
            return f'<img src="{obj.avatar.url}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" alt="Аватар {obj.username}">'
        return '<span style="color: #999;">Нет аватара</span>'

    avatar_display.short_description = "Аватар"

    def recipes_count(self, obj):
        return obj.recipes.count()

    recipes_count.short_description = "Рецептов"

    def subscriptions_count(self, obj):
        return obj.subscriptions.count()

    subscriptions_count.short_description = "Подписок"

    def subscribers_count(self, obj):
        return obj.author_subscriptions.count()

    subscribers_count.short_description = "Подписчиков"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user__username", "author__username")
