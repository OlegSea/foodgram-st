from django.db import transaction
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from rest_framework import serializers

from api.fields import Base64ImageField
from api.validators import (
    validate_cooking_time,
    validate_ingredient_amount,
    validate_ingredients_uniqueness,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLink,
)
from users.models import Subscription, User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )
        read_only_fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(obj, "is_subscribed_annotation"):
                return obj.is_subscribed_annotation
            return obj.subscribers.filter(user=request.user).exists()
        return False


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")
        read_only_fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(validators=[validate_ingredient_amount])

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Ингредиент с id={value} не существует.")
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(validators=[validate_cooking_time])

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("id", "author")

    def validate_ingredients(self, value):
        return validate_ingredients_uniqueness(value)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        author = self.context["request"].user

        recipe = Recipe.objects.create(author=author, **validated_data)

        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe


class RecipeUpdateSerializer(RecipeCreateSerializer):
    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()

            recipe_ingredients = []
            for ingredient_data in ingredients_data:
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient_id=ingredient_data["id"],
                        amount=ingredient_data["amount"],
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return instance


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source="recipe_ingredients"
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(obj, "is_favorited_annotation"):
                return obj.is_favorited_annotation
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(obj, "is_in_shopping_cart_annotation"):
                return obj.is_in_shopping_cart_annotation
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
            "recipes",
            "recipes_count",
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = None

        if request:
            recipes_limit = request.query_params.get("recipes_limit")

        recipes = obj.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[: int(recipes_limit)]
            except (ValueError, TypeError):
                pass

        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("user", "author")

    def validate(self, data):
        user = data.get("user")
        author = data.get("author")

        if user == author:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")

        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого автора.")

        return data


class ShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = ShortLink
        fields = ("short-link",)

    def get_short_link(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/s/{obj.short_code}")
        return f"/s/{obj.short_code}"
