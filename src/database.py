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
    meals_per_day = Column(Integer)
    workouts_per_week = Column(Integer)
    
    # НОВЫЕ ПОЛЯ ДЛЯ МАКРОНУТРИЕНТОВ
    target_calories = Column(Float)
    target_protein = Column(Float)
    target_fat = Column(Float)
    target_carbs = Column(Float)
    
    user = relationship('User', back_populates='goals')


class Allergen(Base):
    """Справочник аллергенов"""
    __tablename__ = 'allergens'
    
    allergen_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    
    users = relationship('UserAllergy', back_populates='allergen')


class UserAllergy(Base):
    """Связь пользователь-аллергия"""
    __tablename__ = 'user_allergies'
    
    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    allergen_id = Column(Integer, ForeignKey('allergens.allergen_id'), primary_key=True)
    
    user = relationship('User', back_populates='allergies')
    allergen = relationship('Allergen', back_populates='users')


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


class Food(Base):
    """Справочник продуктов"""
    __tablename__ = 'foods'
    
    food_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)
    
    # Микронутриенты (все на 100г)
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
    sodium = Column(Float)
    cholesterol = Column(Float)
    caffeine = Column(Float)
    alcohol = Column(Float)
    
    logs = relationship('FoodLog', back_populates='food')


class FoodLog(Base):
    """Дневник питания"""
    __tablename__ = 'food_log'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    food_id = Column(Integer, ForeignKey('foods.food_id'), nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String(20), nullable=False)  # breakfast, lunch, dinner, snack
    weight_eaten = Column(Float, nullable=False)
    
    user = relationship('User', back_populates='food_logs')
    food = relationship('Food', back_populates='logs')


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
    print(f"✅ Количество продуктов: {session.query(Food).count()}")
    session.close()