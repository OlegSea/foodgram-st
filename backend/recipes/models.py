from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        "Email адрес",
        max_length=254,
        unique=True,
        help_text="Обязательное поле. Введите действующий email адрес.",
    )

    username = models.CharField(
        "Псевдоним",
        max_length=150,
        unique=True,
        help_text="Обязательное поле. Не более 150 символов. "
        "Только буквы, цифры и символы @/./+/-/_.",
        validators=[
            RegexValidator(
                r"^[\w.@+-]+$", "Введите корректный псевдоним пользователя."
            )
        ],
    )

    first_name = models.CharField(
        "Имя", max_length=150, help_text="Имя пользователя"
    )

    last_name = models.CharField(
        "Фамилия", max_length=150, help_text="Фамилия пользователя"
    )

    avatar = models.ImageField(
        "Аватар",
        upload_to="users/avatars/",
        null=True,
        blank=True,
        help_text="Загрузите аватар пользователя",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ("username", "first_name", "last_name")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("email",)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="author_subscriptions",
        verbose_name="Автор",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} подписан на {self.author.username}"


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
        db_index=True,
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
    )
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Изображение",
    )
    text = models.TextField(
        verbose_name="Описание",
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления (мин)",
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
        db_index=True,
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Продукт",
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = "Продукт в рецепте"
        verbose_name_plural = "Продукты в рецептах"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} в {self.recipe.name}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
        db_index=True,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Рецепт",
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления",
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_favorite"
            )
        ]

    def __str__(self):
        return f"{self.user.username} добавил {self.recipe.name} в избранное"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
        db_index=True,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="in_shopping_carts",
        verbose_name="Рецепт",
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="unique_shopping_cart"
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} добавил {self.recipe.name} в список покупок"
        )
