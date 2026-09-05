"""
Главный файл приложения - интерфейс на Streamlit с авторизацией
"""
import streamlit as st
from datetime import date
import pandas as pd
from database import get_session, User, Food, Exercise, FoodLog, Workout, WorkoutLog, UserMeasurement, UserGoal, MedicalResult, ComplexMeal, ComplexMealComponent
from calculations import calculate_food_calories, calculate_daily_totals, calculate_workout_volume, calculate_age, calculate_bmr, calculate_tdee, calculate_macro_goals, calculate_complex_meal_totals
from auth import register_user, authenticate_user

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
            page = st.radio("Навигация", ["🏠 Главная", "👤 Профиль", "🥗 Моя еда", "🍎 Питание", "🏋️ Тренировки", "🩺 Анализы", "📊 Прогресс"])
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
            
            if today_logs:
                totals = calculate_daily_totals(today_logs)
                goals = session.query(UserGoal).filter(UserGoal.user_id == current_user.user_id).first()
                
                st.markdown("#### 📊 Прогресс за сегодня")
                
                # Вспомогательная функция для красивого прогресс-бара
                def render_progress(current, target, label, unit, color="#1f77b4"):
                    if target and target > 0:
                        pct = min(current / target, 1.5) # Ограничиваем 150%, чтобы бар не ломался при переедании
                        st.progress(pct, text=f"**{label}**: {current:.1f} / {target:.1f} {unit} ({(current/target)*100:.0f}%)")
                    else:
                        st.write(f"**{label}**: {current:.1f} {unit} *(Цель не задана в Профиле)*")
                
                # Получаем цели или дефолтные значения
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

        # =========================================================================
        # СТРАНИЦА ПРОФИЛЯ (Личные данные и замеры)
        # =========================================================================
        elif page == "👤 Профиль":
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
                # =========================================================================
        # СТРАНИЦА "МОЯ ЕДА" (Управление справочником)
        # =========================================================================
        elif page == "🥗 Моя еда":
            st.header("🥗 Справочник моей еды")
            st.info("💡 Здесь отображаются все продукты, которые ты добавил вручную через вкладку 'Питание'. Они сохраняются навсегда и доступны для быстрого выбора.")
            
            # Получаем все продукты из базы
            foods = session.query(Food).order_by(Food.name).all()
            
            if foods:
                import pandas as pd
                
                # Формируем данные для красивой таблицы
                data = []
                for f in foods:
                    data.append({
                        "Название": f.name,
                        "Ккал": f.calories_per_100g,
                        "Белки": f.protein_per_100g,
                        "Жиры": f.fat_per_100g,
                        "Углеводы": f.carbs_per_100g,
                        "ID": f.food_id # Скрытый ID для удаления
                    })
                
                df = pd.DataFrame(data)
                
                # Показываем таблицу (скрываем колонку ID)
                st.dataframe(
                    df[["Название", "Ккал", "Белки", "Жиры", "Углеводы"]], 
                    use_container_width=True, 
                    hide_index=True
                )
                
                st.markdown("---")
                st.subheader("🗑️ Управление справочником")
                
                with st.form("delete_food_form"):
                    st.caption("Выбери продукт, который был добавлен с ошибкой, чтобы удалить его из справочника.")
                    food_names = [f.name for f in foods]
                    food_to_delete = st.selectbox("Продукт для удаления:", food_names)
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        confirm_delete = st.form_submit_button("Удалить", type="primary")
                    
                    if confirm_delete:
                        # Находим продукт и удаляем
                        food_obj = session.query(Food).filter(Food.name == food_to_delete).first()
                        if food_obj:
                            session.delete(food_obj)
                            session.commit()
                            st.success(f"✅ Продукт '{food_to_delete}' успешно удален из справочника!")
                            st.rerun() # Перезагружаем страницу, чтобы обновить список
            
            else:
                st.info("📭 Твой личный справочник пока пуст. Добавь свой первый кастомный продукт во вкладке '🍎 Питание' -> '🔍 Другое (добавить свой)'!") 
                        
        # ============================================================================
        # СТРАНИЦА ПИТАНИЯ (НОВАЯ ВЕРСИЯ - ОСТАВЬ ТОЛЬКО ЭТУ)
        # ============================================================================

        elif page == "🍎 Питание":
            st.header("Дневник питания")
            
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
                
                st.markdown("---")
                
                # ====== ФОРМА ДОБАВЛЕНИЯ ЕДЫ ======
                st.subheader("➕ Добавить прием пищи")
                
                # =========================================================================
                # 1. СЕЛЕКТОР ПРОДУКТА (СНАРУЖИ ФОРМЫ - для мгновенного обновления UI)
                # =========================================================================
                foods = session.query(Food).order_by(Food.name).all()
                food_options = {f.name: f for f in foods}
                
                food_choice = st.selectbox(
                    "Выбери продукт:",
                    options=["🔍 Другое (добавить свой)"] + list(food_options.keys()),
                    key="simple_food_choice_selector" # Уникальный ключ с префиксом
                )

                # =========================================================================
                # 2. ОСНОВНАЯ ФОРМА (ВНУТРИ - для группировки отправки)
                # =========================================================================
                with st.form("add_food_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if food_choice != "🔍 Другое (добавить свой)":
                            selected_preview = food_options[food_choice]
                            st.info(
                                f"📊 **КБЖУ на 100г:** {selected_preview.calories_per_100g} ккал | "
                                f"Б: {selected_preview.protein_per_100g}г | "
                                f"Ж: {selected_preview.fat_per_100g}г | "
                                f"У: {selected_preview.carbs_per_100g}г"
                            )
                        else:
                            st.markdown("###### 🆕 Параметры нового продукта")
                            # Все ключи теперь имеют префикс simple_ для уникальности
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
                            
                            # Микронутриенты в раскрывающемся списке
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
                    
                    submitted = st.form_submit_button("✅ Добавить", type="primary", use_container_width=True)
                    
                    if submitted:
                        if food_choice == "🔍 Другое (добавить свой)":
                            if not new_food_name:
                                st.error("❌ Введи название продукта!")
                                st.stop()
                            
                            existing = session.query(Food).filter(Food.name.ilike(new_food_name)).first()
                            if existing:
                                selected_food = existing
                                st.info(f"ℹ️ Продукт '{new_food_name}' уже есть в справочнике, используем его")
                            else:
                                selected_food = Food(
                                    name=new_food_name,
                                    calories_per_100g=new_cal,
                                    protein_per_100g=new_prot,
                                    fat_per_100g=new_fat,
                                    carbs_per_100g=new_carb,
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
                                session.flush()
                                st.success(f"✅ Продукт '{new_food_name}' добавлен в справочник!")
                        else:
                            selected_food = food_options[food_choice]
                        
                        new_log = FoodLog(
                            user_id=current_user.user_id,
                            food_id=selected_food.food_id,
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
                st.caption("Идеально для домашних блюд. Добавляй ингредиенты по одному, указывай вес и способ приготовления, а затем сохрани всё блюдо целиком.")
                
                # Инициализация списка компонентов в session_state
                if 'recipe_components' not in st.session_state:
                    st.session_state.recipe_components = []
                    
                # =========================================================================
                # ЧАСТЬ 1: ДИНАМИЧЕСКИЙ СПИСОК И ДОБАВЛЕНИЕ (СНАРУЖИ ФОРМЫ)
                # =========================================================================
                
                # Отображение уже добавленных компонентов
                if st.session_state.recipe_components:
                    st.markdown("##### 📋 Текущие ингредиенты:")
                    for idx, comp in enumerate(st.session_state.recipe_components):
                        col_a, col_b, col_c, col_d = st.columns([3, 1, 2, 1])
                        with col_a:
                            st.write(f"**{comp['food_name']}**")
                        with col_b:
                            st.write(f"{comp['weight']} г")
                        with col_c:
                            st.caption(f"Приготовление: {comp['method']}")
                        with col_d:
                            # Кнопка удаления (разрешена снаружи формы)
                            if st.button("❌", key=f"remove_comp_{idx}"):
                                st.session_state.recipe_components.pop(idx)
                                st.rerun()
                    st.markdown("---")
                
                st.markdown("##### ➕ Добавить новый ингредиент")
                col_add1, col_add2, col_add3 = st.columns([3, 1, 2])
                with col_add1:
                    foods = session.query(Food).order_by(Food.name).all()
                    food_options = {f.name: f for f in foods}
                    new_comp_food = st.selectbox("Продукт из справочника:", list(food_options.keys()), key="new_comp_food_select")
                with col_add2:
                    new_comp_weight = st.number_input("Вес (г)", min_value=1, value=100, step=10, key="new_comp_weight")
                with col_add3:
                    new_comp_method = st.text_input("Способ приготовления", value="Без обработки", key="new_comp_method", help="Например: 'Варка 10 мин, затем обжарка'")
                
                # Кнопка добавления в список (СНАРУЖИ формы, поэтому st.button разрешен!)
                if st.button("Добавить ингредиент в список", use_container_width=True):
                    selected_food = food_options[new_comp_food]
                    st.session_state.recipe_components.append({
                        'food_id': selected_food.food_id,
                        'food_name': selected_food.name,
                        'weight': new_comp_weight,
                        'method': new_comp_method
                    })
                    st.success(f"✅ {selected_food.name} добавлен!")
                    st.rerun() # Мгновенно обновляем список выше

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
                            meal_type = st.selectbox("Прием пищи:", ["breakfast", "lunch", "dinner", "snack"], format_func=lambda x: {"breakfast": "🌅 Завтрак", "lunch": "☀️ Обед", "dinner": "🌙 Ужин", "snack": "🍪 Перекус"}[x])
                        
                        meal_date = st.date_input("Дата приготовления:", value=date.today())
                        
                        st.info(f"В блюдо будет добавлено ингредиентов: **{len(st.session_state.recipe_components)}**")
                        
                        # ЕДИНСТВЕННАЯ кнопка внутри формы
                        submit_dish = st.form_submit_button("💾 Сохранить сложное блюдо в дневник", type="primary", use_container_width=True)
                        
                        if submit_dish:
                            if not dish_name:
                                st.error("❌ Введи название блюда!")
                            else:
                                # 1. Собираем все продукты в словарь для быстрого доступа
                                foods_dict = {f.food_id: f for f in session.query(Food).all()}
                                
                                # 2. Считаем итоги через нашу функцию
                                totals = calculate_complex_meal_totals(st.session_state.recipe_components, foods_dict)
                                
                                # 3. Создаем запись ComplexMeal
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
                                session.flush() # Получаем meal_id
                                
                                # 4. Создаем записи компонентов
                                for comp in st.session_state.recipe_components:
                                    new_comp = ComplexMealComponent(
                                        meal_id=new_meal.meal_id,
                                        food_id=comp['food_id'],
                                        weight=comp['weight'],
                                        cooking_method=comp['method']
                                    )
                                    session.add(new_comp)
                                
                                session.commit()
                                
                                # 5. Очищаем session_state и радуемся
                                st.session_state.recipe_components = []
                                st.success(f"🎉 Блюдо '{dish_name}' сохранено! Итого: {totals['calories']:.0f} ккал, Б:{totals['protein']:.1f} Ж:{totals['fat']:.1f} У:{totals['carbs']:.1f}")
                                st.balloons()
                                st.rerun()
                else:
                    st.info("👆 Сначала добавь хотя бы один ингредиент в список выше, чтобы сохранить блюдо.")    
                st.markdown("---")
                
                # ====== ДНЕВНИК ЗА ВЫБРАННУЮ ДАТУ ======
                st.subheader(f"📋 Дневник за {selected_date.strftime('%d.%m.%Y')}")
                
                day_logs = session.query(FoodLog).filter(
                    FoodLog.user_id == current_user.user_id,
                    FoodLog.date == selected_date
                ).order_by(FoodLog.id.desc()).all()
                
                if day_logs:
                    meals_grouped = {
                        'breakfast': [], 'lunch': [], 'dinner': [], 'snack': []
                    }
                    for log in day_logs:
                        meals_grouped[log.meal_type].append(log)
                    
                    meal_names = {
                        'breakfast': '🌅 Завтрак',
                        'lunch': '☀️ Обед',
                        'dinner': '🌙 Ужин',
                        'snack': '🍪 Перекусы'
                    }
                    
                    for meal_type, logs in meals_grouped.items():
                        if logs:
                            st.markdown(f"### {meal_names[meal_type]}")
                            
                            for log in logs:
                                macros = calculate_food_calories(log.food, log.weight_eaten)
                                
                                col1, col2, col3 = st.columns([3, 2, 1])
                                
                                with col1:
                                    st.write(f"**{log.food.name}** — {log.weight_eaten}г")
                                    st.caption(f"{macros['protein']:.1f}Б / {macros['fat']:.1f}Ж / {macros['carbs']:.1f}У")
                                
                                with col2:
                                    st.write(f"**{macros['calories']:.0f} ккал**")
                                
                                with col3:
                                    if st.button("🗑️", key=f"del_food_{log.id}"):
                                        session.delete(log)
                                        session.commit()
                                        st.rerun()
                            
                            st.markdown("")
                    
                    totals = calculate_daily_totals(day_logs)
                    st.markdown("---")
                    st.subheader("📊 Итого за день")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(" Калории", f"{totals['calories']:.0f} ккал")
                    with col2:
                        st.metric("🥩 Белки", f"{totals['protein']:.1f} г")
                    with col3:
                        st.metric("🥑 Жиры", f"{totals['fat']:.1f} г")
                    with col4:
                        st.metric("🍞 Углеводы", f"{totals['carbs']:.1f} г")
                else:
                    st.info(f"📭 Записей за {selected_date.strftime('%d.%m.%Y')} пока нет")

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
        # СТРАНИЦА МЕДИЦИНСКИХ АНАЛИЗОВ
        # =========================================================================
        elif page == "🩺 Анализы":
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
                    
                    submit_med = st.form_submit_button("💾 Сохранить результаты анализов", type="primary", use_container_width=True)
                    
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
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Таблица с историей
                            import pandas as pd
                            df_hist = pd.DataFrame([{
                                "Дата": h.test_date.strftime("%d.%m.%Y"),
                                "Значение": h.value,
                                "Ед. изм.": h.unit or "-"
                            } for h in history])
                            
                            st.markdown("##### 📜 История значений:")
                            st.dataframe(df_hist, use_container_width=True, hide_index=True)
                        else:
                            st.info("Недостаточно данных для построения графика.")
                else:
                    st.info("📭 Вы еще не внесли ни одного результата анализов. Перейдите во вкладку 'Внести результаты'.")
        # ============================================================================
        # СТРАНИЦА ПРОГРЕССА
        # ============================================================================
        elif page == "📊 Прогресс":
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
                        totals = calculate_daily_totals(day_logs)
                        
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
                        
                        calories_by_date = defaultdict(float)
                        for log in all_food_logs:
                            macros = calculate_food_calories(log.food, log.weight_eaten)
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
        # Закрываем сессию
    session.close()