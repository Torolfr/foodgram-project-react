from django.contrib.admin import ModelAdmin, TabularInline, register, site
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)

site.site_header = 'Администрирование Foodgram'


class IngredientRecipeInLine(TabularInline):
    model = IngredientRecipe
    extra = 1


@register(IngredientRecipe)
class LinksAdmin(ModelAdmin):
    pass


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('id', 'name', 'author', '_get_thumbnail')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author__username')
    inlines = (IngredientRecipeInLine,)
    readonly_fields = ['_get_thumbnail']

    def _get_thumbnail(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" hieght="30" />')

    _get_thumbnail.short_description = 'Изображение'


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')


site.register(Favorite)
site.register(ShoppingCart)
