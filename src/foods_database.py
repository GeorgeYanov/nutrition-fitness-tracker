"""
Модуль для работы с базой данных справочника продуктов
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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
    is_basic = Column(Boolean, default=True)
    
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

class FoodCategory(FoodsBase):
    """Справочник категорий продуктов"""
    __tablename__ = 'food_categories'
    
    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)  # например, 'dairy', 'citrus', 'mushrooms'
    display_name = Column(String(100), nullable=False)  # Русское название для отображения
    icon = Column(String(10))  # Эмодзи для красоты


class FoodCategoryLink(FoodsBase):
    """Связь продуктов с категориями (многие-ко-многим)"""
    __tablename__ = 'food_category_links'
    
    link_id = Column(Integer, primary_key=True)
    food_id = Column(Integer, ForeignKey('food_items.food_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('food_categories.category_id'), nullable=False)
    
    food = relationship('FoodItem', backref='category_links')
    category = relationship('FoodCategory', backref='food_links')

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
            FoodItem(name='Гречка вареная', calories_per_100g=110, protein_per_100g=4.5, fat_per_100g=1.7, carbs_per_100g=21.0, category='grains', is_basic=True),
            FoodItem(name='Рис белый вареный', calories_per_100g=130, protein_per_100g=2.7, fat_per_100g=0.3, carbs_per_100g=28.0, category='grains', is_basic=True),
            FoodItem(name='Овсянка на воде', calories_per_100g=88, protein_per_100g=3.0, fat_per_100g=1.7, carbs_per_100g=15.0, category='grains', is_basic=True),
            FoodItem(name='Макароны вареные', calories_per_100g=131, protein_per_100g=5.0, fat_per_100g=1.1, carbs_per_100g=25.0, category='grains', is_basic=True),
            
            # Мясо и птица
            FoodItem(name='Куриная грудка вареная', calories_per_100g=165, protein_per_100g=31.0, fat_per_100g=3.6, carbs_per_100g=0.0, category='meat', is_basic=True),
            FoodItem(name='Говядина вареная', calories_per_100g=250, protein_per_100g=26.0, fat_per_100g=15.0, carbs_per_100g=0.0, category='meat', is_basic=True),
            FoodItem(name='Свинина нежирная', calories_per_100g=160, protein_per_100g=21.0, fat_per_100g=8.0, carbs_per_100g=0.0, category='meat', is_basic=True),
            
            # Рыба
            FoodItem(name='Лосось запеченный', calories_per_100g=208, protein_per_100g=20.0, fat_per_100g=13.0, carbs_per_100g=0.0, category='fish', vitamin_d=11.0, iron=0.3, is_basic=True),
            FoodItem(name='Тунец консервированный', calories_per_100g=116, protein_per_100g=26.0, fat_per_100g=1.0, carbs_per_100g=0.0, category='fish', is_basic=True),
            
            # Молочные продукты
            FoodItem(name='Творог 5%', calories_per_100g=121, protein_per_100g=17.0, fat_per_100g=5.0, carbs_per_100g=1.8, category='dairy', calcium=120, vitamin_b_complex=0.5, is_basic=True),
            FoodItem(name='Молоко 2.5%', calories_per_100g=52, protein_per_100g=2.8, fat_per_100g=2.5, carbs_per_100g=4.7, category='dairy', calcium=120, is_basic=True),
            FoodItem(name='Кефир 1%', calories_per_100g=40, protein_per_100g=3.0, fat_per_100g=1.0, carbs_per_100g=4.0, category='dairy', is_basic=True),
            FoodItem(name='Сыр твердый', calories_per_100g=350, protein_per_100g=25.0, fat_per_100g=27.0, carbs_per_100g=2.0, category='dairy', calcium=700, is_basic=True),
            
            # Яйца
            FoodItem(name='Яйцо куриное вареное', calories_per_100g=155, protein_per_100g=13.0, fat_per_100g=11.0, carbs_per_100g=1.1, category='eggs', vitamin_a=160, iron=1.2, is_basic=True),
            
            # Овощи
            FoodItem(name='Огурцы свежие', calories_per_100g=15, protein_per_100g=0.8, fat_per_100g=0.1, carbs_per_100g=3.6, category='vegetables', vitamin_c=10, is_basic=True),
            FoodItem(name='Помидоры свежие', calories_per_100g=18, protein_per_100g=0.9, fat_per_100g=0.2, carbs_per_100g=3.9, category='vegetables', vitamin_c=14, is_basic=True),
            FoodItem(name='Морковь вареная', calories_per_100g=35, protein_per_100g=0.8, fat_per_100g=0.2, carbs_per_100g=8.0, category='vegetables', vitamin_a=850, is_basic=True),
            FoodItem(name='Картофель вареный', calories_per_100g=82, protein_per_100g=2.0, fat_per_100g=0.4, carbs_per_100g=17.0, category='vegetables', is_basic=True),
            
            # Фрукты
            FoodItem(name='Банан', calories_per_100g=89, protein_per_100g=1.1, fat_per_100g=0.3, carbs_per_100g=22.8, category='fruits', vitamin_c=9, magnesium=27, is_basic=True),
            FoodItem(name='Яблоко', calories_per_100g=52, protein_per_100g=0.3, fat_per_100g=0.2, carbs_per_100g=14.0, category='fruits', vitamin_c=5, is_basic=True),
            FoodItem(name='Апельсин', calories_per_100g=47, protein_per_100g=0.9, fat_per_100g=0.1, carbs_per_100g=12.0, category='fruits', vitamin_c=53, is_basic=True),
            
            # Масла и жиры
            FoodItem(name='Масло подсолнечное', calories_per_100g=884, protein_per_100g=0.0, fat_per_100g=100.0, carbs_per_100g=0.0, category='oils', vitamin_e=41, is_basic=True),
            FoodItem(name='Масло оливковое', calories_per_100g=884, protein_per_100g=0.0, fat_per_100g=100.0, carbs_per_100g=0.0, category='oils', vitamin_e=14, is_basic=True),
            FoodItem(name='Масло сливочное', calories_per_100g=717, protein_per_100g=0.9, fat_per_100g=81.0, carbs_per_100g=0.1, category='oils', vitamin_a=684, is_basic=True),
            
            # Хлеб и выпечка
            FoodItem(name='Хлеб белый', calories_per_100g=265, protein_per_100g=9.0, fat_per_100g=3.2, carbs_per_100g=49.0, category='bakery', is_basic=True),
            FoodItem(name='Хлеб черный (ржаной)', calories_per_100g=214, protein_per_100g=8.5, fat_per_100g=3.3, carbs_per_100g=40.0, category='bakery', is_basic=True),

            # ДОБАВЛЯЕМ ГОТОВЫЕ БЛЮДА (is_basic=False)
            FoodItem(name='Борщ классический', calories_per_100g=45, protein_per_100g=1.5, fat_per_100g=2.0, carbs_per_100g=6.0, is_basic=False, category='vegetables'),
            FoodItem(name='Овсянка с ягодами и медом', calories_per_100g=95, protein_per_100g=2.5, fat_per_100g=1.5, carbs_per_100g=18.0, is_basic=False, category='prepared'),
        
        ]
        
        session.add_all(basic_foods)
        session.commit()
        print(f"✅ База продуктов создана и заполнена {len(basic_foods)} продуктами")
    else:
        print("✅ База продуктов уже существует")

    # Создаем базовые категории
    categories = [
        FoodCategory(name='dairy', display_name='Молочные продукты', icon='🥛'),
        FoodCategory(name='grains', display_name='Крупы и злаки', icon='🌾'),
        FoodCategory(name='meat', display_name='Мясо и птица', icon=''),
        FoodCategory(name='fish', display_name='Рыба и морепродукты', icon='🐟'),
        FoodCategory(name='eggs', display_name='Яйца', icon='🥚'),
        FoodCategory(name='vegetables', display_name='Овощи', icon='🥬'),
        FoodCategory(name='fruits', display_name='Фрукты и ягоды', icon='🍎'),
        FoodCategory(name='citrus', display_name='Цитрусовые', icon='🍊'),
        FoodCategory(name='nuts', display_name='Орехи и семена', icon=''),
        FoodCategory(name='legumes', display_name='Бобовые', icon='🫘'),
        FoodCategory(name='oils', display_name='Масла и жиры', icon='🫙'),
        FoodCategory(name='bakery', display_name='Хлеб и выпечка', icon='🍞'),
        FoodCategory(name='mushrooms', display_name='Грибы', icon='🍄'),
        FoodCategory(name='sweets', display_name='Сладости', icon='🍫'),
        FoodCategory(name='beverages', display_name='Напитки', icon='🥤'),
    ]
    session.add_all(categories)
    session.flush()  # Получаем category_id
    
    # Создаем словарь категорий для быстрого доступа
    cat_dict = {cat.name: cat for cat in categories}
    
    # Привязываем продукты к категориям (многие-ко-многим)
    food_category_map = {
        'Гречка вареная': ['grains'],
        'Рис белый вареный': ['grains'],
        'Овсянка на воде': ['grains'],
        'Макароны вареные': ['grains'],
        'Куриная грудка вареная': ['meat'],
        'Говядина вареная': ['meat'],
        'Свинина нежирная': ['meat'],
        'Лосось запеченный': ['fish'],
        'Тунец консервированный': ['fish'],
        'Творог 5%': ['dairy'],
        'Молоко 2.5%': ['dairy'],
        'Кефир 1%': ['dairy'],
        'Сыр твердый': ['dairy'],
        'Яйцо куриное вареное': ['eggs'],
        'Огурцы свежие': ['vegetables'],
        'Помидоры свежие': ['vegetables'],
        'Морковь вареная': ['vegetables'],
        'Картофель вареный': ['vegetables'],
        'Банан': ['fruits'],
        'Яблоко': ['fruits'],
        'Апельсин': ['fruits', 'citrus'],  # Две категории!
        'Масло подсолнечное': ['oils'],
        'Масло оливковое': ['oils'],
        'Масло сливочное': ['oils', 'dairy'],  # Две категории!
        'Хлеб белый': ['bakery'],
        'Хлеб черный (ржаной)': ['bakery'],
    }
    
    for food in session.query(FoodItem).all():
        if food.name in food_category_map:
            for cat_name in food_category_map[food.name]:
                if cat_name in cat_dict:
                    link = FoodCategoryLink(
                        food_id=food.food_id,
                        category_id=cat_dict[cat_name].category_id
                    )
                    session.add(link)
    
    session.commit()
    print(f"✅ Создано {len(categories)} категорий и привязаны к продуктам")
    
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

def get_all_categories():
    """Возвращает все категории"""
    session = get_foods_session()
    categories = session.query(FoodCategory).order_by(FoodCategory.display_name).all()
    session.close()
    return categories


def get_food_categories(food_id):
    """Возвращает категории конкретного продукта"""
    session = get_foods_session()
    links = session.query(FoodCategoryLink).filter(FoodCategoryLink.food_id == food_id).all()
    categories = [link.category for link in links]
    session.close()
    return categories


def get_foods_by_category(category_name):
    """Возвращает все продукты в категории"""
    session = get_foods_session()
    category = session.query(FoodCategory).filter(FoodCategory.name == category_name).first()
    if not category:
        session.close()
        return []
    
    links = session.query(FoodCategoryLink).filter(FoodCategoryLink.category_id == category.category_id).all()
    food_ids = [link.food_id for link in links]
    foods = session.query(FoodItem).filter(FoodItem.food_id.in_(food_ids)).all()
    session.close()
    return foods

if __name__ == '__main__':
    init_foods_db()
    
    # Проверяем
    session = get_foods_session()
    print(f"✅ Всего продуктов в базе: {session.query(FoodItem).count()}")
    session.close()