from django.db import transaction
from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,
)
from rest_framework import serializers

from api.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    User,
)
from recipes.validators import (
    validate_ingredients_uniqueness,
)


class UserSerializer(DjoserUserSerializer):
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
        read_only_fields = fields

    def get_is_subscribed(self, user):
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and (
                getattr(user, "is_subscribed_annotation", None)
                or user.author_subscriptions.filter(user=request.user).exists()
            )
        )


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)

    def validate(self, data):
        if "avatar" not in data or data["avatar"] is None:
            raise serializers.ValidationError(
                {"avatar": "Поле avatar обязательно для заполнения."}
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id", read_only=True)
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")
        read_only_fields = fields


class RecipeIngredientCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

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

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо добавить хотя бы один продукт."
            )
        return validate_ingredients_uniqueness(value)

    def validate(self, data):
        if self.instance and "ingredients" not in data:
            raise serializers.ValidationError(
                {
                    "ingredients": "Поле ingredients обязательно при обновлении рецепта."
                }
            )
        return data

    def _save_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data["id"].id,
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients")

        instance = super().update(instance, validated_data)

        instance.recipe_ingredients.all().delete()
        self._save_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeDetailSerializer(instance, context=self.context).data


class RecipeDetailSerializer(serializers.ModelSerializer):
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

    def _get_user_relation(self, obj, annotation_attr, model_class):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if hasattr(obj, annotation_attr):
                return getattr(obj, annotation_attr)
            return model_class.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_favorited(self, obj):
        return self._get_user_relation(
            obj, "is_favorited_annotation", Favorite
        )

    def get_is_in_shopping_cart(self, obj):
        return self._get_user_relation(
            obj, "is_in_shopping_cart_annotation", ShoppingCart
        )


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
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")
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

        return RecipeMinifiedSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
