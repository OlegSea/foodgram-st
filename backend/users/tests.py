from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123",
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)

        self.assertEqual(user.email, self.user_data["email"])
        self.assertEqual(user.username, self.user_data["username"])
        self.assertEqual(user.first_name, self.user_data["first_name"])
        self.assertEqual(user.last_name, self.user_data["last_name"])
        self.assertTrue(user.check_password(self.user_data["password"]))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(**self.user_data)

        self.assertEqual(superuser.email, self.user_data["email"])
        self.assertEqual(superuser.username, self.user_data["username"])
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_create_user_without_email(self):
        user_data = self.user_data.copy()
        user_data["email"] = ""

        with self.assertRaises(ValueError) as context:
            User.objects.create_user(**user_data)

        self.assertEqual(str(context.exception), "Email адрес обязателен")

    def test_create_user_without_username(self):
        user_data = self.user_data.copy()
        user_data["username"] = ""

        with self.assertRaises(ValueError) as context:
            User.objects.create_user(**user_data)

        self.assertEqual(str(context.exception), "Имя пользователя обязательно")

    def test_email_uniqueness(self):
        User.objects.create_user(**self.user_data)

        duplicate_data = self.user_data.copy()
        duplicate_data["username"] = "anotheruser"

        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_data)

    def test_username_uniqueness(self):
        User.objects.create_user(**self.user_data)

        duplicate_data = self.user_data.copy()
        duplicate_data["email"] = "another@example.com"

        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_data)

    def test_user_string_representation(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data["username"])

    def test_email_normalization(self):
        user_data = self.user_data.copy()
        user_data["email"] = "TEST@EXAMPLE.COM"

        user = User.objects.create_user(**user_data)
        self.assertEqual(user.email, "TEST@example.com")

    def test_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields(self):
        expected_fields = ["username", "first_name", "last_name"]
        self.assertEqual(User.REQUIRED_FIELDS, expected_fields)

    def test_create_superuser_with_invalid_flags(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(**self.user_data, is_staff=False)
        self.assertEqual(
            str(context.exception), "Суперпользователь должен иметь is_staff=True."
        )

        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(**self.user_data, is_superuser=False)
        self.assertEqual(
            str(context.exception), "Суперпользователь должен иметь is_superuser=True."
        )

    def test_user_avatar_field(self):
        user = User.objects.create_user(**self.user_data)

        self.assertFalse(user.avatar)

        user.avatar = None
        user.save()
        self.assertFalse(user.avatar)
