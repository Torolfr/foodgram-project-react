from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from users.models import Follow

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())])
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())])

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email',
                  'password')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'username': {'required': True},
            'email': {'required': True},
            'password': {'required': True},

        }


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (not user.is_anonymous
                and Follow.objects.filter(user=user, author=obj.id).exists())


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientRecipe.objects.all(),
                fields=['ingredient', 'recipe']
            )
        ]


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(max_length=None, use_url=True)
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        source='recipe_ingredient',
        many=True,
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        read_only_fields = ('author', 'tags',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(favorites__user=user, id=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Recipe.objects.filter(cart__user=user, id=obj.id).exists()

    def validate(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Должен быть хотя бы один тег'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться')
        data['tags'] = tags

        ingredients = self.initial_data.get('ingredients')
        if not ingredients or len(ingredients) < 1:
            raise serializers.ValidationError(
                'Минимум должен быть один ингредиент для рецепта'
            )
        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=ingredient_item['id']
            )
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться'
                )
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) <= 0:
                raise serializers.ValidationError(
                    'Значение количества ингредиента дожно быть больше 0'
                )
        data['ingredients'] = ingredients

        cooking_time = self.initial_data.get('cooking_time')
        if int(cooking_time) < 0:
            raise serializers.ValidationError(
                'Время приготовления должно больше нуля'
            )
        data['cooking_time'] = cooking_time
        return data

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(image=image, **validated_data)
        self.create_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, recipe, validated_data):
        if 'ingredients' in self.initial_data:
            ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            self.create_ingredients(ingredients, recipe)
        if 'tags' in self.initial_data:
            tags_data = validated_data.pop('tags')
            recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        extra_kwargs = {'user': {'write_only': True},
                        'recipe': {'write_only': True}}

    def validate(self, data):
        if Favorite.objects.filter(user=data['user'],
                                   recipe=data['recipe']).exists():
            raise serializers.ValidationError('Рецепт уже добавлен в избраное.')
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = Base64ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time', 'user', 'recipe')
        extra_kwargs = {'user': {'write_only': True},
                        'recipe': {'write_only': True}}

    def validate(self, data):
        if ShoppingCart.objects.filter(user=data['user'],
                                       recipe=data['recipe']).exists():
            raise serializers.ValidationError('Рецепт уже есть в списке'
                                              ' покупок.')
        return data


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user, author=obj.author
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[:int(limit)]
        return ShortRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()
