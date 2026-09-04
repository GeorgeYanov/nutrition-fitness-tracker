"""
Модуль для расчетов калорий, макросов и прогресса
"""
from datetime import date

def calculate_age(birth_date):
    """Рассчитывает точный возраст в годах"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_bmr(weight, height, age, gender):
    """
    Рассчитывает базовый метаболизм (BMR) по формуле Миффлина-Сан Жеора
    weight: кг, height: см, age: лет, gender: 'male' или 'female'
    """
    gender = gender.lower()
    if gender in ['male', 'м', 'мужской', 'm']:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    return bmr

def calculate_tdee(bmr, activity_multiplier):
    """Рассчитывает суточную потребность в калориях (TDEE)"""
    return bmr * activity_multiplier

def calculate_food_calories(food, weight_eaten):
    """
    Рассчитывает калории и макросы для съеденного продукта
    
    Args:
        food: объект Food из базы данных
        weight_eaten: сколько грамм съедено
    
    Returns:
        dict с калориями и макросами
    """
    multiplier = weight_eaten / 100.0
    
    return {
        'calories': food.calories_per_100g * multiplier,
        'protein': food.protein_per_100g * multiplier,
        'fat': food.fat_per_100g * multiplier,
        'carbs': food.carbs_per_100g * multiplier
    }


def calculate_daily_totals(food_logs):
    """
    Рассчитывает общие калории и макросы за день
    
    Args:
        food_logs: список записей FoodLog
    
    Returns:
        dict с общими калориями и макросами
    """
    totals = {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbs': 0
    }
    
    for log in food_logs:
        macros = calculate_food_calories(log.food, log.weight_eaten)
        totals['calories'] += macros['calories']
        totals['protein'] += macros['protein']
        totals['fat'] += macros['fat']
        totals['carbs'] += macros['carbs']
    
    return totals


def calculate_workout_volume(workout_logs):
    """
    Рассчитывает объем тренировки (тоннаж)
    
    Args:
        workout_logs: список записей WorkoutLog
    
    Returns:
        float: общий объем в кг
    """
    total_volume = 0
    
    for log in workout_logs:
        if log.sets and log.reps and log.weight:
            total_volume += log.sets * log.reps * log.weight
    
    return total_volume


def calculate_bmr(weight, height, age, gender):
    """
    Рассчитывает базовый метаболизм (BMR) по формуле Миффлина-Сан Жеора
    
    Args:
        weight: вес в кг
        height: рост в см
        age: возраст в годах
        gender: 'male' или 'female'
    
    Returns:
        float: BMR в ккал/день
    """
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    return bmr


def calculate_tdee(bmr, activity_level=1.55):
    """
    Рассчитывает суточную потребность в калориях (TDEE)
    
    Args:
        bmr: базовый метаболизм
        activity_level: коэффициент активности (1.2-1.9)
    
    Returns:
        float: TDEE в ккал/день
    """
    return bmr * activity_level