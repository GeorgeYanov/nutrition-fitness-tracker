"""
Модуль для работы с базой данных.
Создает все необходимые таблицы и предоставляет функции для работы с ними.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Date, Boolean, 
    ForeignKey, Text, DateTime, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

# Путь к файлу базы данных
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tracker.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'

# Создаем движок (connection to database)
engine = create_engine(DATABASE_URL, echo=False)

# Базовый класс для всех моделей
Base = declarative_base()

# ============================================================================
# МОДЕЛИ ТАБЛИЦ
# ============================================================================

class User(Base):
    """Пользователи приложения"""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True) # Уникальный email
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Эти поля можно заполнить позже в настройках профиля
    gender = Column(String(10), nullable=True)
    birth_date = Column(Date, nullable=True)
    height = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    measurements = relationship('UserMeasurement', back_populates='user', cascade='all, delete-orphan')
    medical_results = relationship('MedicalResult', back_populates='user', cascade='all, delete-orphan')
    goals = relationship('UserGoal', back_populates='user', uselist=False, cascade='all, delete-orphan')
    allergies = relationship('UserAllergy', back_populates='user', cascade='all, delete-orphan')
    injuries = relationship('UserInjury', back_populates='user', cascade='all, delete-orphan')
    priority_muscles = relationship('UserPriorityMuscle', back_populates='user', cascade='all, delete-orphan')
    habits = relationship('UserHabit', back_populates='user', cascade='all, delete-orphan')
    food_logs = relationship('FoodLog', back_populates='user', cascade='all, delete-orphan')
    workouts = relationship('Workout', back_populates='user', cascade='all, delete-orphan')
    complex_meals = relationship('ComplexMeal', back_populates='user', cascade='all, delete-orphan')


class UserMeasurement(Base):
    """Замеры тела (вес, процент жира и т.д.)"""
    __tablename__ = 'user_measurements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    weight = Column(Float)
    fat_percent = Column(Float)
    muscle_mass = Column(Float)
    wake_time = Column(String(5))  # формат HH:MM
    sleep_time = Column(String(5))  # формат HH:MM
    
    user = relationship('User', back_populates='measurements')


class MedicalResult(Base):
    """Результаты медицинских анализов (универсальная таблица)"""
    __tablename__ = 'medical_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    test_date = Column(Date, nullable=False)
    test_category = Column(String(50), nullable=False)  # blood_general, blood_biochem, urine, coprogram
    test_name = Column(String(100), nullable=False)  # hemoglobin, rbc, alt и т.д.
    value = Column(Float)
    unit = Column(String(20))
    
    user = relationship('User', back_populates='medical_results')


class UserGoal(Base):
    """Цели пользователя"""
    __tablename__ = 'user_goals'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    target_weight = Column(Float)
    target_fat_percent = Column(Float)
    target_muscle_mass = Column(Float)
    meals_per_day = Column(Integer)
    workouts_per_week = Column(Integer)
    
    target_calories = Column(Float)
    target_protein = Column(Float)
    target_fat = Column(Float)
    target_carbs = Column(Float)
    
    # НОВЫЕ ПОЛЯ: Цели по микронутриентам (в мг или мкг)
    target_vit_a = Column(Float)
    target_vit_c = Column(Float)
    target_vit_d = Column(Float)
    target_vit_e = Column(Float)
    target_vit_k = Column(Float)
    target_vit_b = Column(Float)
    target_iron = Column(Float)
    target_calcium = Column(Float)
    target_magnesium = Column(Float)
    target_zinc = Column(Float)
    target_iodine = Column(Float)
    target_selenium = Column(Float)
    
    user = relationship('User', back_populates='goals')


class Allergen(Base):
    """Справочник аллергенов"""
    __tablename__ = 'allergens'
    
    allergen_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)  # например, 'milk', 'gluten', 'nuts'


class UserAllergy(Base):
    """Аллергии пользователя"""
    __tablename__ = 'user_allergies'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    allergen_id = Column(Integer, ForeignKey('allergens.allergen_id'), nullable=False)
    
    user = relationship('User', back_populates='allergies')
    allergen = relationship('Allergen')


class Injury(Base):
    """Справочник травм"""
    __tablename__ = 'injuries'
    
    injury_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    users = relationship('UserInjury', back_populates='injury')


class UserInjury(Base):
    """Связь пользователь-травма"""
    __tablename__ = 'user_injuries'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    injury_id = Column(Integer, ForeignKey('injuries.injury_id'), primary_key=True)
    
    user = relationship('User', back_populates='injuries')
    injury = relationship('Injury', back_populates='users')


class MuscleGroup(Base):
    """Справочник мышечных групп"""
    __tablename__ = 'muscle_groups'
    
    muscle_id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    
    users = relationship('UserPriorityMuscle', back_populates='muscle')


class UserPriorityMuscle(Base):
    """Приоритетные мышцы пользователя"""
    __tablename__ = 'user_priority_muscles'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    muscle_id = Column(Integer, ForeignKey('muscle_groups.muscle_id'), primary_key=True)
    
    user = relationship('User', back_populates='priority_muscles')
    muscle = relationship('MuscleGroup', back_populates='users')


class UserHabit(Base):
    """Вредные привычки пользователя"""
    __tablename__ = 'user_habits'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    habit_type = Column(String(20), nullable=False)  # alcohol, smoking
    is_active = Column(Boolean, default=False)
    frequency = Column(String(50))
    details = Column(Text)
    
    user = relationship('User', back_populates='habits')


class FoodLog(Base):
    """Дневник питания"""
    __tablename__ = 'food_log'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    food_name = Column(String(200), nullable=False)  # ИЗМЕНЕНО: храним название, а не ID
    date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    weight_eaten = Column(Float, nullable=False)
    
    user = relationship('User', back_populates='food_logs')


class Exercise(Base):
    """Справочник упражнений"""
    __tablename__ = 'exercises'
    
    exercise_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    exercise_type = Column(String(50), nullable=False)  # strength, cardio, flexibility
    target_muscles = Column(Text)  # JSON или список через запятую
    
    logs = relationship('WorkoutLog', back_populates='exercise')


class Workout(Base):
    """Дневник тренировок"""
    __tablename__ = 'workouts'
    
    workout_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    duration_minutes = Column(Integer)
    
    user = relationship('User', back_populates='workouts')
    logs = relationship('WorkoutLog', back_populates='workout', cascade='all, delete-orphan')


class WorkoutLog(Base):
    """Детализация тренировки (подходы)"""
    __tablename__ = 'workout_log'
    
    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey('workouts.workout_id'), nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercises.exercise_id'), nullable=False)
    sets = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    intensity = Column(String(20))  # RPE или описание
    
    workout = relationship('Workout', back_populates='logs')
    exercise = relationship('Exercise', back_populates='logs')

class ComplexMeal(Base):
    """Сложное блюдо (рецепт), состоящее из нескольких компонентов"""
    __tablename__ = 'complex_meals'
    
    meal_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)
    dish_name = Column(String(200), nullable=False)
    
    total_weight = Column(Float)
    total_calories = Column(Float)
    total_protein = Column(Float)
    total_fat = Column(Float)
    total_carbs = Column(Float)
    
    components = relationship('ComplexMealComponent', back_populates='meal', cascade='all, delete-orphan')
    user = relationship('User', back_populates='complex_meals')

class ComplexMealComponent(Base):
    """Отдельный ингредиент в составе сложного блюда"""
    __tablename__ = 'complex_meal_components'
    
    component_id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey('complex_meals.meal_id'), nullable=False)
    food_name = Column(String(200), nullable=False)  # ИЗМЕНЕНО: храним название
    weight = Column(Float, nullable=False)
    cooking_method = Column(String(255))
    cooking_time = Column(Float)
    
    meal = relationship('ComplexMeal', back_populates='components')

class CustomFood(Base):
    """Пользовательские продукты (добавленные вручную)"""
    __tablename__ = 'custom_foods'
    categories = Column(String(500))
    serving_type = Column(String(100))  # НОВОЕ ПОЛЕ
    custom_food_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    name = Column(String(200), nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)

    is_basic = Column(Boolean, default=True)
    is_complex_meal = Column(Boolean, default=False)
    complex_meal_id = Column(Integer, nullable=True)
    
    vitamin_a = Column(Float)
    vitamin_c = Column(Float)
    vitamin_d = Column(Float)
    vitamin_e = Column(Float)
    vitamin_k = Column(Float)
    vitamin_b_complex = Column(Float)
    iron = Column(Float)
    calcium = Column(Float)
    magnesium = Column(Float)
    zinc = Column(Float)
    iodine = Column(Float)
    selenium = Column(Float)

class GeneratedPlan(Base):
    """Сохраненный сгенерированный рацион на конкретный день"""
    __tablename__ = 'generated_plans'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False, unique=True) # Уникален для одного пользователя в один день
    
    # Храним компоненты каждого приема пищи как JSON-строки
    breakfast_json = Column(String)
    lunch_json = Column(String)
    dinner_json = Column(String)
    
    user = relationship('User', backref='generated_plans')

class UserFoodPreference(Base):
    """Предпочтения пользователя по продуктам (любимые/нелюбимые)"""
    __tablename__ = 'user_food_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    food_name = Column(String(200), nullable=False)
    preference_type = Column(String(20), nullable=False)  # 'favorite' или 'disliked'
    
    user = relationship('User', backref='food_preferences')


class MealPlanSettings(Base):
    """Настройки генерации рациона пользователя"""
    __tablename__ = 'meal_plan_settings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, unique=True)
    meals_per_day = Column(Integer, default=3)  # Количество приемов пищи в день
    min_favorite_meals = Column(Integer, default=2)  # Минимум любимых блюд в рационе
    
    # Храним распределение типов подачи по приемам пищи как JSON
    # Например: {"breakfast": ["breakfast", "main"], "lunch": ["soup", "second"], "dinner": ["second", "salad"]}
    serving_distribution = Column(String)
    
    user = relationship('User', backref='meal_plan_settings')

class DailySteps(Base):
    """Ежедневная цель и факт по шагам"""
    __tablename__ = 'daily_steps'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    goal_steps = Column(Integer, default=10000)
    actual_steps = Column(Integer, default=0)
    
    user = relationship('User', backref='daily_steps')


class WorkoutSession(Base):
    """Запись о тренировке"""
    __tablename__ = 'workout_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    date = Column(Date, nullable=False)
    workout_type = Column(String(20), nullable=False)  # 'running', 'cardio', 'strength'
    
    # Общие поля
    duration_minutes = Column(Float)
    calories_burned = Column(Float)
    
    # Для бега
    distance_km = Column(Float)
    avg_speed_kmh = Column(Float)
    
    # Для кардио и силовых
    exercise_name = Column(String(200))
    sets_count = Column(Integer)
    
    # Специфичные поля
    duration_per_set_minutes = Column(Float)  # Для кардио
    weight_kg = Column(Float)  # Для силовых
    reps_count = Column(Integer)  # Для силовых
    
    user = relationship('User', backref='workout_sessions')

# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ ДАННЫХ
# ============================================================================

def init_db():
    """Создает все таблицы в базе данных"""
    # Создаем папку data, если её нет
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Создаем все таблицы
    Base.metadata.create_all(engine)
    print(f"✅ База данных создана: {DB_PATH}")


def get_session():
    """Возвращает сессию для работы с БД"""
    Session = sessionmaker(bind=engine)
    return Session()


# ============================================================================
# ТОЧКА ВХОДА (для тестирования)
# ============================================================================

if __name__ == '__main__':
    # Запускаем создание базы данных
    init_db()
    
    # Проверяем, что всё создалось
    session = get_session()
    print(f"✅ Сессия создана успешно")
    print(f"✅ Количество пользователей: {session.query(User).count()}")
    session.close()