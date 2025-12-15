from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
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
