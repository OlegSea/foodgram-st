from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(
        self, email, username, first_name, last_name, password=None, **extra_fields
    ):
        if not email:
            raise ValueError("Email адрес обязателен")
        if not username:
            raise ValueError("Имя пользователя обязательно")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, username, first_name, last_name, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(
            email, username, first_name, last_name, password, **extra_fields
        )


class User(AbstractUser):
    email = models.EmailField(
        "Email адрес",
        max_length=254,
        unique=True,
        help_text="Обязательное поле. Введите действующий email адрес.",
    )

    username = models.CharField(
        "Имя пользователя",
        max_length=150,
        unique=True,
        help_text="Обязательное поле. Не более 150 символов. "
        "Только буквы, цифры и символы @/./+/-/_.",
    )

    first_name = models.CharField("Имя", max_length=150, help_text="Имя пользователя")

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
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["id"]

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
        db_index=True,
    )
    author = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Автор",
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата подписки",
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["-created_at"]
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
