"""
Модуль для расчетов калорий, макросов и прогресса
"""
from datetime import date
import random

def adjust_nutrients_for_cooking(food, method, time_minutes):
    """
    Корректирует нутриенты продукта с учетом способа и времени приготовления.
    Возвращает словарь с обновленными значениями на 100г.
    """
    # Базовые значения (защищаемся от None, заменяя на 0)
    adj = {
        'protein': getattr(food, 'protein_per_100g', 0) or 0,
        'fat': getattr(food, 'fat_per_100g', 0) or 0,
        'carbs': getattr(food, 'carbs_per_100g', 0) or 0,
        'vit_c': getattr(food, 'vitamin_c', 0) or 0,
        'vit_b': getattr(food, 'vitamin_b_complex', 0) or 0,
        'iron': getattr(food, 'iron', 0) or 0,
        'calcium': getattr(food, 'calcium', 0) or 0,
        'magnesium': getattr(food, 'magnesium', 0) or 0,
        'zinc': getattr(food, 'zinc', 0) or 0,
        'iodine': getattr(food, 'iodine', 0) or 0,
        'selenium': getattr(food, 'selenium', 0) or 0,
    }

    time = max(0, time_minutes or 0) # Защита от отрицательного времени

    if method == "Варка":
        # Вымывание водорастворимых витаминов и минералов в воду
        adj['vit_c'] *= (1 - 0.02 * time)   # -2% в минуту
        adj['vit_b'] *= (1 - 0.01 * time)   # -1% в минуту
        # Минералы вымываются медленнее
        for mineral in ['iron', 'calcium', 'magnesium', 'zinc', 'iodine', 'selenium']:
            adj[mineral] *= (1 - 0.005 * time) # -0.5% в минуту
        adj['protein'] *= (1 - 0.002 * time)  # Небольшая потеря белка

    elif method == "Жарка":
        # Впитывание масла (примерно +0.5г жира каждые 5 минут жарки)
        adj['fat'] += (0.5 * (time / 5))
        # Высокая температура разрушает витамины
        adj['vit_c'] *= (1 - 0.03 * time)   # -3% в минуту
        adj['vit_b'] *= (1 - 0.015 * time)  # -1.5% в минуту

    elif method == "Тушение":
        # Умеренный нагрев, частичное вымывание в соус
        adj['vit_c'] *= (1 - 0.015 * time)
        adj['vit_b'] *= (1 - 0.008 * time)
        adj['fat'] += (0.2 * (time / 5)) # Небольшое добавление жира (если тушим с маслом)

    elif method in ["Запекание", "Гриль"]:
        # Сухой жар, минералы сохраняются, витамины разрушаются умеренно
        adj['vit_c'] *= (1 - 0.01 * time)
        adj['vit_b'] *= (1 - 0.005 * time)
        adj['fat'] += (0.1 * (time / 5)) # Минимальное впитывание жира/потеря собственного

    elif method == "На пару":
        # Самый щадящий метод
        adj['vit_c'] *= (1 - 0.005 * time)
        adj['vit_b'] *= (1 - 0.003 * time)

    # "Без обработки" или неизвестный метод: коэффициенты = 1.0 (ничего не меняем)

    # ⚠️ ВАЖНО: Пересчитываем калорийность на основе новых макросов (формула 4-9-4)
    adj['calories'] = (adj['protein'] * 4) + (adj['fat'] * 9) + (adj['carbs'] * 4)

    # Остальные витамины (A, D, E, K) относительно стабильны, их не трогаем для простоты MVP,
    # но при желании можно добавить им небольшой коэффициент разрушения при "Жарке".

    return adj

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
    """Рассчитывает калории и макросы. Работает и с FoodItem, и с CustomFood"""
    multiplier = weight_eaten / 100.0
    return {
        'calories': (getattr(food, 'calories_per_100g', 0) or 0) * multiplier,
        'protein': (getattr(food, 'protein_per_100g', 0) or 0) * multiplier,
        'fat': (getattr(food, 'fat_per_100g', 0) or 0) * multiplier,
        'carbs': (getattr(food, 'carbs_per_100g', 0) or 0) * multiplier
    }


def calculate_daily_totals(food_logs, foods_dict):
    """Рассчитывает общие калории, макросы и микронутриенты за день по имени продукта"""
    totals = {
        'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0,
        'vit_a': 0, 'vit_c': 0, 'vit_d': 0, 'vit_e': 0, 'vit_k': 0, 'vit_b': 0,
        'iron': 0, 'calcium': 0, 'magnesium': 0, 'zinc': 0, 'iodine': 0, 'selenium': 0
    }
    
    for log in food_logs:
        food = foods_dict.get(log.food_name) # Ищем по имени!
        if not food:
            continue
            
        mult = log.weight_eaten / 100.0
        totals['calories'] += (getattr(food, 'calories_per_100g', 0) or 0) * mult
        totals['protein'] += (getattr(food, 'protein_per_100g', 0) or 0) * mult
        totals['fat'] += (getattr(food, 'fat_per_100g', 0) or 0) * mult
        totals['carbs'] += (getattr(food, 'carbs_per_100g', 0) or 0) * mult
        
        totals['vit_a'] += (getattr(food, 'vitamin_a', 0) or 0) * mult
        totals['vit_c'] += (getattr(food, 'vitamin_c', 0) or 0) * mult
        totals['vit_d'] += (getattr(food, 'vitamin_d', 0) or 0) * mult
        totals['vit_e'] += (getattr(food, 'vitamin_e', 0) or 0) * mult
        totals['vit_k'] += (getattr(food, 'vitamin_k', 0) or 0) * mult
        totals['vit_b'] += (getattr(food, 'vitamin_b_complex', 0) or 0) * mult
        totals['iron'] += (getattr(food, 'iron', 0) or 0) * mult
        totals['calcium'] += (getattr(food, 'calcium', 0) or 0) * mult
        totals['magnesium'] += (getattr(food, 'magnesium', 0) or 0) * mult
        totals['zinc'] += (getattr(food, 'zinc', 0) or 0) * mult
        totals['iodine'] += (getattr(food, 'iodine', 0) or 0) * mult
        totals['selenium'] += (getattr(food, 'selenium', 0) or 0) * mult
    
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
    Рассчитывает итоговые КБЖУ и микронутриенты сложного блюда, 
    учитывая корректировки от способа и времени приготовления каждого компонента.
    """
    totals = {
        'weight': 0.0,
        'calories': 0.0,
        'protein': 0.0,
        'fat': 0.0,
        'carbs': 0.0,
        'vit_c': 0.0, 'vit_b': 0.0,
        'iron': 0.0, 'calcium': 0.0, 'magnesium': 0.0, 
        'zinc': 0.0, 'iodine': 0.0, 'selenium': 0.0
    }
    
    for comp in components_data:
        # ✅ ИСПРАВЛЕНИЕ: Ищем 'food_name', а если его нет (как в генераторе), берем 'name'
        f_name = comp.get('food_name') or comp.get('name')
        food = foods_dict.get(f_name)
        
        if not food:
            continue
            
        # 1. Получаем скорректированные нутриенты на 100г (с защитой от отсутствия ключей)
        method = comp.get('method', 'Без обработки')
        time = comp.get('time', 0)
        adj = adjust_nutrients_for_cooking(food, method, time)
        
        # 2. Рассчитываем вклад этого компонента с учетом его веса
        multiplier = comp['weight'] / 100.0
        
        totals['weight'] += comp['weight']
        totals['calories'] += adj['calories'] * multiplier
        totals['protein'] += adj['protein'] * multiplier
        totals['fat'] += adj['fat'] * multiplier
        totals['carbs'] += adj['carbs'] * multiplier
        
        totals['vit_c'] += adj['vit_c'] * multiplier
        totals['vit_b'] += adj['vit_b'] * multiplier
        totals['iron'] += adj['iron'] * multiplier
        totals['calcium'] += adj['calcium'] * multiplier
        totals['magnesium'] += adj['magnesium'] * multiplier
        totals['zinc'] += adj['zinc'] * multiplier
        totals['iodine'] += adj['iodine'] * multiplier
        totals['selenium'] += adj['selenium'] * multiplier
        
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

def generate_weekly_plan(target_calories, target_protein, target_fat, target_carbs, 
                        user_allergen_names, user_favorite_foods, user_disliked_foods,
                        meals_per_day, min_favorite_meals, serving_distribution,
                        base_foods, custom_foods):
    """
    Генерирует план питания на неделю с учетом предпочтений пользователя
    """
    daily_cal = target_calories if target_calories else 2000
    
    # Объединяем и фильтруем продукты
    all_foods = base_foods + custom_foods
    
    # Карта аллергенов
    allergen_map = {
        'milk': ['dairy', 'молоко', 'творог', 'сыр', 'кефир', 'сливки'],
        'dairy': ['dairy', 'молоко', 'творог', 'сыр', 'кефир'],
        'gluten': ['bakery', 'grains', 'пшеница', 'хлеб', 'макароны', 'овсянка'],
        'wheat': ['bakery', 'grains', 'пшеница', 'хлеб'],
        'nuts': ['nuts', 'орех', 'миндаль', 'кешью'],
        'peanuts': ['nuts', 'арахис'],
        'eggs': ['eggs', 'яйц', 'омлет'],
        'soy': ['legumes', 'соя', 'тофу'],
        'fish': ['fish', 'рыба', 'лосось', 'тунец', 'форель'],
        'shellfish': ['fish', 'креветк', 'краб', 'мидии']
    }
    
    safe_foods = []
    for f in all_foods:
        is_safe = True
        f_cats = []
        if hasattr(f, 'categories') and f.categories:
            f_cats = [c.strip().lower() for c in f.categories.split(',')]
        elif hasattr(f, 'category') and f.category:
            f_cats = [f.category.lower()]
        
        f_name = f.name.lower()
        
        # Проверка аллергий
        for allergen in user_allergen_names:
            allergen = allergen.lower()
            if allergen in allergen_map:
                for keyword in allergen_map[allergen]:
                    if keyword in f_cats or keyword in f_name:
                        is_safe = False
                        break
            if allergen in f_cats or allergen in f_name:
                is_safe = False
        
        # Исключаем нелюбимые блюда
        if f.name in user_disliked_foods:
            is_safe = False
        
        if is_safe:
            safe_foods.append(f)

    if not safe_foods:
        return {'error': 'Не найдено безопасных продуктов. Проверьте аллергии и предпочтения.'}

    # Распределяем калории на приемы пищи
    cal_per_meal = daily_cal / meals_per_day
    
    weekly_plan = {}
    
    # Для каждого дня недели
    for day in range(7):
        day_plan = {}
        favorite_count = 0
        
        # Для каждого приема пищи
        for meal_num in range(1, meals_per_day + 1):
            meal_key = f"meal_{meal_num}"
            allowed_serving_types = serving_distribution.get(str(meal_num), [])
            
            # Фильтруем продукты по типу подачи
            suitable_foods = []
            for f in safe_foods:
                f_serving = getattr(f, 'serving_type', None)
                if f_serving:
                    f_serving_list = [s.strip().lower() for s in f_serving.split(',')]
                    if not allowed_serving_types or any(s in allowed_serving_types for s in f_serving_list):
                        suitable_foods.append(f)
                else:
                    suitable_foods.append(f)
            
            if not suitable_foods:
                suitable_foods = safe_foods
            
            # Пытаемся добавить любимое блюдо (если еще не достигли минимума)
            favorite_foods_in_suitable = [f for f in suitable_foods if f.name in user_favorite_foods]
            
            if favorite_foods_in_suitable and favorite_count < min_favorite_meals and random.random() > 0.3:
                # Выбираем любимое блюдо
                chosen = random.choice(favorite_foods_in_suitable)
                favorite_count += 1
            else:
                # Ищем готовые блюда или конструируем
                ready_meals = [f for f in suitable_foods if not getattr(f, 'is_basic', True)]
                
                if ready_meals and random.random() > 0.3:
                    chosen = random.choice(ready_meals)
                else:
                    # Конструируем из базовых
                    proteins = [f for f in suitable_foods if getattr(f, 'is_basic', True) and getattr(f, 'category', '') in ['meat', 'fish', 'eggs', 'dairy']]
                    carbs = [f for f in suitable_foods if getattr(f, 'is_basic', True) and getattr(f, 'category', '') in ['grains', 'vegetables', 'bakery']]
                    
                    if not proteins: proteins = [f for f in suitable_foods if getattr(f, 'is_basic', True)]
                    if not carbs: carbs = proteins
                    
                    p = random.choice(proteins) if proteins else None
                    c = random.choice(carbs) if carbs else None
                    
                    components = []
                    w_p, w_c = 150, 200
                    base_cals = 0
                    if p: base_cals += p.calories_per_100g * w_p / 100
                    if c: base_cals += c.calories_per_100g * w_c / 100
                    
                    if base_cals > 0:
                        scale = cal_per_meal / base_cals
                        w_p = int(w_p * scale)
                        w_c = int(w_c * scale)
                    
                    if p: components.append({'name': p.name, 'weight': w_p, 'method': 'Запекание', 'time': 20})
                    if c: components.append({'name': c.name, 'weight': w_c, 'method': 'Варка', 'time': 15})
                    
                    day_plan[meal_key] = components
                    continue
            
            # Если выбрали одно блюдо (готовое или любимое)
            weight = (cal_per_meal / chosen.calories_per_100g * 100) if chosen.calories_per_100g > 0 else 250
            day_plan[meal_key] = [{
                'name': chosen.name,
                'weight': round(weight),
                'method': 'Без обработки',
                'time': 0,
                'is_ready_meal': True
            }]
        
        weekly_plan[day] = day_plan

    return weekly_plan
    
    safe_foods = []
    for f in all_foods:
        is_safe = True
        f_cats = []
        if hasattr(f, 'categories') and f.categories:
            f_cats = [c.strip().lower() for c in f.categories.split(',')]
        elif hasattr(f, 'category') and f.category:
            f_cats = [f.category.lower()]
            
        f_name = f.name.lower()
        
        for allergen in user_allergen_names:
            allergen = allergen.lower()
            # Проверяем категории
            if allergen in allergen_map:
                for keyword in allergen_map[allergen]:
                    if keyword in f_cats or keyword in f_name:
                        is_safe = False
                        break
            # Прямое совпадение
            if allergen in f_cats or allergen in f_name:
                is_safe = False
        if is_safe:
            safe_foods.append(f)

    if not safe_foods:
        return {'error': 'Не найдено безопасных продуктов. Проверьте аллергии.'}

    # 2. Распределяем калории (30% / 40% / 30%)
    meal_targets = {
        'breakfast': daily_cal * 0.30,
        'lunch': daily_cal * 0.40,
        'dinner': daily_cal * 0.30
    }
    
    plan = {}
    
    for meal_type, cal_target in meal_targets.items():
        # Ищем готовые блюда
        ready_meals = [f for f in safe_foods if not getattr(f, 'is_basic', True)]
        
        if ready_meals and random.random() > 0.3: # 70% шанс выбрать готовое блюдо, если есть
            chosen = random.choice(ready_meals)
            weight = (cal_target / chosen.calories_per_100g * 100) if chosen.calories_per_100g > 0 else 250
            plan[meal_type] = [{
                'name': chosen.name, 
                'weight': round(weight), 
                'method': 'Без обработки', 
                'time': 0,
                'is_ready_meal': True
            }]
        else:
            # Конструируем из базовых ингредиентов
            proteins = [f for f in safe_foods if getattr(f, 'is_basic', True) and getattr(f, 'category', '') in ['meat', 'fish', 'eggs', 'dairy']]
            carbs = [f for f in safe_foods if getattr(f, 'is_basic', True) and getattr(f, 'category', '') in ['grains', 'vegetables', 'bakery']]
            
            # Фоллбэк, если категорий нет
            if not proteins: proteins = [f for f in safe_foods if getattr(f, 'is_basic', True)]
            if not carbs: carbs = proteins 
            
            p = random.choice(proteins) if proteins else None
            c = random.choice(carbs) if carbs else None
            
            components = []
            # Базовые порции для расчета масштаба
            w_p, w_c = 150, 200 
            base_cals = 0
            if p: base_cals += p.calories_per_100g * w_p / 100
            if c: base_cals += c.calories_per_100g * w_c / 100
            
            if base_cals > 0:
                scale = cal_target / base_cals
                w_p = int(w_p * scale)
                w_c = int(w_c * scale)
            
            if p: components.append({'name': p.name, 'weight': w_p, 'method': 'Запекание', 'time': 20})
            if c: components.append({'name': c.name, 'weight': w_c, 'method': 'Варка', 'time': 15})
            
            plan[meal_type] = components

    return plan