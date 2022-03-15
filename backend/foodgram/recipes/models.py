from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель тегов для рецептов."""
    name = models.CharField(verbose_name='Тег', max_length=200)
    color = ColorField(
        verbose_name='Цветовой HEX-код',
        default='#00FF00',
        format='hex',
        unique=True
    )
    slug = models.SlugField(verbose_name='Слаг тега', unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиентов для рецепта."""
    name = models.CharField(verbose_name='Ингридиент', max_length=256)
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=24
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецептов."""
    name = models.CharField(
        verbose_name='Название',
        max_length=256
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/images/',
    )
    text = models.TextField(verbose_name='Описание', max_length=5000)
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-id',)
        constraints = (
            models.CheckConstraint(
                check=models.Q(cooking_time__gte=1),
                name='%(app_label)s_%(class)s_cooking_time__gte=1'
            ),
        )

    def __str__(self):
        return f'{self.name}. Автор: {self.author.username}'


class IngredientRecipe(models.Model):
    """Модель для связывания количества ингридиентов в рецепте."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredient',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    amount = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Ингридиент рецепта'
        verbose_name_plural = 'Ингридиенты рецептов'


class Favorite(models.Model):
    """Модель для избранных рецептов пользователя."""
    recipe = models.ForeignKey(
        Recipe,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        related_name='favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                name='%(app_label)s_%(class)s_unique_relationships',
                fields=('recipe', 'user'),
            ),
        )

    def __str__(self):
        return f'{self.user}/{self.recipe}'


class ShoppingCart(models.Model):
    """Модель для списка покупок пользователя."""
    recipe = models.ForeignKey(
        Recipe,
        related_name='cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        related_name='cart',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} / {self.recipe}'
