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
    """Рассчитывает общие калории, макросы и микронутриенты за день"""
    totals = {
        'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0,
        'vit_a': 0, 'vit_c': 0, 'vit_d': 0, 'vit_e': 0, 'vit_k': 0, 'vit_b': 0,
        'iron': 0, 'calcium': 0, 'magnesium': 0, 'zinc': 0, 'iodine': 0, 'selenium': 0
    }
    
    for log in food_logs:
        food = log.food
        mult = log.weight_eaten / 100.0
        
        totals['calories'] += (food.calories_per_100g or 0) * mult
        totals['protein'] += (food.protein_per_100g or 0) * mult
        totals['fat'] += (food.fat_per_100g or 0) * mult
        totals['carbs'] += (food.carbs_per_100g or 0) * mult
        
        # Суммируем микронутриенты (если они есть в продукте)
        totals['vit_a'] += (food.vitamin_a or 0) * mult
        totals['vit_c'] += (food.vitamin_c or 0) * mult
        totals['vit_d'] += (food.vitamin_d or 0) * mult
        totals['vit_e'] += (food.vitamin_e or 0) * mult
        totals['vit_k'] += (food.vitamin_k or 0) * mult
        totals['vit_b'] += (food.vitamin_b_complex or 0) * mult
        totals['iron'] += (food.iron or 0) * mult
        totals['calcium'] += (food.calcium or 0) * mult
        totals['magnesium'] += (food.magnesium or 0) * mult
        totals['zinc'] += (food.zinc or 0) * mult
        totals['iodine'] += (food.iodine or 0) * mult
        totals['selenium'] += (food.selenium or 0) * mult
    
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

def get_standard_micro_goals(gender, weight):
    """
    Возвращает рекомендуемые суточные нормы (RDA) микронутриентов.
    Базовые значения адаптированы под средний вес, с небольшой корректировкой.
    """
    is_female = gender.lower() in ['female', 'ж', 'женский', 'f']
    
    # Базовые нормы (упрощенные средние значения для взрослых)
    goals = {
        'vit_a': 900,       # мкг
        'vit_c': 90 if not is_female else 75,  # мг
        'vit_d': 15,        # мкг (600 ME)
        'vit_e': 15,        # мг
        'vit_k': 120 if not is_female else 90, # мкг
        'vit_b': 1.3 if not is_female else 1.1, # мг (усредненно по B-комплексу)
        'iron': 8 if not is_female else 18,    # мг
        'calcium': 1000,    # мг
        'magnesium': 400 if not is_female else 310, # мг
        'zinc': 11 if not is_female else 8,    # мг
        'iodine': 150,      # мкг
        'selenium': 55      # мкг
    }
    
    # Легкая корректировка на вес (например, +1% на каждый кг свыше 70)
    multiplier = 1.0 + max(0, (weight - 70) * 0.01)
    
    return {k: round(v * multiplier) for k, v in goals.items()}