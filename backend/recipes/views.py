from django.shortcuts import get_object_or_404, redirect

from recipes.models import ShortLink


def short_link_redirect(request, short_code):
    short_link = get_object_or_404(ShortLink, short_code=short_code)
    recipe_id = short_link.recipe.id

    return redirect(f"/recipes/{recipe_id}")
