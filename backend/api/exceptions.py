from rest_framework import status
from rest_framework.exceptions import APIException


class AlreadyExistsError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Объект уже существует."
    default_code = "already_exists"


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Объект не найден."
    default_code = "not_found"


class PermissionDeniedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Операция запрещена."
    default_code = "permission_denied"


class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Ошибка валидации данных."
    default_code = "validation_error"


class RecipeAlreadyInFavoritesError(AlreadyExistsError):
    default_detail = "Рецепт уже в избранном."
    default_code = "recipe_already_in_favorites"


class RecipeNotInFavoritesError(ValidationError):
    default_detail = "Рецепт не в избранном."
    default_code = "recipe_not_in_favorites"


class RecipeAlreadyInShoppingCartError(AlreadyExistsError):
    default_detail = "Рецепт уже в списке покупок."
    default_code = "recipe_already_in_shopping_cart"


class RecipeNotInShoppingCartError(ValidationError):
    default_detail = "Рецепт не в списке покупок."
    default_code = "recipe_not_in_shopping_cart"


class AlreadySubscribedError(AlreadyExistsError):
    default_detail = "Вы уже подписаны на этого автора."
    default_code = "already_subscribed"


class NotSubscribedError(ValidationError):
    default_detail = "Вы не подписаны на этого автора."
    default_code = "not_subscribed"


class SelfSubscriptionError(ValidationError):
    default_detail = "Нельзя подписаться на самого себя."
    default_code = "self_subscription"
