from django.db.models import Exists, OuterRef, Prefetch
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeMinifiedSerializer,
    RecipeWriteSerializer,
    SetAvatarSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from api.utils import generate_shopping_list
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    User,
)


class UserViewSet(DjoserUserViewSet):
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
        if self.action in ("me", "avatar", "subscriptions", "subscribe"):
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=False, methods=("put", "delete"), url_path="me/avatar")
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            serializer = SetAvatarSerializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=("get",), url_path="subscriptions")
    def subscriptions(self, request):
        subscriptions = (
            User.objects.filter(author_subscriptions__user=request.user)
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

        serializer = UserWithRecipesSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=("post", "delete"), url_path="subscribe")
    def subscribe(self, request, id=None):
        user = request.user

        if request.method == "DELETE":
            # валит тесты
            get_object_or_404(Subscription, user=user, author_id=id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError("Нельзя подписаться на самого себя.")

        _, created = Subscription.objects.get_or_create(
            user=user, author=author
        )
        if not created:
            raise ValidationError(f"Вы уже подписаны на автора {author}.")
        serializer = UserWithRecipesSerializer(
            author, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    @staticmethod
    def _handle_user_recipe_relation(request, pk, model_class):
        location = "избранном" if model_class == Favorite else "списке покупок"
        user = request.user

        if request.method == "DELETE":
            get_object_or_404(model_class, user=user, recipe_id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = model_class.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            raise ValidationError(
                f"{model_class._meta.verbose_name}: "
                f"Рецепт '{recipe.name}' уже в {location}."
            )
        serializer = RecipeMinifiedSerializer(
            recipe, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        if self.action in ("create", "update", "partial_update"):
            return RecipeWriteSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._handle_user_recipe_relation(request, pk, Favorite)

    @action(
        detail=True,
        methods=("post", "delete"),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_user_recipe_relation(request, pk, ShoppingCart)

    @action(detail=True, methods=("get",), url_path="get-link")
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise Http404(f"Рецепт с id {pk} не найден")

        short_url_path = reverse("short_link_redirect", args=[pk])

        return Response(
            {"short-link": request.build_absolute_uri(short_url_path)},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False, methods=("get",), permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        return FileResponse(
            generate_shopping_list(request.user),
            as_attachment=True,
            filename="shopping_list.txt",
            content_type="text/plain",
        )
