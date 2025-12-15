from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    recipe_url_path = reverse("api:recipes-detail", kwargs={"pk": recipe.id})

    full_url = request.build_absolute_uri(recipe_url_path)

    response_data = {"short-link": full_url}

    return JsonResponse(response_data)
