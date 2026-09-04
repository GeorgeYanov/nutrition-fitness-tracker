"""
Главный файл приложения - интерфейс на Streamlit с авторизацией
"""
import streamlit as st
from datetime import date
import pandas as pd
from database import get_session, User, Food, Exercise, FoodLog, Workout, WorkoutLog, UserMeasurement
from calculations import calculate_food_calories, calculate_daily_totals, calculate_workout_volume, calculate_age, calculate_bmr, calculate_tdee
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
            submit = st.form_submit_button("Войти", use_container_width=True)
            
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
            reg_submit = st.form_submit_button("Зарегистрироваться", use_container_width=True)
            
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
            page = st.radio("Навигация", ["🏠 Главная", "👤 Профиль", "🍎 Питание", "🏋️ Тренировки", "📊 Прогресс"])
            st.markdown("---")
            if st.button("🚪 Выйти из аккаунта", use_container_width=True):
                logout()

        # =========================================================================
        # ГЛАВНАЯ СТРАНИЦА
        # =========================================================================
        if page == "🏠 Главная":
            st.header(f"Добро пожаловать, {current_user.full_name.split()[0]}! 👋")
            
            latest_measurement = current_user.measurements[-1] if current_user.measurements else None
            
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
            today_logs = session.query(FoodLog).filter(FoodLog.user_id == current_current_user.user_id, FoodLog.date == today).all()
            
            if today_logs:
                totals = calculate_daily_totals(today_logs)
                if 'tdee' in locals():
                    st.progress(min(totals['calories'] / tdee, 1.5), text=f"Съедено {totals['calories']:.0f} из {tdee:.0f} ккал")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🔥 Калории", f"{totals['calories']:.0f}")
                c2.metric("🥩 Белки", f"{totals['protein']:.1f} г")
                c3.metric("🥑 Жиры", f"{totals['fat']:.1f} г")
                c4.metric("🍞 Углеводы", f"{totals['carbs']:.1f} г")
            else:
                st.info("📭 Пока нет записей за сегодня.")

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
                
                submit_profile = st.form_submit_button("💾 Сохранить личные данные", use_container_width=True)
                
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
                
                submit_meas = st.form_submit_button("➕ Добавить замер", type="primary", use_container_width=True)
                
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
                        "Жир (%)": m.fat_percent or "-",
                        "Мышцы (кг)": m.muscle_mass or "-"
                    })
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("📭 Замеров пока нет. Добавьте первый замер выше!")

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
                
                with st.form("add_food_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        foods = session.query(Food).all()
                        food_options = {f.name: f for f in foods}
                        
                        food_choice = st.selectbox(
                            "Выбери продукт:",
                            options=["🔍 Другое (добавить свой)"] + list(food_options.keys())
                        )
                        
                        if food_choice == "🔍 Другое (добавить свой)":
                            new_food_name = st.text_input("Название нового продукта:")
                            col_cal, col_p, col_f, col_c = st.columns(4)
                            with col_cal:
                                new_cal = st.number_input("Ккал/100г", min_value=0.0, value=100.0, step=1.0)
                            with col_p:
                                new_prot = st.number_input("Белки/100г", min_value=0.0, value=0.0, step=0.1)
                            with col_f:
                                new_fat = st.number_input("Жиры/100г", min_value=0.0, value=0.0, step=0.1)
                            with col_c:
                                new_carb = st.number_input("Углеводы/100г", min_value=0.0, value=0.0, step=0.1)
                        
                        weight = st.number_input(
                            "Сколько грамм съел?",
                            min_value=1,
                            max_value=5000,
                            value=100,
                            step=10
                        )
                    
                    with col2:
                        meal_date = st.date_input("Дата приема:", value=selected_date)
                        
                        meal_type = st.selectbox(
                            "Тип приема пищи:",
                            ["breakfast", "lunch", "dinner", "snack"],
                            format_func=lambda x: {
                                "breakfast": "🌅 Завтрак",
                                "lunch": "️ Обед",
                                "dinner": "🌙 Ужин",
                                "snack": "🍪 Перекус"
                            }[x]
                        )
                    
                    submitted = st.form_submit_button("✅ Добавить")
                    
                    if submitted:
                        if food_choice == "🔍 Другое (добавить свой)":
                            if not new_food_name:
                                st.error("❌ Введи название продукта!")
                            else:
                                existing = session.query(Food).filter(Food.name == new_food_name).first()
                                if existing:
                                    selected_food = existing
                                    st.info(f"ℹ️ Продукт '{new_food_name}' уже есть в справочнике")
                                else:
                                    selected_food = Food(
                                        name=new_food_name,
                                        calories_per_100g=new_cal,
                                        protein_per_100g=new_prot,
                                        fat_per_100g=new_fat,
                                        carbs_per_100g=new_carb
                                    )
                                    session.add(selected_food)
                                    session.flush()
                                    st.success(f"✅ Продукт '{new_food_name}' добавлен в справочник!")
                        else:
                            selected_food = food_options[food_choice]
                        
                        if food_choice != "🔍 Другое (добавить свой)" or new_food_name:
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