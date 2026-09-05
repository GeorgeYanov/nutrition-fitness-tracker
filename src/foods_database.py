"""
Модуль для работы с базой данных справочника продуктов
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Путь к файлу базы данных продуктов
FOODS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'foods.db')
FOODS_DATABASE_URL = f'sqlite:///{FOODS_DB_PATH}'

# Создаем движок
foods_engine = create_engine(FOODS_DATABASE_URL, echo=False)

# Базовый класс
FoodsBase = declarative_base()

class FoodItem(FoodsBase):
    """Продукт в справочнике"""
    __tablename__ = 'food_items'
    
    food_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)
    
    # Микронутриенты
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
    
    category = Column(String(50))  # Например: 'grains', 'meat', 'dairy'


def init_foods_db():
    """Создает таблицу продуктов и заполняет базовыми данными"""
    FoodsBase.metadata.create_all(foods_engine)
    
    Session = sessionmaker(bind=foods_engine)
    session = Session()
    
    # Проверяем, есть ли уже продукты
    if session.query(FoodItem).count() == 0:
        # Базовые продукты для старта
        basic_foods = [
            # Крупы и злаки
            FoodItem(name='Гречка вареная', calories_per_100g=110, protein_per_100g=4.5, fat_per_100g=1.7, carbs_per_100g=21.0, category='grains'),
            FoodItem(name='Рис белый вареный', calories_per_100g=130, protein_per_100g=2.7, fat_per_100g=0.3, carbs_per_100g=28.0, category='grains'),
            FoodItem(name='Овсянка на воде', calories_per_100g=88, protein_per_100g=3.0, fat_per_100g=1.7, carbs_per_100g=15.0, category='grains'),
            FoodItem(name='Макароны вареные', calories_per_100g=131, protein_per_100g=5.0, fat_per_100g=1.1, carbs_per_100g=25.0, category='grains'),
            
            # Мясо и птица
            FoodItem(name='Куриная грудка вареная', calories_per_100g=165, protein_per_100g=31.0, fat_per_100g=3.6, carbs_per_100g=0.0, category='meat'),
            FoodItem(name='Говядина вареная', calories_per_100g=250, protein_per_100g=26.0, fat_per_100g=15.0, carbs_per_100g=0.0, category='meat'),
            FoodItem(name='Свинина нежирная', calories_per_100g=160, protein_per_100g=21.0, fat_per_100g=8.0, carbs_per_100g=0.0, category='meat'),
            
            # Рыба
            FoodItem(name='Лосось запеченный', calories_per_100g=208, protein_per_100g=20.0, fat_per_100g=13.0, carbs_per_100g=0.0, category='fish', vitamin_d=11.0, iron=0.3),
            FoodItem(name='Тунец консервированный', calories_per_100g=116, protein_per_100g=26.0, fat_per_100g=1.0, carbs_per_100g=0.0, category='fish'),
            
            # Молочные продукты
            FoodItem(name='Творог 5%', calories_per_100g=121, protein_per_100g=17.0, fat_per_100g=5.0, carbs_per_100g=1.8, category='dairy', calcium=120, vitamin_b_complex=0.5),
            FoodItem(name='Молоко 2.5%', calories_per_100g=52, protein_per_100g=2.8, fat_per_100g=2.5, carbs_per_100g=4.7, category='dairy', calcium=120),
            FoodItem(name='Кефир 1%', calories_per_100g=40, protein_per_100g=3.0, fat_per_100g=1.0, carbs_per_100g=4.0, category='dairy'),
            FoodItem(name='Сыр твердый', calories_per_100g=350, protein_per_100g=25.0, fat_per_100g=27.0, carbs_per_100g=2.0, category='dairy', calcium=700),
            
            # Яйца
            FoodItem(name='Яйцо куриное вареное', calories_per_100g=155, protein_per_100g=13.0, fat_per_100g=11.0, carbs_per_100g=1.1, category='eggs', vitamin_a=160, iron=1.2),
            
            # Овощи
            FoodItem(name='Огурцы свежие', calories_per_100g=15, protein_per_100g=0.8, fat_per_100g=0.1, carbs_per_100g=3.6, category='vegetables', vitamin_c=10),
            FoodItem(name='Помидоры свежие', calories_per_100g=18, protein_per_100g=0.9, fat_per_100g=0.2, carbs_per_100g=3.9, category='vegetables', vitamin_c=14),
            FoodItem(name='Морковь вареная', calories_per_100g=35, protein_per_100g=0.8, fat_per_100g=0.2, carbs_per_100g=8.0, category='vegetables', vitamin_a=850),
            FoodItem(name='Картофель вареный', calories_per_100g=82, protein_per_100g=2.0, fat_per_100g=0.4, carbs_per_100g=17.0, category='vegetables'),
            
            # Фрукты
            FoodItem(name='Банан', calories_per_100g=89, protein_per_100g=1.1, fat_per_100g=0.3, carbs_per_100g=22.8, category='fruits', vitamin_c=9, magnesium=27),
            FoodItem(name='Яблоко', calories_per_100g=52, protein_per_100g=0.3, fat_per_100g=0.2, carbs_per_100g=14.0, category='fruits', vitamin_c=5),
            FoodItem(name='Апельсин', calories_per_100g=47, protein_per_100g=0.9, fat_per_100g=0.1, carbs_per_100g=12.0, category='fruits', vitamin_c=53),
            
            # Масла и жиры
            FoodItem(name='Масло подсолнечное', calories_per_100g=884, protein_per_100g=0.0, fat_per_100g=100.0, carbs_per_100g=0.0, category='oils', vitamin_e=41),
            FoodItem(name='Масло оливковое', calories_per_100g=884, protein_per_100g=0.0, fat_per_100g=100.0, carbs_per_100g=0.0, category='oils', vitamin_e=14),
            FoodItem(name='Масло сливочное', calories_per_100g=717, protein_per_100g=0.9, fat_per_100g=81.0, carbs_per_100g=0.1, category='oils', vitamin_a=684),
            
            # Хлеб и выпечка
            FoodItem(name='Хлеб белый', calories_per_100g=265, protein_per_100g=9.0, fat_per_100g=3.2, carbs_per_100g=49.0, category='bakery'),
            FoodItem(name='Хлеб черный (ржаной)', calories_per_100g=214, protein_per_100g=8.5, fat_per_100g=3.3, carbs_per_100g=40.0, category='bakery'),
        ]
        
        session.add_all(basic_foods)
        session.commit()
        print(f"✅ База продуктов создана и заполнена {len(basic_foods)} продуктами")
    else:
        print("✅ База продуктов уже существует")
    
    session.close()


def get_foods_session():
    """Возвращает сессию для работы с базой продуктов"""
    Session = sessionmaker(bind=foods_engine)
    return Session()


def get_all_foods():
    """Возвращает все продукты из справочника"""
    session = get_foods_session()
    foods = session.query(FoodItem).order_by(FoodItem.name).all()
    session.close()
    return foods


def get_food_by_name(name):
    """Находит продукт по названию"""
    session = get_foods_session()
    food = session.query(FoodItem).filter(FoodItem.name.ilike(name)).first()
    session.close()
    return food


if __name__ == '__main__':
    init_foods_db()
    
    # Проверяем
    session = get_foods_session()
    print(f"✅ Всего продуктов в базе: {session.query(FoodItem).count()}")
    session.close()