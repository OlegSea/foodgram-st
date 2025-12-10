from django.db.models import Count, Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.exceptions import (
    AlreadySubscribedError,
    NotSubscribedError,
    RecipeAlreadyInFavoritesError,
    RecipeAlreadyInShoppingCartError,
    RecipeNotInFavoritesError,
    RecipeNotInShoppingCartError,
    SelfSubscriptionError,
)
from api.filters import RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    RecipeUpdateSerializer,
    SetAvatarSerializer,
    SubscriptionCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
from users.models import Subscription, User


class CustomUserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = User.objects.all()

        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed_annotation=Exists(
                    Subscription.objects.filter(
                        user=self.request.user, author=OuterRef("pk")
                    )
                )
            )

        return queryset

    def get_permissions(self):
        if self.action in ["me", "avatar", "subscriptions", "subscribe"]:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            serializer = SetAvatarSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "DELETE":
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="subscriptions")
    def subscriptions(self, request):
        subscriptions = (
            User.objects.filter(subscribers__user=request.user)
            .prefetch_related("recipes")
            .annotate(
                is_subscribed_annotation=Exists(
                    Subscription.objects.filter(
                        user=request.user, author=OuterRef("pk")
                    )
                )
            )
        )
        page = self.paginate_queryset(subscriptions)

        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            subscriptions, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        user = request.user

        if request.method == "POST":
            if user == author:
                raise SelfSubscriptionError()

            if Subscription.objects.filter(user=user, author=author).exists():
                raise AlreadySubscribedError()

            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            subscription = Subscription.objects.filter(user=user, author=author)
            if not subscription.exists():
                raise NotSubscribedError()

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__startswith=name)

        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        queryset = Recipe.objects.select_related("author").prefetch_related(
            Prefetch(
                "recipe_ingredients",
                queryset=RecipeIngredient.objects.select_related("ingredient"),
            )
        )

        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited_annotation=Exists(
                    Favorite.objects.filter(
                        user=self.request.user, recipe=OuterRef("pk")
                    )
                ),
                is_in_shopping_cart_annotation=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef("pk")
                    )
                ),
            )

        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return RecipeCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return RecipeUpdateSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        from api.serializers import RecipeMinifiedSerializer

        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                raise RecipeAlreadyInFavoritesError()

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                raise RecipeNotInFavoritesError()

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        from api.serializers import RecipeMinifiedSerializer

        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                raise RecipeAlreadyInShoppingCartError()

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            shopping_cart_item = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not shopping_cart_item.exists():
                raise RecipeNotInShoppingCartError()

            shopping_cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        import random
        import string

        from api.serializers import ShortLinkSerializer
        from recipes.models import ShortLink

        recipe = get_object_or_404(Recipe, pk=pk)

        short_link = ShortLink.objects.filter(recipe=recipe).first()

        if not short_link:
            while True:
                short_code = "".join(
                    random.choices(string.ascii_letters + string.digits, k=6)
                )
                if not ShortLink.objects.filter(short_code=short_code).exists():
                    break

            short_link = ShortLink.objects.create(recipe=recipe, short_code=short_code)

        serializer = ShortLinkSerializer(short_link, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        from django.http import HttpResponse

        from api.utils import generate_shopping_list

        user = request.user
        shopping_list = generate_shopping_list(user)

        response = HttpResponse(shopping_list, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'

        return response
