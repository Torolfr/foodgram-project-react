import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает таблицу ингридиентов из csv-файла'

    def handle(self, *args, **options):
        with open('recipes/data/ingredients.csv', encoding='utf-8') as file:
            data_reader = csv.reader(file)
            for row in data_reader:
                name, unit = row
                Ingredient.objects.get_or_create(
                    name=name, measurement_unit=unit
                )
