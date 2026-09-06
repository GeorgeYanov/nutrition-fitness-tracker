"""
Главный файл приложения - интерфейс на Streamlit с авторизацией
"""
import streamlit as st
import json
from datetime import date, timedelta
import pandas as pd
from database import (
    get_session, User, Exercise, FoodLog, Workout, WorkoutLog, 
    UserMeasurement, UserGoal, MedicalResult, ComplexMeal, 
    ComplexMealComponent, Allergen, UserAllergy, CustomFood, GeneratedPlan # <-- ДОБАВИЛИ GeneratedPlan
)
from foods_database import get_all_foods, get_food_by_name, FoodItem, get_all_categories, get_food_categories, get_foods_by_category, FoodCategory
from calculations import (
       calculate_food_calories, calculate_daily_totals, calculate_workout_volume, 
       calculate_age, calculate_bmr, calculate_tdee, calculate_macro_goals, 
       calculate_complex_meal_totals, get_standard_micro_goals, generate_daily_plan
   )
from auth import register_user, authenticate_user

def get_display_categories(food_obj):
    """Универсальная функция для получения строки категорий продукта"""
    all_cats = get_all_categories()
    cat_map = {c.name: f"{c.icon} {c.display_name}" for c in all_cats}
    
    # 1. Если это базовый продукт из foods.db
    if hasattr(food_obj, 'food_id'):
        categories = get_food_categories(food_obj.food_id)
        if categories:
            return ", ".join([f"{c.icon} {c.display_name}" for c in categories])
    
    # 2. Если это пользовательский продукт (или сложное блюдо) из tracker.db
    elif hasattr(food_obj, 'categories') and food_obj.categories:
        # Строка выглядит как "dairy,meat,vegetables"
        cat_names = [name.strip() for name in food_obj.categories.split(',')]
        display_cats = [cat_map.get(name, name) for name in cat_names if name in cat_map]
        if display_cats:
            return ", ".join(display_cats)
            
    return "Без категории"

# Настройка страницы
st.set_page_config(page_title="Fitness Tracker", page_icon="🏋️", layout="wide")

# Инициализация состояния сессии (авторизация)
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
       st.session_state.user_name = ""

def logout():
    st.session_state.user_id = None
    st.session_state.user_name = ""
    st.rerun()

# ============================================================================
# ЭКРАН АВТОРИЗАЦИИ / РЕГИСТРАЦИИ (Если пользователь не вошел)
# ============================================================================
if st.session_state.user_id is None:
    st.title("🏋️ Добро пожаловать в Fitness Tracker")
    st.markdown("Отслеживайте питание, тренировки и прогресс в одном месте.")
    
    tab1, tab2 = st.tabs(["🔑 Вход", "📝 Регистрация"])
    
    with tab1:
        st.subheader("Вход в аккаунт")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Пароль", type="password")
            submit = st.form_submit_button("Войти", width='stretch')
            
            if submit:
                if not email or not password:
                    st.error("Пожалуйста, заполните все поля.")
                else:
                    success, user_id, name = authenticate_user(email, password)
                    if success:
                        st.session_state.user_id = user_id
                        st.session_state.user_name = name
                        st.success("Успешный вход!")
                        st.rerun()
                    else:
                        st.error("Неверный email или пароль.")
    
    with tab2:
        st.subheader("Создать новый аккаунт")
        with st.form("register_form"):
            reg_email = st.text_input("Email")
            reg_name = st.text_input("Имя и Фамилия")
            reg_password = st.text_input("Пароль", type="password")
            reg_submit = st.form_submit_button("Зарегистрироваться", width='stretch')
            
            if reg_submit:
                if not reg_email or not reg_name or not reg_password:
                    st.error("Пожалуйста, заполните все поля.")
                else:
                    success, message = register_user(reg_email, reg_name, reg_password)
                    if success:
                        st.success(message)
                        st.info("Теперь вы можете перейти на вкладку 'Вход'")
                    else:
                        st.error(message)

# ============================================================================
# ОСНОВНОЕ ПРИЛОЖЕНИЕ (Если пользователь вошел)
# ============================================================================
else:
    session = get_session()
    # Получаем данные ТЕКУЩЕГО пользователя
    current_user = session.query(User).filter(User.user_id == st.session_state.user_id).first()
    
    if not current_user:
        st.error("Ошибка: пользователь не найден в базе данных.")
        logout()
    else:
        # Боковая панель с информацией о пользователе и кнопкой выхода
        with st.sidebar:
            st.success(f"👤 {current_user.full_name}")
            st.caption(current_user.email)
            st.markdown("---")
            page = st.radio(
                "Навигация", 
                ["🏠 Главная", "👤 Профиль", "🍎 Питание", "🏋️ Тренировки", "📅 Мой календарь"]
            )
            st.markdown("---")
            if st.button("🚪 Выйти из аккаунта", width='stretch'):
                logout()

        # =========================================================================
        # ГЛАВНАЯ СТРАНИЦА
        # =========================================================================
        if page == "🏠 Главная":
            st.header(f"Добро пожаловать, {current_user.full_name.split()[0]}! 👋")
            
            latest_measurement = session.query(UserMeasurement).filter(UserMeasurement.user_id == current_user.user_id).order_by(UserMeasurement.date.desc()).first()
            
            st.markdown("### 🧮 Твои метаболические показатели")
            if latest_measurement and latest_measurement.weight and current_user.height and current_user.birth_date:
                age = calculate_age(current_user.birth_date)
                bmr = calculate_bmr(latest_measurement.weight, current_user.height, age, current_user.gender or 'male')
                
                activity_levels = {
                    "🛋️ Сидячий образ жизни": 1.2,
                    "🚶 Легкая активность (1-3 тр/нед)": 1.375,
                    "🏃 Умеренная активность (3-5 тр/нед)": 1.55,
                    "🏋️ Высокая активность (6-7 тр/нед)": 1.725,
                }
                selected_activity = st.selectbox("Уровень активности:", list(activity_levels.keys()), index=2)
                tdee = calculate_tdee(bmr, activity_levels[selected_activity])
                
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("🎂 Возраст", f"{age} лет")
                with col2: st.metric("⚖️ Вес", f"{latest_measurement.weight} кг")
                with col3: st.metric("🔥 BMR", f"{bmr:.0f} ккал")
                with col4: st.metric("🎯 TDEE", f"{tdee:.0f} ккал")
                
                st.info(f"💡 Для похудения ешь ~{int(tdee - 300)} ккал. Для набора массы ~{int(tdee + 300)} ккал.")
            else:
                st.warning("⚠️ Заполни рост, дату рождения и добавь замер веса, чтобы увидеть расчет BMR/TDEE.")
            
            st.markdown("---")
            st.subheader("📈 Статистика питания за сегодня")
            
            today = date.today()
            today_logs = session.query(FoodLog).filter(
                FoodLog.user_id == current_user.user_id, 
                FoodLog.date == today
            ).all()
            
            # Собираем словарь продуктов для расчетов
            all_foods_dict = {}
            for f in get_all_foods():
                all_foods_dict[f.name] = f
            for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                all_foods_dict[f.name] = f

            totals = calculate_daily_totals(today_logs, all_foods_dict)
            goals = session.query(UserGoal).filter(UserGoal.user_id == current_user.user_id).first()
            
            if today_logs:
                st.markdown("#### 📊 Прогресс за сегодня (Макронутриенты)")
                
                # Вспомогательная функция для красивого прогресс-бара
                def render_progress(current, target, label, unit, color="#1f77b4"):
                    if target and target > 0:
                        pct = min(current / target, 1.0) # Ограничиваем 100%
                        st.progress(pct, text=f"**{label}**: {current:.1f} / {target:.1f} {unit} ({(current/target)*100:.0f}%)")
                    else:
                        st.write(f"**{label}**: {current:.1f} {unit} *(Цель не задана в Профиле)*")
                
                t_cal = goals.target_calories if goals else None
                t_prot = goals.target_protein if goals else None
                t_fat = goals.target_fat if goals else None
                t_carb = goals.target_carbs if goals else None
                
                render_progress(totals['calories'], t_cal, "🔥 Калории", "ккал", "#ef553b")
                render_progress(totals['protein'], t_prot, "🥩 Белки", "г", "#1f77b4")
                render_progress(totals['fat'], t_fat, "🥑 Жиры", "г", "#ff7f0e")
                render_progress(totals['carbs'], t_carb, "🍞 Углеводы", "г", "#2ca02c")
                
            else:
                st.info("📭 Пока нет записей о питании за сегодня. Самое время добавить завтрак!")

            # ✅ ТЕПЕРЬ ЭТОТ БЛОК БЕЗОПАСЕН, ТАК КАК 'totals' ВСЕГДА СУЩЕСТВУЕТ
            st.markdown("---")
            with st.expander("🧪 Прогресс по микронутриентам за сегодня", expanded=False):
                
                micro_names = {
                    'vit_a': ('Витамин А', 'мкг', '#f39c12'),
                    'vit_c': ('Витамин С', 'мг', '#e67e22'),
                    'vit_d': ('Витамин D', 'мкг', '#f1c40f'),
                    'vit_e': ('Витамин E', 'мг', '#2ecc71'),
                    'vit_k': ('Витамин K', 'мкг', '#27ae60'),
                    'vit_b': ('Витамины B', 'мг', '#3498db'),
                    'iron': ('Железо', 'мг', '#e74c3c'),
                    'calcium': ('Кальций', 'мг', '#ecf0f1'),
                    'magnesium': ('Магний', 'мг', '#9b59b6'),
                    'zinc': ('Цинк', 'мг', '#95a5a6'),
                    'iodine': ('Йод', 'мкг', '#1abc9c'),
                    'selenium': ('Селен', 'мкг', '#34495e')
                }
                
                cols_micro = st.columns(3)
                for i, (key, (name, unit, color)) in enumerate(micro_names.items()):
                    with cols_micro[i % 3]:
                        current_val = totals.get(key, 0) # Теперь это работает всегда!
                        target_val = getattr(goals, f"target_{key}") if goals else None
                        
                        if target_val and target_val > 0:
                            pct = min(current_val / target_val, 1.0)
                            st.progress(pct, text=f"**{name}**: {current_val:.1f} / {target_val:.1f} {unit}")
                        else:
                            st.write(f"**{name}**: {current_val:.1f} {unit} *(Цель не задана)*")

        # =========================================================================
        # СТРАНИЦА ПРОФИЛЯ (Личные данные и замеры)
        # =========================================================================
        elif page == "👤 Профиль":
            st.header("👤 Профиль пользователя")
            
            # Создаем верхние вкладки
            tab_personal, tab_analyses, tab_progress = st.tabs([
                "📝 Личные данные и замеры", 
                "🩺 Медицинские анализы", 
                "📊 Прогресс и аналитика"
            ])
            
            with tab_personal:
                st.header("👤 Настройки профиля и замеры")
                
                # ---------------------------------------------------------------------
                # ФОРМА 1: ЛИЧНЫЕ ДАННЫЕ
                # ---------------------------------------------------------------------
                st.subheader("📝 Личные данные")
                st.caption("Эти данные используются для расчета BMR, TDEE и возраста.")
                
                with st.form("profile_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        # Определяем индекс для пола (0 - male, 1 - female)
                        gender_idx = 0 if (current_user.gender or "").lower() in ["male", "м", "мужской"] else 1
                        gender = st.selectbox(
                            "Пол", 
                            ["male", "female"], 
                            index=gender_idx,
                            format_func=lambda x: "👨 Мужской" if x == "male" else "👩 Женский"
                        )
                        
                        # Дата рождения (по умолчанию 01.01.2000, если не задана)
                        default_bd = current_user.birth_date or date(2000, 1, 1)
                        birth_date = st.date_input("Дата рождения", value=default_bd)
                    
                    with col2:
                        # Рост (по умолчанию 170, если не задан)
                        default_height = float(current_user.height or 170.0)
                        height = st.number_input("Рост (см)", min_value=100.0, max_value=250.0, value=default_height, step=1.0)
                    
                    submit_profile = st.form_submit_button("💾 Сохранить личные данные", width='stretch')
                    
                    if submit_profile:
                        current_user.gender = gender
                        current_user.birth_date = birth_date
                        current_user.height = height
                        session.commit()
                        st.success("✅ Личные данные успешно обновлены!")
                        st.rerun()
                
                st.markdown("---")
                
                # ---------------------------------------------------------------------
                # ФОРМА 2: ДОБАВЛЕНИЕ ЗАМЕРА ВЕСА
                # ---------------------------------------------------------------------
                st.subheader("⚖️ Добавить новый замер")
                
                with st.form("measurement_form"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        meas_date = st.date_input("Дата замера", value=date.today())
                    with col2:
                        weight = st.number_input("Вес (кг)", min_value=30.0, max_value=300.0, step=0.1)
                    with col3:
                        fat_percent = st.number_input("Процент жира (%)", min_value=0.0, max_value=60.0, step=0.1, value=0.0)
                    
                    muscle_mass = st.number_input("Мышечная масса (кг) (необязательно)", min_value=0.0, max_value=200.0, step=0.1, value=0.0)
                    
                    submit_meas = st.form_submit_button("➕ Добавить замер", type="primary", width='stretch')
                    
                    if submit_meas:
                        new_meas = UserMeasurement(
                            user_id=current_user.user_id,
                            date=meas_date,
                            weight=weight,
                            fat_percent=fat_percent if fat_percent > 0 else None,
                            muscle_mass=muscle_mass if muscle_mass > 0 else None
                        )
                        session.add(new_meas)
                        session.commit()
                        st.success("✅ Замер веса успешно добавлен! Теперь на Главной странице обновятся расчеты.")
                        st.rerun()
                
                st.markdown("---")
                
                # ---------------------------------------------------------------------
                # ИСТОРИЯ ЗАМЕРОВ
                # ---------------------------------------------------------------------
                st.subheader("📜 История ваших замеров")
                
                measurements = session.query(UserMeasurement).filter(
                    UserMeasurement.user_id == current_user.user_id
                ).order_by(UserMeasurement.date.desc()).all()
                
                if measurements:
                    # Создаем красивую таблицу через pandas (Streamlit это любит)
                    import pandas as pd
                    data = []
                    for m in measurements:
                        data.append({
                            "Дата": m.date.strftime("%d.%m.%Y"),
                            "Вес (кг)": m.weight,
                            # Явно преобразуем в строку или ставим прочерк, чтобы не было смешения типов float и str
                            "Жир (%)": f"{m.fat_percent}" if m.fat_percent is not None else "-",
                            "Мышцы (кг)": f"{m.muscle_mass}" if m.muscle_mass is not None else "-"
                        })
                    df = pd.DataFrame(data)
                    st.dataframe(df, width='stretch', hide_index=True)
                else:
                    st.info("📭 Замеров пока нет. Добавьте первый замер выше!")
                st.markdown("---")
                
                # ---------------------------------------------------------------------
                # ФОРМА 3: УМНЫЕ ЦЕЛИ (Расчет макросов на основе желаемого веса)
                # ---------------------------------------------------------------------
                st.subheader("🎯 Целевые показатели")
                st.caption("Укажи, к какому весу ты стремишься, и приложение само рассчитает идеальные КБЖУ.")
                
                # Проверяем, есть ли базовые данные для расчета
                latest_meas = session.query(UserMeasurement).filter(
                    UserMeasurement.user_id == current_user.user_id
                ).order_by(UserMeasurement.date.desc()).first()
                
                if not latest_meas or not latest_meas.weight or not current_user.height or not current_user.birth_date:
                    st.warning("⚠️ Сначала заполни рост, дату рождения и добавь хотя бы один замер веса в разделе выше, чтобы мы могли рассчитать цели!")
                else:
                    current_goal = session.query(UserGoal).filter(UserGoal.user_id == current_user.user_id).first()
                    
                    with st.form("smart_goals_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            def_target_w = current_goal.target_weight if current_goal and current_goal.target_weight else latest_meas.weight
                            target_weight = st.number_input("Желаемый вес (кг)", min_value=30.0, max_value=300.0, value=float(def_target_w), step=0.5)
                            
                            def_target_m = current_goal.target_muscle_mass if current_goal and current_goal.target_muscle_mass else (latest_meas.muscle_mass or 0.0)
                            target_muscle = st.number_input("Желаемая мышечная масса (кг) (необязательно)", min_value=0.0, max_value=200.0, value=float(def_target_m), step=0.5)
                        
                        with col2:
                            def_target_f = current_goal.target_fat_percent if current_goal and current_goal.target_fat_percent else (latest_meas.fat_percent or 15.0)
                            target_fat_pct = st.number_input("Желаемый % жира", min_value=5.0, max_value=50.0, value=float(def_target_f), step=0.5)
                            
                            activity_levels = {
                                "🛋️ Сидячий (1.2)": 1.2,
                                "🚶 Легкая активность (1.375)": 1.375,
                                "🏃 Умеренная активность (1.55)": 1.55,
                                "🏋️ Высокая активность (1.725)": 1.725,
                            }
                            # Дефолтное значение активности
                            default_act_idx = 2 
                            selected_activity = st.selectbox("Твой уровень активности:", list(activity_levels.keys()), index=default_act_idx)
                            activity_mult = activity_levels[selected_activity]
                        
                        submit_goals = st.form_submit_button("🧮 Рассчитать и сохранить цели", type="primary", width='stretch')
                        
                        if submit_goals:
                            # Вызываем нашу новую умную функцию!
                            age = calculate_age(current_user.birth_date)
                            macros = calculate_macro_goals(
                                current_weight=latest_meas.weight,
                                target_weight=target_weight,
                                height=current_user.height,
                                age=age,
                                gender=current_user.gender or 'male',
                                activity_multiplier=activity_mult
                            )
                            
                            if current_goal:
                                current_goal.target_weight = target_weight
                                current_goal.target_muscle_mass = target_muscle if target_muscle > 0 else None
                                current_goal.target_fat_percent = target_fat_pct
                                current_goal.target_calories = macros['calories']
                                current_goal.target_protein = macros['protein']
                                current_goal.target_fat = macros['fat']
                                current_goal.target_carbs = macros['carbs']
                            else:
                                new_goal = UserGoal(
                                    user_id=current_user.user_id,
                                    target_weight=target_weight,
                                    target_muscle_mass=target_muscle if target_muscle > 0 else None,
                                    target_fat_percent=target_fat_pct,
                                    target_calories=macros['calories'],
                                    target_protein=macros['protein'],
                                    target_fat=macros['fat'],
                                    target_carbs=macros['carbs']
                                )
                                session.add(new_goal)
                            
                            session.commit()
                            
                            st.success("✅ Цели рассчитаны и сохранены!")
                            st.info(f"📊 **Твоя новая норма:** {macros['calories']} ккал | Б: {macros['protein']}г | Ж: {macros['fat']}г | У: {macros['carbs']}г")
                            st.rerun()
                    st.markdown("---")
                    st.subheader("🧪 Цели по микронутриентам")
                    st.caption("Приложение предложило нормы на основе твоего пола и веса. Ты можешь их изменить.")
                    
                    # Получаем текущие цели или генерируем дефолтные
                    current_goal = session.query(UserGoal).filter(UserGoal.user_id == current_user.user_id).first()
                    default_micros = get_standard_micro_goals(current_user.gender or 'male', latest_meas.weight)
                    
                    with st.form("micro_goals_form"):
                        cols = st.columns(4)
                        micro_fields = [
                            ('Витамин A (мкг)', 'target_vit_a', default_micros['vit_a']),
                            ('Витамин C (мг)', 'target_vit_c', default_micros['vit_c']),
                            ('Витамин D (мкг)', 'target_vit_d', default_micros['vit_d']),
                            ('Витамин E (мг)', 'target_vit_e', default_micros['vit_e']),
                            ('Витамин K (мкг)', 'target_vit_k', default_micros['vit_k']),
                            ('Витамины B (мг)', 'target_vit_b', default_micros['vit_b']),
                            ('Железо (мг)', 'target_iron', default_micros['iron']),
                            ('Кальций (мг)', 'target_calcium', default_micros['calcium']),
                            ('Магний (мг)', 'target_magnesium', default_micros['magnesium']),
                            ('Цинк (мг)', 'target_zinc', default_micros['zinc']),
                            ('Йод (мкг)', 'target_iodine', default_micros['iodine']),
                            ('Селен (мкг)', 'target_selenium', default_micros['selenium']),
                        ]
                        
                        # Динамически создаем поля ввода
                        micro_inputs = {}
                        for i, (label, db_field, default_val) in enumerate(micro_fields):
                            with cols[i % 4]:
                                current_val = getattr(current_goal, db_field) if current_goal and getattr(current_goal, db_field) else default_val
                                micro_inputs[db_field] = st.number_input(label, min_value=0.0, value=float(current_val), step=1.0, key=f"micro_{db_field}")
                        
                        submit_micro = st.form_submit_button("💾 Сохранить цели по микронутриентам", width='stretch')
                        
                        if submit_micro:
                            if not current_goal:
                                current_goal = UserGoal(user_id=current_user.user_id)
                                session.add(current_goal)
                            
                            for db_field, value in micro_inputs.items():
                                setattr(current_goal, db_field, value if value > 0 else None)
                            
                            session.commit()
                            st.success("✅ Цели по микронутриентам обновлены!")
                            st.rerun()
                st.markdown("---")
                
                # ---------------------------------------------------------------------
                # РАЗДЕЛ: АЛЛЕРГИИ И НЕПЕРЕНОСИМОСТИ
                # ---------------------------------------------------------------------
                st.subheader("⚠️ Аллергии и пищевые непереносимости")
                st.caption("Отметь продукты, которые тебе нельзя употреблять. Это важно для будущего автоматического построения рациона.")
                
                # Получаем список всех доступных аллергенов из справочника
                all_allergens = session.query(Allergen).order_by(Allergen.name).all()
                
                # Если справочник пуст, создаем базовые аллергены
                if not all_allergens:
                    common_allergens = [
                        'milk', 'gluten', 'nuts', 'eggs', 'soy', 
                        'fish', 'shellfish', 'peanuts', 'wheat', 'dairy'
                    ]
                    for allergen_name in common_allergens:
                        new_allergen = Allergen(name=allergen_name)
                        session.add(new_allergen)
                    session.commit()
                    all_allergens = session.query(Allergen).order_by(Allergen.name).all()
                
                # Получаем текущие аллергии пользователя
                user_allergies = session.query(UserAllergy).filter(
                    UserAllergy.user_id == current_user.user_id
                ).all()
                user_allergen_ids = {ua.allergen_id for ua in user_allergies}
                
                # Создаем словарь для отображения (английский -> русский)
                allergen_display_names = {
                    'milk': '🥛 Молоко и молочные продукты',
                    'gluten': '🌾 Глютен (пшеница, рожь, ячмень)',
                    'nuts': '🌰 Орехи (все виды)',
                    'eggs': ' Яйца',
                    'soy': '🫘 Соя и соевые продукты',
                    'fish': '🐟 Рыба',
                    'shellfish': '🦐 Морепродукты (креветки, крабы)',
                    'peanuts': ' Арахис',
                    'wheat': '🌾 Пшеница',
                    'dairy': '🧀 Молочные продукты (сыр, йогурт)'
                }
                
                with st.form("allergies_form"):
                    # Показываем чекбоксы в 2 колонки
                    cols_allergy = st.columns(2)
                    selected_allergens = []
                    
                    for i, allergen in enumerate(all_allergens):
                        with cols_allergy[i % 2]:
                            display_name = allergen_display_names.get(allergen.name, allergen.name)
                            is_checked = allergen.allergen_id in user_allergen_ids
                            
                            if st.checkbox(display_name, value=is_checked, key=f"allergy_{allergen.allergen_id}"):
                                selected_allergens.append(allergen.allergen_id)
                    
                    submit_allergies = st.form_submit_button(" Сохранить аллергии", type="primary", width='stretch')
                    
                    if submit_allergies:
                        # Удаляем старые аллергии
                        for ua in user_allergies:
                            session.delete(ua)
                        
                        # Добавляем новые выбранные аллергии
                        for allergen_id in selected_allergens:
                            new_allergy = UserAllergy(
                                user_id=current_user.user_id,
                                allergen_id=allergen_id
                            )
                            session.add(new_allergy)
                        
                        session.commit()
                        st.success(f"✅ Аллергии обновлены! Выбрано: {len(selected_allergens)}")
                        st.rerun()
                
                # Показываем текущие аллергии красивым списком
                if user_allergies:
                    st.markdown("##### 📋 Твои текущие аллергии:")
                    allergy_names = []
                    for ua in user_allergies:
                        allergen = session.query(Allergen).filter(Allergen.allergen_id == ua.allergen_id).first()
                        if allergen:
                            display_name = allergen_display_names.get(allergen.name, allergen.name)
                            allergy_names.append(display_name)
                    
                    for allergy_name in sorted(allergy_names):
                        st.write(f"• {allergy_name}")
                else:
                    st.info("✅ У тебя пока нет отмеченных аллергий.")

                    pass 

            with tab_analyses:
                # =========================================================================
                # СТРАНИЦА МЕДИЦИНСКИХ АНАЛИЗОВ
                # =========================================================================

                st.header("🩺 Дневник медицинских анализов")
                st.info("💡 Заполняйте только те показатели, которые вы сдали. Приложение запомнит единицы измерения и построит график динамики.")
                
                # СЛОВАРЬ ПОКАЗАТЕЛЕЙ (Можешь легко добавить сюда остальные из твоего списка)
                MEDICAL_INDICATORS = {
                    "🩸 Общий анализ крови": {
                        "Гемоглобин": "г/л",
                        "Эритроциты": "10^12/л",
                        "Лейкоциты": "10^9/л",
                        "Тромбоциты": "10^9/л",
                        "Гематокрит": "%",
                        "MCV (средний объем эритроцита)": "фл",
                        "MCH (среднее содержание Hb)": "пг"
                    },
                    "🧪 Биохимический анализ крови": {
                        "Общий белок": "г/л",
                        "Альбумин": "г/л",
                        "Глюкоза": "ммоль/л",
                        "Холестерин общий": "ммоль/л",
                        "Холестерин ЛПВП": "ммоль/л",
                        "Холестерин ЛПНП": "ммоль/л",
                        "Триглицериды": "ммоль/л",
                        "АЛТ": "Ед/л",
                        "АСТ": "Ед/л",
                        "Билирубин общий": "мкмоль/л",
                        "Креатинин": "мкмоль/л",
                        "Мочевая кислота": "мкмоль/л",
                        "Ферритин": "мкг/л",
                        "Витамин D (25-OH)": "нг/мл",
                        "ТТГ": "мкМЕ/мл"
                    },
                    "💧 Общий анализ мочи": {
                        "Белок": "г/л",
                        "Глюкоза": "ммоль/л",
                        "Лейкоциты": "в п/зр",
                        "Эритроциты": "в п/зр",
                        "Удельный вес": ""
                    }
                }
                
                tab_input, tab_graph = st.tabs(["➕ Внести результаты", "📈 График динамики"])
                
                # ---------------------------------------------------------------------
                # ВКЛАДКА 1: ВВОД ДАННЫХ
                # ---------------------------------------------------------------------
                with tab_input:
                    test_date = st.date_input("📅 Дата сдачи анализов:", value=date.today())
                    
                    with st.form("medical_form"):
                        for category, indicators in MEDICAL_INDICATORS.items():
                            with st.expander(category):
                                for name, unit in indicators.items():
                                    unit_str = f" ({unit})" if unit else ""
                                    
                                    # ИСПРАВЛЕНИЕ: добавили {category} в ключ для уникальности
                                    st.number_input(
                                        f"{name}{unit_str}", 
                                        min_value=0.0, 
                                        value=0.0, 
                                        step=0.1, 
                                        key=f"med_{category}_{name}_{test_date}"
                                    )
                        
                        submit_med = st.form_submit_button("💾 Сохранить результаты анализов", type="primary", width='stretch')
                        
                        if submit_med:
                            saved_count = 0
                            for category, indicators in MEDICAL_INDICATORS.items():
                                for name, unit in indicators.items():
                                    # ИСПРАВЛЕНИЕ: читаем по новому уникальному ключу
                                    val = st.session_state[f"med_{category}_{name}_{test_date}"]
                                    if val > 0.0:
                                        # Проверяем, нет ли уже такой записи на эту дату (чтобы не дублировать при повторном нажатии)
                                        existing = session.query(MedicalResult).filter(
                                            MedicalResult.user_id == current_user.user_id,
                                            MedicalResult.test_date == test_date,
                                            MedicalResult.test_name == name
                                        ).first()
                                        
                                        if existing:
                                            existing.value = val # Обновляем, если уже есть
                                        else:
                                            new_result = MedicalResult(
                                                user_id=current_user.user_id,
                                                test_date=test_date,
                                                test_category=category,
                                                test_name=name,
                                                value=val,
                                                unit=unit
                                            )
                                            session.add(new_result)
                                        saved_count += 1
                            
                            session.commit()
                            st.success(f"✅ Успешно сохранено {saved_count} показателей за {test_date.strftime('%d.%m.%Y')}!")
                            st.rerun()

                # ---------------------------------------------------------------------
                # ВКЛАДКА 2: ГРАФИК ДИНАМИКИ
                # ---------------------------------------------------------------------
                with tab_graph:
                    st.subheader("📈 Динамика конкретного показателя")
                    
                    # Получаем список всех уникальных показателей, которые когда-либо сдавал этот пользователь
                    user_results = session.query(MedicalResult).filter(
                        MedicalResult.user_id == current_user.user_id
                    ).all()
                    
                    if user_results:
                        # Создаем уникальный отсортированный список названий
                        unique_tests = sorted(list(set([r.test_name for r in user_results])))
                        
                        selected_test = st.selectbox("Выберите показатель для графика:", unique_tests)
                        
                        if selected_test:
                            # Находим единицу измерения для этого показателя
                            unit = next((r.unit for r in user_results if r.test_name == selected_test), "")
                            unit_str = f" ({unit})" if unit else ""
                            
                            # Получаем историю по этому показателю, отсортированную по дате
                            history = session.query(MedicalResult).filter(
                                MedicalResult.user_id == current_user.user_id,
                                MedicalResult.test_name == selected_test
                            ).order_by(MedicalResult.test_date).all()
                            
                            if len(history) >= 1:
                                import plotly.graph_objects as go
                                
                                dates = [h.test_date for h in history]
                                values = [h.value for h in history]
                                
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=dates,
                                    y=values,
                                    mode='lines+markers',
                                    name=selected_test,
                                    line=dict(color='#9b59b6', width=3),
                                    marker=dict(size=8),
                                    hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Значение: %{y:.2f}' + unit_str + '<extra></extra>'
                                ))
                                
                                fig.update_layout(
                                    title=f'Динамика: {selected_test}',
                                    xaxis_title='Дата',
                                    yaxis_title=f'Значение{unit_str}',
                                    hovermode='x unified',
                                    height=500,
                                    template='plotly_white'
                                )
                                
                                st.plotly_chart(fig, width='stretch')
                                
                                # Таблица с историей
                                import pandas as pd
                                df_hist = pd.DataFrame([{
                                    "Дата": h.test_date.strftime("%d.%m.%Y"),
                                    "Значение": h.value,
                                    "Ед. изм.": h.unit or "-"
                                } for h in history])
                                
                                st.markdown("##### 📜 История значений:")
                                st.dataframe(df_hist, width='stretch', hide_index=True)
                            else:
                                st.info("Недостаточно данных для построения графика.")
                    else:
                        st.info("📭 Вы еще не внесли ни одного результата анализов. Перейдите во вкладку 'Внести результаты'.")
                pass

            with tab_progress:
                # ============================================================================
                # СТРАНИЦА ПРОГРЕССА
                # ============================================================================

                st.header("📊 Прогресс и аналитика")
                
                user = session.query(User).first()
                
                if not user:
                    st.error("Пользователь не найден!")
                else:
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📈 Вес тела", 
                        "💪 Силовые показатели", 
                        " БЖУ за день",
                        " Калории по дням"
                    ])
                    
                    # ====================================================================
                    # ВКЛАДКА 1: ГРАФИК ВЕСА ТЕЛА
                    # ====================================================================
                    with tab1:
                        st.subheader(" Динамика веса тела")
                        
                        measurements = session.query(UserMeasurement).filter(
                            UserMeasurement.user_id == current_user.user_id,
                            UserMeasurement.weight.isnot(None)
                        ).order_by(UserMeasurement.date).all()
                        
                        if measurements:
                            import plotly.graph_objects as go
                            
                            dates = [m.date for m in measurements]
                            weights = [m.weight for m in measurements]
                            
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=dates,
                                y=weights,
                                mode='lines+markers',
                                name='Вес',
                                line=dict(color='#1f77b4', width=3),
                                marker=dict(size=8),
                                hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Вес: %{y:.1f} кг<extra></extra>'
                            ))
                            
                            fig.update_layout(
                                title='Изменение веса по дням',
                                xaxis_title='Дата',
                                yaxis_title='Вес (кг)',
                                hovermode='x unified',
                                height=500,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig, width="stretch")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Текущий вес", f"{weights[-1]:.1f} кг")
                            with col2:
                                st.metric("Минимальный вес", f"{min(weights):.1f} кг")
                            with col3:
                                st.metric("Максимальный вес", f"{max(weights):.1f} кг")
                            
                            if len(weights) > 1:
                                change = weights[-1] - weights[0]
                                if change > 0:
                                    st.info(f"📈 Изменение за весь период: **+{change:.1f} кг**")
                                elif change < 0:
                                    st.success(f"📉 Изменение за весь период: **{change:.1f} кг**")
                                else:
                                    st.info(f"➡️ Вес не изменился за весь период")
                        else:
                            st.warning("📭 Нет данных о замерах веса. Добавь замеры на главной странице.")
                    
                    # ====================================================================
                    # ВКЛАДКА 2: СИЛОВЫЕ ПОКАЗАТЕЛИ
                    # ====================================================================
                    with tab2:
                        st.subheader(" Прогресс в упражнениях")
                        
                        exercises_with_logs = session.query(Exercise).join(WorkoutLog).all()
                        
                        if exercises_with_logs:
                            ex_options = {e.name: e for e in exercises_with_logs}
                            selected_ex_name = st.selectbox(
                                "Выбери упражнение:",
                                options=list(ex_options.keys())
                            )
                            
                            if selected_ex_name:
                                selected_ex = ex_options[selected_ex_name]
                                
                                logs = session.query(WorkoutLog).join(Workout).filter(
                                    WorkoutLog.exercise_id == selected_ex.exercise_id,
                                    Workout.user_id == current_user.user_id,
                                    WorkoutLog.weight.isnot(None)
                                ).order_by(Workout.date).all()
                                
                                if logs:
                                    import plotly.graph_objects as go
                                    
                                    dates = [log.workout.date for log in logs]
                                    weights = [log.weight for log in logs]
                                    volumes = [log.sets * log.reps * log.weight for log in logs]
                                    
                                    fig = go.Figure()
                                    
                                    fig.add_trace(go.Scatter(
                                        x=dates,
                                        y=weights,
                                        mode='lines+markers',
                                        name='Вес (кг)',
                                        line=dict(color='#ff7f0e', width=3),
                                        marker=dict(size=8),
                                        yaxis='y1',
                                        hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Вес: %{y:.1f} кг<extra></extra>'
                                    ))
                                    
                                    fig.add_trace(go.Scatter(
                                        x=dates,
                                        y=volumes,
                                        mode='lines+markers',
                                        name='Объем (кг)',
                                        line=dict(color='#2ca02c', width=2, dash='dash'),
                                        marker=dict(size=6),
                                        yaxis='y2',
                                        hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Объем: %{y:.0f} кг<extra></extra>'
                                    ))
                                    
                                    fig.update_layout(
                                        title=f'Прогресс: {selected_ex_name}',
                                        xaxis_title='Дата',
                                        yaxis=dict(
                                            title=dict(text='Вес (кг)', font=dict(color='#ff7f0e'))
                                        ),
                                        yaxis2=dict(
                                            title=dict(text='Объем (кг)', font=dict(color='#2ca02c')),
                                            overlaying='y',
                                            side='right'
                                        ),
                                        hovermode='x unified',
                                        height=500,
                                        template='plotly_white',
                                        legend=dict(x=0, y=1.1, orientation='h')
                                    )
                                    
                                    st.plotly_chart(fig, width="stretch")
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Максимальный вес", f"{max(weights):.1f} кг")
                                    with col2:
                                        st.metric("Текущий вес", f"{weights[-1]:.1f} кг")
                                    with col3:
                                        st.metric("Всего тренировок", f"{len(logs)}")
                                else:
                                    st.info(f"📭 Нет данных по упражнению '{selected_ex_name}'")
                        else:
                            st.warning("📭 Нет данных о тренировках. Добавь хотя бы одну тренировку.")
                    
                    # ====================================================================
                    # ВКЛАДКА 3: БЖУ ЗА ДЕНЬ
                    # ====================================================================
                    with tab3:
                        st.subheader("🥧 Соотношение БЖУ за день")
                        
                        macro_date = st.date_input(
                            "Выбери дату:",
                            value=date.today(),
                            max_value=date.today(),
                            key="macro_date"
                        )
                        
                        day_logs = session.query(FoodLog).filter(
                            FoodLog.user_id == current_user.user_id,
                            FoodLog.date == macro_date
                        ).all()
                        
                        if day_logs:
                            # ✅ ИСПРАВЛЕНИЕ: Создаем словарь продуктов и передаем его в функцию
                            all_foods_dict = {}
                            for f in get_all_foods():
                                all_foods_dict[f.name] = f
                            for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                                all_foods_dict[f.name] = f
                                
                            totals = calculate_daily_totals(day_logs, all_foods_dict)
                            
                            if totals['protein'] > 0 or totals['fat'] > 0 or totals['carbs'] > 0:
                                import plotly.graph_objects as go
                                
                                labels = ['Белки', 'Жиры', 'Углеводы']
                                values = [totals['protein'], totals['fat'], totals['carbs']]
                                colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
                                
                                fig = go.Figure(data=[go.Pie(
                                    labels=labels,
                                    values=values,
                                    hole=.4,
                                    marker=dict(colors=colors),
                                    textinfo='label+percent',
                                    hovertemplate='<b>%{label}</b><br>%{value:.1f}г<br>%{percent}<extra></extra>'
                                )])
                                
                                fig.update_layout(
                                    title=f'БЖУ за {macro_date.strftime("%d.%m.%Y")}',
                                    height=500,
                                    annotations=[dict(
                                        text=f'<b>{totals["calories"]:.0f}</b><br>ккал',
                                        x=0.5, y=0.5,
                                        font_size=20,
                                        showarrow=False
                                    )]
                                )
                                
                                st.plotly_chart(fig, width="stretch")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("🥩 Белки", f"{totals['protein']:.1f} г")
                                with col2:
                                    st.metric("🥑 Жиры", f"{totals['fat']:.1f} г")
                                with col3:
                                    st.metric("🍞 Углеводы", f"{totals['carbs']:.1f} г")
                            else:
                                st.info("📭 Нет данных о макронутриентах за этот день")
                        else:
                            st.info(f"📭 Нет записей о питании за {macro_date.strftime('%d.%m.%Y')}")
                    
                    # ====================================================================
                    # ВКЛАДКА 4: КАЛОРИИ ПО ДНЯМ
                    # ====================================================================
                    with tab4:
                        st.subheader("🔥 Динамика калорийности по дням")
                        
                        all_food_logs = session.query(FoodLog).filter(
                            FoodLog.user_id == current_user.user_id
                        ).all()
                        
                        if all_food_logs:
                            import plotly.graph_objects as go
                            from collections import defaultdict
                            
                            # ✅ ИСПРАВЛЕНИЕ: Создаем словарь продуктов
                            all_foods_dict = {}
                            for f in get_all_foods():
                                all_foods_dict[f.name] = f
                            for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                                all_foods_dict[f.name] = f
                            
                            calories_by_date = defaultdict(float)
                            for log in all_food_logs:
                                # ✅ ИСПРАВЛЕНИЕ: Используем food_name и словарь вместо log.food
                                food_item = all_foods_dict.get(log.food_name)
                                macros = calculate_food_calories(food_item, log.weight_eaten) if food_item else {'calories': 0}
                                calories_by_date[log.date] += macros['calories']
                            
                            sorted_dates = sorted(calories_by_date.keys())
                            calories = [calories_by_date[d] for d in sorted_dates]
                            
                            fig = go.Figure()
                            
                            fig.add_trace(go.Bar(
                                x=sorted_dates,
                                y=calories,
                                marker_color='#ef553b',
                                hovertemplate='<b>%{x|%d.%m.%Y}</b><br>Калории: %{y:.0f} ккал<extra></extra>'
                            ))
                            
                            fig.update_layout(
                                title='Потребление калорий по дням',
                                xaxis_title='Дата',
                                yaxis_title='Калории (ккал)',
                                hovermode='x unified',
                                height=500,
                                template='plotly_white'
                            )
                            
                            st.plotly_chart(fig, width="stretch")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                avg_calories = sum(calories) / len(calories)
                                st.metric("Среднее за день", f"{avg_calories:.0f} ккал")
                            with col2:
                                st.metric("Минимум", f"{min(calories):.0f} ккал")
                            with col3:
                                st.metric("Максимум", f"{max(calories):.0f} ккал")
                        else:
                            st.warning("📭 Нет данных о питании. Добавь хотя бы один прием пищи.")
                pass
        # ============================================================================
        # СТРАНИЦА ПИТАНИЯ
        # ============================================================================

        elif page == "🍎 Питание":
            st.header("🍎 Управление питанием")
            
            # Создаем верхние вкладки
            tab_diary, tab_reference = st.tabs([
                "📝 Дневник питания", 
                "🥗 Справочник моей еды"
            ])
            user = session.query(User).first()
            
            if not user:
                st.error("Пользователь не найден!")
            else:
                # ====== ВЫБОР ДАТЫ ======
                selected_date = st.date_input(
                    "📅 Выбери дату:",
                    value=date.today(),
                    max_value=date.today()
                )
            with tab_diary:
                st.subheader("➕ Добавить прием пищи")
                
                # =========================================================================
                # 1. СЕЛЕКТОР ПРОДУКТА (СНАРУЖИ ФОРМЫ - для мгновенного обновления UI)
                # =========================================================================
                
                show_only_basic = st.checkbox("🥬 Показывать только базовые продукты (ингредиенты)", value=True, key="filter_basic_add_meal")
                
                # Собираем доступные продукты
                available_foods = []
                for f in get_all_foods():
                    if not show_only_basic or getattr(f, 'is_basic', True):
                        available_foods.append(f)
                
                for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                    if not show_only_basic or getattr(f, 'is_basic', True):
                        available_foods.append(f)
                
                # Сортируем по имени
                available_foods.sort(key=lambda x: x.name)
                food_options = {f.name: f for f in available_foods}
                
                # ЕДИНСТВЕННЫЙ selectbox с этим ключом во всем файле!
                food_choice = st.selectbox(
                    "Выбери продукт:",
                    options=["🔍 Другое (добавить свой)"] + list(food_options.keys()),
                    key="simple_food_choice_selector"
                )

                # =========================================================================
                # 2. ОСНОВНАЯ ФОРМА (ВНУТРИ - для группировки отправки)
                # =========================================================================
                with st.form("add_food_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if food_choice != "🔍 Другое (добавить свой)":
                            selected_preview = food_options[food_choice]
                            
                            # 1. Основной блок с КБЖУ (всегда виден)
                            st.info(
                                f"📊 **КБЖУ на 100г:** {selected_preview.calories_per_100g} ккал | "
                                f"Б: {selected_preview.protein_per_100g}г | "
                                f"Ж: {selected_preview.fat_per_100g}г | "
                                f"У: {selected_preview.carbs_per_100g}г"
                            )
                            
                            # 2. Динамический сбор микронутриентов (проверяем, что они не None)
                            micros = []
                            if selected_preview.vitamin_a is not None: micros.append(f"Вит. А: {selected_preview.vitamin_a} мкг")
                            if selected_preview.vitamin_c is not None: micros.append(f"Вит. C: {selected_preview.vitamin_c} мг")
                            if selected_preview.vitamin_d is not None: micros.append(f"Вит. D: {selected_preview.vitamin_d} мкг")
                            if selected_preview.vitamin_e is not None: micros.append(f"Вит. E: {selected_preview.vitamin_e} мг")
                            if selected_preview.vitamin_k is not None: micros.append(f"Вит. K: {selected_preview.vitamin_k} мкг")
                            if selected_preview.vitamin_b_complex is not None: micros.append(f"Вит. B: {selected_preview.vitamin_b_complex} мг")
                            if selected_preview.iron is not None: micros.append(f"Железо: {selected_preview.iron} мг")
                            if selected_preview.calcium is not None: micros.append(f"Кальций: {selected_preview.calcium} мг")
                            if selected_preview.magnesium is not None: micros.append(f"Магний: {selected_preview.magnesium} мг")
                            if selected_preview.zinc is not None: micros.append(f"Цинк: {selected_preview.zinc} мг")
                            if selected_preview.iodine is not None: micros.append(f"Йод: {selected_preview.iodine} мкг")
                            if selected_preview.selenium is not None: micros.append(f"Селен: {selected_preview.selenium} мкг")
                            
                            # 3. Показываем блок только если есть хотя бы один микронутриент
                            if micros:
                                with st.expander("🧪 Содержит микронутриенты (на 100г)", expanded=False):
                                    cols = st.columns(3)
                                    for i, micro_text in enumerate(micros):
                                        with cols[i % 3]: # Распределяем по 3 колонкам для компактности
                                            st.caption(f"• {micro_text}")
                        else:
                            st.markdown("###### 🆕 Параметры нового продукта")
                            new_food_name = st.text_input("Название нового продукта:", key="simple_new_food_name")
                            col_cal, col_p, col_f, col_c = st.columns(4)
                            with col_cal:
                                new_cal = st.number_input("Ккал/100г", min_value=0.0, value=100.0, step=1.0, key="simple_new_cal")
                            with col_p:
                                new_prot = st.number_input("Белки/100г", min_value=0.0, value=0.0, step=0.1, key="simple_new_prot")
                            with col_f:
                                new_fat = st.number_input("Жиры/100г", min_value=0.0, value=0.0, step=0.1, key="simple_new_fat")
                            with col_c:
                                new_carb = st.number_input("Углеводы/100г", min_value=0.0, value=0.0, step=0.1, key="simple_new_carb")
                            
                            with st.expander("🧪 Микронутриенты (витамины и минералы)", expanded=False):
                                st.caption("Укажите содержание на 100г продукта. Оставьте 0, если не знаете.")
                                
                                col_vit1, col_vit2, col_vit3 = st.columns(3)
                                with col_vit1:
                                    new_vit_a = st.number_input("Витамин А (мкг)", min_value=0.0, value=0.0, step=1.0, key="simple_vit_a")
                                    new_vit_c = st.number_input("Витамин C (мг)", min_value=0.0, value=0.0, step=1.0, key="simple_vit_c")
                                    new_vit_d = st.number_input("Витамин D (мкг)", min_value=0.0, value=0.0, step=0.1, key="simple_vit_d")
                                with col_vit2:
                                    new_vit_e = st.number_input("Витамин E (мг)", min_value=0.0, value=0.0, step=0.1, key="simple_vit_e")
                                    new_vit_k = st.number_input("Витамин K (мкг)", min_value=0.0, value=0.0, step=1.0, key="simple_vit_k")
                                    new_vit_b = st.number_input("Витамины B-группы (мг)", min_value=0.0, value=0.0, step=0.1, key="simple_vit_b")
                                with col_vit3:
                                    new_iron = st.number_input("Железо (мг)", min_value=0.0, value=0.0, step=0.1, key="simple_iron")
                                    new_calcium = st.number_input("Кальций (мг)", min_value=0.0, value=0.0, step=1.0, key="simple_calcium")
                                    new_magnesium = st.number_input("Магний (мг)", min_value=0.0, value=0.0, step=1.0, key="simple_magnesium")
                                
                                col_min1, col_min2, col_min3 = st.columns(3)
                                with col_min1:
                                    new_zinc = st.number_input("Цинк (мг)", min_value=0.0, value=0.0, step=0.1, key="simple_zinc")
                                    new_iodine = st.number_input("Йод (мкг)", min_value=0.0, value=0.0, step=1.0, key="simple_iodine")
                                    new_selenium = st.number_input("Селен (мкг)", min_value=0.0, value=0.0, step=1.0, key="simple_selenium")
                            with st.expander("🏷️ Категории продукта", expanded=False):
                                st.caption("Выбери одну или несколько категорий (например, 'Молочные' и 'Грибы' для крем-супа)")
                                all_categories = get_all_categories()
                                selected_cats = []
                                cols_cat = st.columns(3)
                                for i, cat in enumerate(all_categories):
                                    with cols_cat[i % 3]:
                                        if st.checkbox(f"{cat.icon} {cat.display_name}", key=f"cat_{cat.category_id}"):
                                            selected_cats.append(cat.name)
                        
                        weight = st.number_input(
                            "Сколько грамм съел?",
                            min_value=1,
                            max_value=5000,
                            value=100,
                            step=10,
                            key="simple_weight_input"
                        )
                    
                    with col2:
                        meal_date = st.date_input("Дата приема:", value=selected_date, key="simple_meal_date_input")
                        
                        meal_type = st.selectbox(
                            "Тип приема пищи:",
                            ["breakfast", "lunch", "dinner", "snack"],
                            format_func=lambda x: {
                                "breakfast": "🌅 Завтрак",
                                "lunch": "☀️ Обед",
                                "dinner": "🌙 Ужин",
                                "snack": "🍪 Перекус"
                            }[x],
                            key="simple_meal_type_input"
                        )
                    
                    submitted = st.form_submit_button("✅ Добавить", type="primary", width='stretch')
                    
                    if submitted:
                        if food_choice == "🔍 Другое (добавить свой)":
                            if not new_food_name:
                                st.error("❌ Введи название продукта!")
                                st.stop()
                            
                            existing = session.query(CustomFood).filter(CustomFood.name.ilike(new_food_name)).first()
                            if existing:
                                selected_food = existing
                                st.info(f"ℹ️ Продукт '{new_food_name}' уже есть в справочнике, используем его")
                            else:
                                selected_food = CustomFood(
                                    user_id=current_user.user_id,
                                    name=new_food_name,
                                    calories_per_100g=new_cal,
                                    protein_per_100g=new_prot,
                                    fat_per_100g=new_fat,
                                    carbs_per_100g=new_carb,
                                    # Сохраняем выбранные категории через запятую
                                    categories=",".join(selected_cats) if 'selected_cats' in locals() and selected_cats else None,
                                    # Микронутриенты
                                    vitamin_a=new_vit_a if new_vit_a > 0 else None,
                                    vitamin_c=new_vit_c if new_vit_c > 0 else None,
                                    vitamin_d=new_vit_d if new_vit_d > 0 else None,
                                    vitamin_e=new_vit_e if new_vit_e > 0 else None,
                                    vitamin_k=new_vit_k if new_vit_k > 0 else None,
                                    vitamin_b_complex=new_vit_b if new_vit_b > 0 else None,
                                    iron=new_iron if new_iron > 0 else None,
                                    calcium=new_calcium if new_calcium > 0 else None,
                                    magnesium=new_magnesium if new_magnesium > 0 else None,
                                    zinc=new_zinc if new_zinc > 0 else None,
                                    iodine=new_iodine if new_iodine > 0 else None,
                                    selenium=new_selenium if new_selenium > 0 else None
                                )
                                session.add(selected_food)
                                session.commit()
                                st.success(f"✅ Продукт '{new_food_name}' добавлен в справочник!")
                        else:
                            selected_food = food_options[food_choice]
                        
                        # Создаем запись в дневнике (теперь используем food_name)
                        new_log = FoodLog(
                            user_id=current_user.user_id,
                            food_name=selected_food.name,
                            date=meal_date,
                            meal_type=meal_type,
                            weight_eaten=weight
                        )
                        session.add(new_log)
                        session.commit()
                        
                        macros = calculate_food_calories(selected_food, weight)
                        st.success(f"✅ Добавлено! Калории: {macros['calories']:.0f} ккал")
                        st.balloons()
                        st.rerun()

                st.markdown("---")
                st.subheader("🍲 Конструктор сложного блюда (Рецепт)")
                st.caption("Идеально для домашних блюд. Добавляй ингредиенты по одному, указывай вес, способ и время приготовления.")
                
                if 'recipe_components' not in st.session_state:
                    st.session_state.recipe_components = []
                
                # =========================================================================
                # ЧАСТЬ 1: ДИНАМИЧЕСКИЙ СПИСОК И ДОБАВЛЕНИЕ (СНАРУЖИ ФОРМЫ)
                # =========================================================================
                
                if st.session_state.recipe_components:
                    st.markdown("##### 📋 Текущие ингредиенты:")
                    for idx, comp in enumerate(st.session_state.recipe_components):
                        col_a, col_b, col_c, col_d, col_e = st.columns([3, 1, 2, 2, 1])
                        with col_a:
                            st.write(f"**{comp['food_name']}**")
                        with col_b:
                            st.write(f"{comp['weight']} г")
                        with col_c:
                            st.caption(f"Способ: {comp['method']}")
                        with col_d:
                            st.caption(f"Время: {comp['time']} мин")
                        with col_e:
                            if st.button("❌", key=f"remove_comp_{idx}"):
                                st.session_state.recipe_components.pop(idx)
                                st.rerun()
                    st.markdown("---")
                
                st.markdown("##### ➕ Добавить новый ингредиент")
                col_add1, col_add2, col_add3, col_add4 = st.columns([3, 1, 2, 2])
                with col_add1:
                    # ЖЕСТКАЯ ФИЛЬТРАЦИЯ: только is_basic == True
                    basic_foods_only = []
                    for f in get_all_foods():
                        if f.is_basic:
                            basic_foods_only.append(f)
                    for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                        if getattr(f, 'is_basic', True):
                            basic_foods_only.append(f)
                    
                    basic_foods_only.sort(key=lambda x: x.name)
                    food_options_builder = {f.name: f for f in basic_foods_only}
                    
                    new_comp_food = st.selectbox("Продукт из справочника:", list(food_options_builder.keys()), key="new_comp_food_select")
                with col_add2:
                    new_comp_weight = st.number_input("Вес (г)", min_value=1, value=100, step=10, key="new_comp_weight")
                with col_add3:
                    new_comp_method = st.selectbox(
                        "Способ приготовления", 
                        ["Без обработки", "Варка", "Жарка", "Тушение", "Запекание", "На пару", "Гриль", "Копчение"],
                        key="new_comp_method"
                    )
                with col_add4:
                    new_comp_time = st.number_input("Время (мин)", min_value=0, value=0, step=5, key="new_comp_time")
                
                if st.button("Добавить ингредиент в список", width='stretch'):
                    selected_food = food_options[new_comp_food]
                    st.session_state.recipe_components.append({
                        'food_name': selected_food.name, # Храним имя, а не ID
                        'weight': new_comp_weight,
                        'method': new_comp_method,
                        'time': new_comp_time
                    })
                    st.success(f"✅ {selected_food.name} добавлен!")
                    st.rerun()

                st.markdown("---")
                
                # =========================================================================
                # ЧАСТЬ 2: ФИНАЛЬНОЕ СОХРАНЕНИЕ (ВНУТРИ ФОРМЫ)
                # =========================================================================
                
                if st.session_state.recipe_components:
                    with st.form("save_complex_meal_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            dish_name = st.text_input("🍽 Название готового блюда (например, 'Плов с курицей'):")
                        with col2:
                            meal_type = st.selectbox("Прием пищи:", ["breakfast", "lunch", "dinner", "snack"], format_func=lambda x: {"breakfast": " Завтрак", "lunch": "️ Обед", "dinner": " Ужин", "snack": "🍪 Перекус"}[x])
                        
                        meal_date = st.date_input("Дата приготовления:", value=date.today())
                        st.caption("Приложение автоматически корректирует витамины и минералы в зависимости от времени и способа приготовления (например, вымывание при варке или впитывание масла при жарке).")
                
                        # Показываем итог прямо перед сохранением
                        foods_dict = {}
                        for f in get_all_foods():
                            foods_dict[f.name] = f
                        for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                            foods_dict[f.name] = f
                            
                        preview_totals = calculate_complex_meal_totals(st.session_state.recipe_components, foods_dict)
                        
                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            st.metric("🔥 Итого ккал", f"{preview_totals['calories']:.0f}")
                        with col_p2:
                            st.metric("🥩 Белки", f"{preview_totals['protein']:.1f} г")
                        with col_p3:
                            st.metric("🥑 Жиры", f"{preview_totals['fat']:.1f} г")
                        
                        st.markdown("---")
                        st.info(f"В блюдо будет добавлено ингредиентов: **{len(st.session_state.recipe_components)}**")
                        
                        submit_dish = st.form_submit_button("💾 Сохранить сложное блюдо в дневник", type="primary", width='stretch')
                        
                        if submit_dish:
                            if not dish_name:
                                st.error("❌ Введи название блюда!")
                            else:
                                # 1. Собираем ВСЕ продукты в словарь по ИМЕНИ для расчета
                                foods_dict = {}
                                for f in get_all_foods():
                                    foods_dict[f.name] = f
                                for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                                    foods_dict[f.name] = f
                                
                                totals = calculate_complex_meal_totals(st.session_state.recipe_components, foods_dict)
                                
                                # 2. Создаем запись ComplexMeal (для хранения деталей рецепта)
                                new_meal = ComplexMeal(
                                    user_id=current_user.user_id,
                                    date=meal_date,
                                    meal_type=meal_type,
                                    dish_name=dish_name,
                                    total_weight=totals['weight'],
                                    total_calories=totals['calories'],
                                    total_protein=totals['protein'],
                                    total_fat=totals['fat'],
                                    total_carbs=totals['carbs']
                                )
                                session.add(new_meal)
                                session.flush() # Получаем new_meal.meal_id
                                
                                # 3. Создаем компоненты блюда
                                for comp in st.session_state.recipe_components:
                                    new_comp = ComplexMealComponent(
                                        meal_id=new_meal.meal_id,
                                        food_name=comp['food_name'],
                                        weight=comp['weight'],
                                        cooking_method=comp['method'],
                                        cooking_time=comp['time'] if comp['time'] > 0 else None
                                    )
                                    session.add(new_comp)
                                
                                # 4. ВАЖНО: Проверяем, есть ли уже такое блюдо в справочнике (Определяем existing_food!)
                                existing_food = session.query(CustomFood).filter(
                                    CustomFood.name.ilike(dish_name),
                                    CustomFood.user_id == current_user.user_id
                                ).first()
                                
                                # 5. Собираем ВСЕ категории из ингредиентов для наследования
                                ingredient_categories = set()
                                all_cats = get_all_categories()
                                cat_name_map = {c.name: c.name for c in all_cats}
                                
                                for comp in st.session_state.recipe_components:
                                    f_name = comp['food_name']
                                    # Ищем продукт в базе
                                    f_obj = next((f for f in get_all_foods() if f.name == f_name), None)
                                    if not f_obj:
                                        f_obj = session.query(CustomFood).filter(
                                            CustomFood.name == f_name, 
                                            CustomFood.user_id == current_user.user_id
                                        ).first()
                                    
                                    if f_obj:
                                        if hasattr(f_obj, 'food_id'):
                                            cats = get_food_categories(f_obj.food_id)
                                            for c in cats: 
                                                if c.name in cat_name_map:
                                                    ingredient_categories.add(c.name)
                                        elif hasattr(f_obj, 'categories') and f_obj.categories:
                                            for c_name in f_obj.categories.split(','):
                                                if c_name.strip() in cat_name_map:
                                                    ingredient_categories.add(c_name.strip())
                                
                                combined_categories_str = ",".join(list(ingredient_categories)) if ingredient_categories else None

                                # 6. Создаем или обновляем запись в справочнике продуктов
                                if not existing_food:
                                    new_food = CustomFood(
                                        user_id=current_user.user_id,
                                        name=dish_name,
                                        calories_per_100g=(totals['calories'] / totals['weight'] * 100) if totals['weight'] > 0 else 0,
                                        protein_per_100g=(totals['protein'] / totals['weight'] * 100) if totals['weight'] > 0 else 0,
                                        fat_per_100g=(totals['fat'] / totals['weight'] * 100) if totals['weight'] > 0 else 0,
                                        carbs_per_100g=(totals['carbs'] / totals['weight'] * 100) if totals['weight'] > 0 else 0,
                                        is_basic=False, # Это готовое блюдо!
                                        is_complex_meal=True, 
                                        complex_meal_id=new_meal.meal_id,
                                        categories=combined_categories_str # НАСЛЕДУЕМ КАТЕГОРИИ!
                                    )
                                    session.add(new_food)
                                    session.flush()
                                    meal_food_id = new_food.custom_food_id
                                else:
                                    meal_food_id = existing_food.custom_food_id
                                
                                # 7. Создаем запись в дневнике питания
                                new_log = FoodLog(
                                    user_id=current_user.user_id,
                                    food_name=dish_name,
                                    date=meal_date,
                                    meal_type=meal_type,
                                    weight_eaten=totals['weight']
                                )
                                session.add(new_log)
                                
                                session.commit()
                                st.session_state.recipe_components = []
                                st.success(f"🎉 Блюдо '{dish_name}' сохранено и добавлено в дневник! Итого: {totals['calories']:.0f} ккал")
                                st.balloons()
                                st.rerun()
                else:
                    st.info("👆 Сначала добавь хотя бы один ингредиент в список выше, чтобы сохранить блюдо.")    
                st.markdown("---")
                
                # =========================================================================
                # ДНЕВНИК ЗА ВЫБРАННУЮ ДАТУ
                # =========================================================================
                st.markdown("---")
                st.subheader(f"📋 Дневник за {selected_date.strftime('%d.%m.%Y')}")
                
                day_logs = session.query(FoodLog).filter(
                    FoodLog.user_id == current_user.user_id,
                    FoodLog.date == selected_date
                ).order_by(FoodLog.id.desc()).all()
                
                # Собираем словарь продуктов для расчетов
                all_foods_dict = {}
                for f in get_all_foods():
                    all_foods_dict[f.name] = f
                for f in session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all():
                    all_foods_dict[f.name] = f
                
                if day_logs:
                    meals_grouped = {'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []}
                    for log in day_logs:
                        meals_grouped[log.meal_type].append(log)
                    
                    meal_names = {'breakfast': '🌅 Завтрак', 'lunch': '☀️ Обед', 'dinner': '🌙 Ужин', 'snack': '🍪 Перекусы'}
                    
                    for meal_type, logs in meals_grouped.items():
                        if logs:
                            st.markdown(f"### {meal_names[meal_type]}")
                            
                            for log in logs:
                                food_item = all_foods_dict.get(log.food_name)
                                macros = calculate_food_calories(food_item, log.weight_eaten) if food_item else {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
                                
                                col1, col2, col3 = st.columns([3, 2, 1])
                                with col1:
                                    st.write(f"**{log.food_name}** — {log.weight_eaten}г")
                                    st.caption(f"{macros['protein']:.1f}Б / {macros['fat']:.1f}Ж / {macros['carbs']:.1f}У")
                                    
                                    if isinstance(food_item, CustomFood) and food_item.is_complex_meal and food_item.complex_meal_id:
                                        complex_meal = session.query(ComplexMeal).filter(ComplexMeal.meal_id == food_item.complex_meal_id).first()
                                        if complex_meal:
                                            with st.expander("📝 Состав блюда"):
                                                for comp in complex_meal.components:
                                                    time_str = f", {int(comp.cooking_time)} мин" if comp.cooking_time else ""
                                                    st.write(f"• {comp.food_name}: {comp.weight}г ({comp.cooking_method}{time_str})")
                                
                                with col2:
                                    st.write(f"**{macros['calories']:.0f} ккал**")
                                with col3:
                                    if st.button("🗑️", key=f"del_food_{log.id}"):
                                        session.delete(log)
                                        session.commit()
                                        st.rerun()
                            st.markdown("")
                    
                    # Используем обновленную функцию с передачей словаря
                    totals = calculate_daily_totals(day_logs, all_foods_dict)
                    st.markdown("---")
                    st.subheader("📊 Итого за день")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: st.metric("🔥 Калории", f"{totals['calories']:.0f} ккал")
                    with col2: st.metric("🥩 Белки", f"{totals['protein']:.1f} г")
                    with col3: st.metric("🥑 Жиры", f"{totals['fat']:.1f} г")
                    with col4: st.metric("🍞 Углеводы", f"{totals['carbs']:.1f} г")
                else:
                    st.info(f"📭 Записей за {selected_date.strftime('%d.%m.%Y')} пока нет")
                pass

            with tab_reference:
                # =========================================================================
                # СТРАНИЦА "МОЯ ЕДА" (Умный справочник с поиском и фильтрацией)
                # =========================================================================
                st.header("🥗 Справочник моей еды")
                st.info("💡 Здесь отображаются все продукты. Ты можешь искать их по названию и удалять только те, что добавил сам.")
                
                # 1. Получаем все продукты
                base_foods = get_all_foods()
                custom_foods = session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all()
                all_foods = base_foods + custom_foods
                
                # 2. Вкладки
                tab1, tab2 = st.tabs(["🥬 Базовые продукты", "🍲 Готовые блюда"])
                
                # Универсальная функция для рендера содержимого вкладки
                def render_tab_content(is_basic_target):
                    # А. Фильтрация по типу (базовый/готовый)
                    filtered_foods = [f for f in all_foods if getattr(f, 'is_basic', True) == is_basic_target]
                    
                    # Б. Поисковая строка (уникальный ключ для каждой вкладки)
                    search_query = st.text_input(
                        "🔍 Поиск по названию:", 
                        key=f"search_{'basic' if is_basic_target else 'prepared'}",
                        placeholder="Введите название продукта..."
                    )
                    
                    if search_query:
                        filtered_foods = [f for f in filtered_foods if search_query.lower() in f.name.lower()]
                    
                    if not filtered_foods:
                        st.info(f"📭 В этой категории ничего не найдено.")
                        return
                    
                    import pandas as pd
                    
                    data_macros = []
                    data_micros = []
                    
                    for f in filtered_foods:
                        # Категории (только для base_foods)
                        categories = get_food_categories(f.food_id) if hasattr(f, 'food_id') else []
                        cat_display = get_display_categories(f)
                        is_custom_tag = " *(Твой)*" if hasattr(f, 'custom_food_id') else ""
                        
                        data_macros.append({
                            "Название": f"{f.name}{is_custom_tag}",
                            "Категории": cat_display,
                            "Ккал": f.calories_per_100g,
                            "Белки": f.protein_per_100g,
                            "Жиры": f.fat_per_100g,
                            "Углеводы": f.carbs_per_100g,
                            "ID": f.food_id if hasattr(f, 'food_id') else f.custom_food_id
                        })
                        
                        data_micros.append({
                            "Название": f"{f.name}{is_custom_tag}",
                            "Вит.А": f.vitamin_a or 0,
                            "Вит.C": f.vitamin_c or 0,
                            "Вит.D": f.vitamin_d or 0,
                            "Вит.E": f.vitamin_e or 0,
                            "Вит.K": f.vitamin_k or 0,
                            "Вит.B": f.vitamin_b_complex or 0,
                            "Железо": f.iron or 0,
                            "Кальций": f.calcium or 0,
                            "Магний": f.magnesium or 0,
                            "Цинк": f.zinc or 0,
                            "Йод": f.iodine or 0,
                            "Селен": f.selenium or 0,
                            "ID": f.food_id if hasattr(f, 'food_id') else f.custom_food_id
                        })
                    
                    df_macros = pd.DataFrame(data_macros)
                    df_micros = pd.DataFrame(data_micros)
                    
                    # В. Компактная таблица макронутриентов с форматированием
                    st.subheader("📊 Макронутриенты (на 100г)")
                    st.dataframe(
                        df_macros[["Название", "Категории", "Ккал", "Белки", "Жиры", "Углеводы"]], 
                        width='stretch', 
                        hide_index=True,
                        column_config={
                            "Ккал": st.column_config.NumberColumn(format="%.0f"),
                            "Белки": st.column_config.NumberColumn(format="%.1f г"),
                            "Жиры": st.column_config.NumberColumn(format="%.1f г"),
                            "Углеводы": st.column_config.NumberColumn(format="%.1f г"),
                        }
                    )
                    
                    # Г. Компактная таблица микронутриентов внутри expander
                    with st.expander("🧪 Показать микронутриенты", expanded=False):
                        st.dataframe(
                            df_micros.drop(columns=["ID"]), 
                            width='stretch', 
                            hide_index=True,
                            column_config={col: st.column_config.NumberColumn(format="%.1f") for col in df_micros.columns if col != "Название"}
                        )
                    
                    st.markdown("---")
                    st.subheader("🗑️ Управление справочником")
                    st.caption("Здесь можно удалить только *твои* добавленные продукты, отображаемые в этой вкладке.")
                    
                    # Д. Фильтруем только кастомные продукты из текущего отфильтрованного списка
                    custom_filtered = [f for f in filtered_foods if hasattr(f, 'custom_food_id')]
                    
                    if custom_filtered:
                        with st.form(f"delete_food_form_{'basic' if is_basic_target else 'prepared'}"):
                            food_names = [f.name for f in custom_filtered]
                            food_to_delete = st.selectbox("Выбери продукт для удаления:", food_names)
                            
                            col1, col2 = st.columns([1, 3])
                            with col1:
                                confirm_delete = st.form_submit_button("Удалить", type="primary")
                            
                            if confirm_delete:
                                food_obj = session.query(CustomFood).filter(
                                    CustomFood.name == food_to_delete, 
                                    CustomFood.user_id == current_user.user_id
                                ).first()
                                if food_obj:
                                    session.delete(food_obj)
                                    session.commit()
                                    st.success(f"✅ Продукт '{food_to_delete}' успешно удален!")
                                    st.rerun()
                    else:
                        st.info("📭 В этой категории нет твоих личных продуктов для удаления.")

                # 3. Рендерим содержимое вкладок
                with tab1:
                    render_tab_content(is_basic_target=True)
                
                with tab2:
                    render_tab_content(is_basic_target=False)              
                pass
                st.markdown("---")
                
        # ============================================================================
        # СТРАНИЦА ТРЕНИРОВОК (НОВАЯ ВЕРСИЯ - ОСТАВЬ ТОЛЬКО ЭТУ)
        # ============================================================================

        elif page == "🏋️ Тренировки":
            st.header("Дневник тренировок")
            
            user = session.query(User).first()
            if not user:
                st.error("Пользователь не найден!")
            else:
                # ====== 1. ВЫБОР ДАТЫ ======
                selected_date = st.date_input(
                    "📅 Выбери дату для просмотра или добавления:",
                    value=date.today(),
                    max_value=date.today()
                )
                st.markdown("---")
                
                # ====== 2. КОНСТРУКТОР ТРЕНИРОВКИ ======
                st.subheader("➕ Новая тренировка")
                
                col1, col2 = st.columns(2)
                with col1:
                    w_date = st.date_input("Дата:", value=selected_date, key="w_date_input")
                    w_duration = st.number_input("Длительность (мин):", min_value=1, value=60, step=5, key="w_dur")
                with col2:
                    w_intensity = st.selectbox("Общая интенсивность:", ["Легкая", "Средняя", "Тяжелая", "Максимальная"], key="w_int")
                
                st.markdown("---")
                st.markdown("##### Добавить упражнение")
                
                if 'temp_exercises' not in st.session_state:
                    st.session_state.temp_exercises = []
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    exercises = session.query(Exercise).all()
                    ex_options = {e.name: e for e in exercises}
                    ex_choice = st.selectbox(
                        "Упражнение:", 
                        options=["🔍 Другое (добавить свое)"] + list(ex_options.keys()),
                        key="ex_choice_select"
                    )
                    
                    if ex_choice == "🔍 Другое (добавить свое)":
                        new_ex_name = st.text_input("Название упражнения:", key="new_ex_name")
                        new_ex_type = st.selectbox("Тип:", ["strength", "cardio", "flexibility"], key="new_ex_type")
                        new_ex_muscles = st.text_input("Целевые мышцы (через запятую):", key="new_ex_muscles")
                
                with col_b:
                    ex_sets = st.number_input("Подходы:", min_value=1, value=3, key="ex_sets")
                    ex_reps = st.number_input("Повторения:", min_value=1, value=10, key="ex_reps")
                with col_c:
                    ex_weight = st.number_input("Вес (кг):", min_value=0.0, value=20.0, step=2.5, key="ex_weight")
                
                if st.button("➕ Добавить упражнение в тренировку", width="stretch"):
                    if ex_choice == "🔍 Другое (добавить свое)":
                        if not new_ex_name:
                            st.error("❌ Введите название упражнения!")
                        else:
                            existing_ex = session.query(Exercise).filter(Exercise.name.ilike(new_ex_name)).first()
                            if existing_ex:
                                ex_obj = existing_ex
                                st.info(f"ℹ️ Упражнение '{new_ex_name}' уже есть в справочнике")
                            else:
                                ex_obj = Exercise(
                                    name=new_ex_name, 
                                    exercise_type=new_ex_type, 
                                    target_muscles=new_ex_muscles
                                )
                                session.add(ex_obj)
                                session.flush()
                    else:
                        ex_obj = ex_options[ex_choice]
                    
                    st.session_state.temp_exercises.append({
                        'exercise_id': ex_obj.exercise_id,
                        'exercise_name': ex_obj.name,
                        'sets': ex_sets,
                        'reps': ex_reps,
                        'weight': ex_weight
                    })
                    st.success(f"✅ {ex_obj.name} добавлен в список!")
                    st.rerun()
                
                # ====== 3. ОТОБРАЖЕНИЕ ТЕКУЩЕЙ ТРЕНИРОВКИ ======
                if st.session_state.temp_exercises:
                    st.markdown("###### 📋 Текущая тренировка:")
                    for idx, temp_ex in enumerate(st.session_state.temp_exercises):
                        col_d1, col_d2, col_d3 = st.columns([3, 2, 1])
                        with col_d1:
                            st.write(f"**{temp_ex['exercise_name']}**")
                        with col_d2:
                            st.write(f"{temp_ex['sets']} × {temp_ex['reps']} @ {temp_ex['weight']} кг")
                        with col_d3:
                            if st.button("🗑️", key=f"remove_temp_{idx}"):
                                st.session_state.temp_exercises.pop(idx)
                                st.rerun()
                    
                    st.markdown("")
                    if st.button("💾 Сохранить тренировку целиком", type="primary", width="stretch"):
                        new_workout = Workout(
                            user_id=current_user.user_id,
                            date=w_date,
                            duration_minutes=w_duration
                        )
                        session.add(new_workout)
                        session.flush()
                        
                        for temp_ex in st.session_state.temp_exercises:
                            new_log = WorkoutLog(
                                workout_id=new_workout.workout_id,
                                exercise_id=temp_ex['exercise_id'],
                                sets=temp_ex['sets'],
                                reps=temp_ex['reps'],
                                weight=temp_ex['weight'],
                                intensity=w_intensity
                            )
                            session.add(new_log)
                        
                        session.commit()
                        st.session_state.temp_exercises = [] 
                        st.success("🎉 Тренировка успешно сохранена!")
                        st.balloons()
                        st.rerun()
                
                st.markdown("---")
                
                # ====== 4. ПРОСМОТР ТРЕНИРОВОК ЗА ВЫБРАННУЮ ДАТУ ======
                st.subheader(f"📋 Тренировки за {selected_date.strftime('%d.%m.%Y')}")
                
                day_workouts = session.query(Workout).filter(
                    Workout.user_id == current_user.user_id,
                    Workout.date == selected_date
                ).order_by(Workout.workout_id.desc()).all()
                
                if day_workouts:
                    for workout in day_workouts:
                        volume = calculate_workout_volume(workout.logs)
                        intensity_display = workout.logs[0].intensity if workout.logs else "N/A"
                        
                        with st.expander(f"🏋️ {workout.duration_minutes} мин | Интенсивность: {intensity_display} | Объем: {volume:.1f} кг"):
                            for log in workout.logs:
                                st.write(f"- **{log.exercise.name}**: {log.sets}×{log.reps} @ {log.weight} кг")
                            
                            st.markdown("")
                            if st.button("️ Удалить тренировку", key=f"del_w_{workout.workout_id}"):
                                session.delete(workout)
                                session.commit()
                                st.rerun()
                else:
                    st.info(f"📭 Тренировок за {selected_date.strftime('%d.%m.%Y')} не найдено")

        # =========================================================================
        # СТРАНИЦА "МОЙ КАЛЕНДАРЬ" (Адаптивная неделя)
        # =========================================================================
        elif page == "📅 Мой календарь":
            st.header("📅 Мой календарь питания")
            st.caption("План на текущую неделю. Рацион сохраняется и не меняется при переключении вкладок.")
            
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
            day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
            
            col_widths = [3 if i == today.weekday() else 1 for i in range(7)]
            cols = st.columns(col_widths)
            
            # Вспомогательная функция для отображения плана
            def display_plan(plan_data, is_today_day):
                meal_icons = {'breakfast': '🌅', 'lunch': '☀️', 'dinner': '🌙'}
                meal_names_ru = {'breakfast': 'Завтрак', 'lunch': 'Обед', 'dinner': 'Ужин'}
                
                for m_type in ['breakfast', 'lunch', 'dinner']:
                    st.markdown(f"##### {meal_icons[m_type]} {meal_names_ru[m_type]}")
                    components = plan_data.get(m_type, [])
                    
                    if components:
                        # Для сегодняшнего дня раскрываем по умолчанию, для прошлых - свернуто
                        with st.expander(f"Состав", expanded=is_today_day):
                            for comp in components:
                                time_str = f", {comp.get('time', 0)} мин" if comp.get('time', 0) > 0 else ""
                                st.write(f"• **{comp['name']}**: {comp['weight']}г ({comp['method']}{time_str})")
                    else:
                        st.caption("Нет вариантов")
                    st.markdown("")

            for i, (col, d_date, d_name) in enumerate(zip(cols, week_dates, day_names)):
                with col:
                    is_today = (i == today.weekday())
                    
                    with st.container(border=is_today):
                        if is_today:
                            st.subheader(f"📅 {d_name}, {d_date.strftime('%d.%m')}")
                            st.markdown("📍 **Сегодня**")
                        else:
                            st.markdown(f"**{d_name}**")
                            st.markdown(f"{d_date.strftime('%d.%m')}")
                        
                        st.divider()
                        
                        # 1. Проверяем, есть ли уже сохраненный план на эту дату
                        existing_plan = session.query(GeneratedPlan).filter(
                            GeneratedPlan.user_id == current_user.user_id,
                            GeneratedPlan.date == d_date
                        ).first()
                        
                        if existing_plan:
                            st.success("✅ Рацион сохранен")
                            if st.button("🔄 Сгенерировать заново", key=f"regen_{d_date}", use_container_width=True):
                                session.delete(existing_plan)
                                session.commit()
                                st.rerun()
                            
                            # Загружаем и отображаем
                            plan_data = {
                                'breakfast': json.loads(existing_plan.breakfast_json) if existing_plan.breakfast_json else [],
                                'lunch': json.loads(existing_plan.lunch_json) if existing_plan.lunch_json else [],
                                'dinner': json.loads(existing_plan.dinner_json) if existing_plan.dinner_json else []
                            }
                            display_plan(plan_data, is_today)
                            
                        else:
                            st.info("📝 Рацион еще не составлен")
                            if st.button("✨ Сгенерировать рацион", key=f"gen_{d_date}", use_container_width=True, type="primary"):
                                with st.spinner("Подбираем лучшие блюда с учетом ваших целей и аллергий..."):
                                    user_goal = session.query(UserGoal).filter(UserGoal.user_id == current_user.user_id).first()
                                    
                                    user_allergies_objs = session.query(UserAllergy).filter(UserAllergy.user_id == current_user.user_id).all()
                                    user_allergen_names = []
                                    for ua in user_allergies_objs:
                                        allergen = session.query(Allergen).filter(Allergen.allergen_id == ua.allergen_id).first()
                                        if allergen:
                                            user_allergen_names.append(allergen.name)
                                    
                                    new_plan = generate_daily_plan(
                                        user_goal.target_calories if user_goal else 2000,
                                        user_goal.target_protein if user_goal else 150,
                                        user_goal.target_fat if user_goal else 70,
                                        user_goal.target_carbs if user_goal else 250,
                                        user_allergen_names,
                                        get_all_foods(),
                                        session.query(CustomFood).filter(CustomFood.user_id == current_user.user_id).all()
                                    )
                                    
                                    if 'error' in new_plan:
                                        st.error(new_plan['error'])
                                    else:
                                        # Сохраняем в базу!
                                        new_record = GeneratedPlan(
                                            user_id=current_user.user_id,
                                            date=d_date,
                                            breakfast_json=json.dumps(new_plan.get('breakfast', [])),
                                            lunch_json=json.dumps(new_plan.get('lunch', [])),
                                            dinner_json=json.dumps(new_plan.get('dinner', []))
                                        )
                                        session.add(new_record)
                                        session.commit()
                                        st.rerun()
                        
        # Закрываем сессию
    session.close()