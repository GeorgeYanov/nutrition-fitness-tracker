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

def calculate_macro_goals(current_weight, target_weight, height, age, gender, activity_multiplier):
    """
    Автоматически рассчитывает цели по макронутриентам на основе целей по весу.
    """
    # 1. Считаем TDEE на основе ТЕКУЩЕГО веса (это безопасная база)
    bmr = calculate_bmr(current_weight, height, age, gender)
    tdee = calculate_tdee(bmr, activity_multiplier)
    
    # 2. Определяем корректировку калорий
    weight_diff = target_weight - current_weight
    if weight_diff < -1:  # Цель: похудение
        target_calories = tdee - 400  # Умеренный дефицит
    elif weight_diff > 1:  # Цель: набор массы
        target_calories = tdee + 300  # Умеренный профицит
    else:  # Цель: поддержание
        target_calories = tdee
        
    # 3. Белок: 2.0г на 1 кг ЦЕЛЕВОГО веса (для поддержки/роста мышц)
    target_protein = target_weight * 2.0
    
    # 4. Жиры: 0.9г на 1 кг ЦЕЛЕВОГО веса (для гормонального здоровья)
    target_fat = target_weight * 0.9
    
    # 5. Углеводы: все оставшиеся калории
    protein_cals = target_protein * 4
    fat_cals = target_fat * 9
    remaining_cals = target_calories - (protein_cals + fat_cals)
    target_carbs = remaining_cals / 4
    
    # Защита: углеводы не должны падать ниже 50г (минимум для работы мозга)
    if target_carbs < 50:
        target_carbs = 50
        target_calories = protein_cals + fat_cals + (50 * 4)

    return {
        'calories': round(target_calories),
        'protein': round(target_protein),
        'fat': round(target_fat),
        'carbs': round(target_carbs)
    }

def calculate_complex_meal_totals(components_data, foods_dict):
    """
    Рассчитывает итоговые КБЖУ сложного блюда на основе его компонентов.
    
    Args:
        components_data: список словарей [{'food_id': 1, 'weight': 100, 'method': 'Варка'}, ...]
        foods_dict: словарь объектов Food из БД, где ключ - food_id
    
    Returns:
        dict с общими весами и макросами
    """
    totals = {
        'weight': 0.0,
        'calories': 0.0,
        'protein': 0.0,
        'fat': 0.0,
        'carbs': 0.0
    }
    
    for comp in components_data:
        food = foods_dict.get(comp['food_id'])
        if food:
            multiplier = comp['weight'] / 100.0
            totals['weight'] += comp['weight']
            totals['calories'] += food.calories_per_100g * multiplier
            totals['protein'] += food.protein_per_100g * multiplier
            totals['fat'] += food.fat_per_100g * multiplier
            totals['carbs'] += food.carbs_per_100g * multiplier
            
    return totals