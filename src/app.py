"""
Главный файл приложения - интерфейс на Streamlit
"""
import streamlit as st
from datetime import date, datetime
from database import get_session, User, Food, Exercise, FoodLog, Workout, WorkoutLog
from calculations import calculate_food_calories, calculate_daily_totals, calculate_workout_volume

# Настройка страницы
st.set_page_config(
    page_title="Fitness Tracker",
    page_icon="🏋️",
    layout="wide"
)

# Заголовок
st.title("🏋️ Трекер питания и тренировок")

# Получаем сессию БД
session = get_session()

# ============================================================================
# БОКОВАЯ ПАНЕЛЬ НАВИГАЦИИ
# ============================================================================

st.sidebar.title("Навигация")
page = st.sidebar.radio(
    "Выбери раздел:",
    ["🏠 Главная", "🍎 Питание", "🏋️ Тренировки", "📊 Прогресс"]
)

# ============================================================================
# ГЛАВНАЯ СТРАНИЦА
# ============================================================================

if page == "🏠 Главная":
    st.header("Добро пожаловать!")
    
    # Получаем первого пользователя (для MVP)
    user = session.query(User).first()
    
    if user:
        st.success(f"Привет, {user.tag}! 👋")
        
        # Показываем последние замеры
        latest_measurement = session.query(User).first().measurements[-1] if user.measurements else None
        
        if latest_measurement:
            st.subheader("📊 Последние замеры")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Вес", f"{latest_measurement.weight} кг")
            with col2:
                st.metric("Процент жира", f"{latest_measurement.fat_percent}%" if latest_measurement.fat_percent else "N/A")
            with col3:
                st.metric("Мышечная масса", f"{latest_measurement.muscle_mass} кг" if latest_measurement.muscle_mass else "N/A")
        
        # Показываем статистику за сегодня
        st.subheader("📈 Статистика за сегодня")
        
        today = date.today()
        today_food_logs = session.query(FoodLog).filter(
            FoodLog.user_id == user.user_id,
            FoodLog.date == today
        ).all()
        
        if today_food_logs:
            totals = calculate_daily_totals(today_food_logs)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Калории", f"{totals['calories']:.0f} ккал")
            with col2:
                st.metric("Белки", f"{totals['protein']:.1f} г")
            with col3:
                st.metric("Жиры", f"{totals['fat']:.1f} г")
            with col4:
                st.metric("Углеводы", f"{totals['carbs']:.1f} г")
        else:
            st.info("Пока нет записей о питании за сегодня")
    
    else:
        st.warning("Пользователь не найден. Запусти add_test_data.py для создания тестового пользователя.")

# ============================================================================
# СТРАНИЦА ПИТАНИЯ
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
                # Выбор продукта + опция "Другое"
                foods = session.query(Food).all()
                food_options = {f.name: f for f in foods}
                
                food_choice = st.selectbox(
                    "Выбери продукт:",
                    options=["🔍 Другое (добавить свой)"] + list(food_options.keys())
                )
                
                # Если выбрано "Другое" - показываем поля для нового продукта
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
                
                # Количество
                weight = st.number_input(
                    "Сколько грамм съел?",
                    min_value=1,
                    max_value=5000,
                    value=100,
                    step=10
                )
            
            with col2:
                # Дата приема пищи (по умолчанию = выбранная дата)
                meal_date = st.date_input("Дата приема:", value=selected_date)
                
                # Тип приема пищи
                meal_type = st.selectbox(
                    "Тип приема пищи:",
                    ["breakfast", "lunch", "dinner", "snack"],
                    format_func=lambda x: {
                        "breakfast": "🌅 Завтрак",
                        "lunch": "☀️ Обед",
                        "dinner": "🌙 Ужин",
                        "snack": "🍪 Перекус"
                    }[x]
                )
            
            submitted = st.form_submit_button("✅ Добавить")
            
            if submitted:
                # Обработка нового продукта
                if food_choice == "🔍 Другое (добавить свой)":
                    if not new_food_name:
                        st.error("❌ Введи название продукта!")
                    else:
                        # Проверяем, нет ли уже такого продукта
                        existing = session.query(Food).filter(Food.name == new_food_name).first()
                        if existing:
                            selected_food = existing
                            st.info(f"ℹ️ Продукт '{new_food_name}' уже есть в справочнике")
                        else:
                            # Создаем новый продукт
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
                
                # Создаем запись в дневнике (только если продукт выбран)
                if food_choice != "🔍 Другое (добавить свой)" or new_food_name:
                    new_log = FoodLog(
                        user_id=user.user_id,
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
            FoodLog.user_id == user.user_id,
            FoodLog.date == selected_date
        ).order_by(FoodLog.id.desc()).all()
        
        if day_logs:
            # Группируем по типу приема пищи
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
                            # Кнопка удаления
                            if st.button("🗑️", key=f"del_food_{log.id}"):
                                session.delete(log)
                                session.commit()
                                st.rerun()  # Перезагружаем страницу
                    
                    st.markdown("")  # Отступ
            
            # Общие итоги за день
            totals = calculate_daily_totals(day_logs)
            st.markdown("---")
            st.subheader("📊 Итого за день")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🔥 Калории", f"{totals['calories']:.0f} ккал")
            with col2:
                st.metric("🥩 Белки", f"{totals['protein']:.1f} г")
            with col3:
                st.metric("🥑 Жиры", f"{totals['fat']:.1f} г")
            with col4:
                st.metric("🍞 Углеводы", f"{totals['carbs']:.1f} г")
        else:
            st.info(f"📭 Записей за {selected_date.strftime('%d.%m.%Y')} пока нет")
    st.header("Дневник питания")
    
    user = session.query(User).first()
    
    if not user:
        st.error("Пользователь не найден!")
    else:
        # Форма добавления еды
        st.subheader("➕ Добавить прием пищи")
        
        with st.form("add_food_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Выбор продукта
                foods = session.query(Food).all()
                food_options = {f.name: f for f in foods}
                selected_food_name = st.selectbox(
                    "Выбери продукт:",
                    options=list(food_options.keys())
                )
                
                # Количество
                weight = st.number_input(
                    "Сколько грамм съел?",
                    min_value=1,
                    max_value=5000,
                    value=100,
                    step=10
                )
            
            with col2:
                # Дата
                meal_date = st.date_input("Дата:", value=date.today())
                
                # Тип приема пищи
                meal_type = st.selectbox(
                    "Тип приема пищи:",
                    ["breakfast", "lunch", "dinner", "snack"],
                    format_func=lambda x: {
                        "breakfast": "🌅 Завтрак",
                        "lunch": "☀️ Обед",
                        "dinner": "🌙 Ужин",
                        "snack": "🍪 Перекус"
                    }[x]
                )
            
            submitted = st.form_submit_button("✅ Добавить")
            
            if submitted and selected_food_name:
                selected_food = food_options[selected_food_name]
                
                # Создаем запись в дневнике
                new_log = FoodLog(
                    user_id=user.user_id,
                    food_id=selected_food.food_id,
                    date=meal_date,
                    meal_type=meal_type,
                    weight_eaten=weight
                )
                
                session.add(new_log)
                session.commit()
                
                # Показываем рассчитанные калории
                macros = calculate_food_calories(selected_food, weight)
                st.success(f"✅ Добавлено! Калории: {macros['calories']:.0f} ккал")
                st.balloons()
        
        # Показываем дневник за сегодня
        st.subheader("📋 Дневник за сегодня")
        
        today = date.today()
        today_logs = session.query(FoodLog).filter(
            FoodLog.user_id == user.user_id,
            FoodLog.date == today
        ).order_by(FoodLog.id.desc()).all()
        
        if today_logs:
            for log in today_logs:
                macros = calculate_food_calories(log.food, log.weight_eaten)
                
                with st.expander(f"{log.food.name} - {log.weight_eaten}г ({macros['calories']:.0f} ккал)"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Белки", f"{macros['protein']:.1f}г")
                    col2.metric("Жиры", f"{macros['fat']:.1f}г")
                    col3.metric("Углеводы", f"{macros['carbs']:.1f}г")
                    col4.metric("Тип", log.meal_type)
            
            # Общие итоги
            totals = calculate_daily_totals(today_logs)
            st.subheader("📊 Итого за день")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Калории", f"{totals['calories']:.0f} ккал")
            with col2:
                st.metric("Белки", f"{totals['protein']:.1f} г")
            with col3:
                st.metric("Жиры", f"{totals['fat']:.1f} г")
            with col4:
                st.metric("Углеводы", f"{totals['carbs']:.1f} г")
        else:
            st.info("Пока нет записей за сегодня")

# ============================================================================
# СТРАНИЦА ТРЕНИРОВОК
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
        
        # Базовые параметры тренировки
        col1, col2 = st.columns(2)
        with col1:
            w_date = st.date_input("Дата:", value=selected_date, key="w_date_input")
            w_duration = st.number_input("Длительность (мин):", min_value=1, value=60, step=5, key="w_dur")
        with col2:
            w_intensity = st.selectbox("Общая интенсивность:", ["Легкая", "Средняя", "Тяжелая", "Максимальная"], key="w_int")
        
        st.markdown("---")
        st.markdown("##### Добавить упражнение")
        
        # Инициализация временного списка упражнений в session_state
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
            
            # Если выбираем "Другое", показываем поля для нового упражнения
            if ex_choice == "🔍 Другое (добавить свое)":
                new_ex_name = st.text_input("Название упражнения:", key="new_ex_name")
                new_ex_type = st.selectbox("Тип:", ["strength", "cardio", "flexibility"], key="new_ex_type")
                new_ex_muscles = st.text_input("Целевые мышцы (через запятую):", key="new_ex_muscles")
        
        with col_b:
            ex_sets = st.number_input("Подходы:", min_value=1, value=3, key="ex_sets")
            ex_reps = st.number_input("Повторения:", min_value=1, value=10, key="ex_reps")
        with col_c:
            ex_weight = st.number_input("Вес (кг):", min_value=0.0, value=20.0, step=2.5, key="ex_weight")
        
        # Кнопка добавления упражнения во временный список
        if st.button("➕ Добавить упражнение в тренировку", use_container_width=True):
            if ex_choice == "🔍 Другое (добавить свое)":
                if not new_ex_name:
                    st.error("❌ Введите название упражнения!")
                else:
                    # Проверяем, есть ли уже такое упражнение
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
                        session.flush() # Получаем ex_id
            else:
                ex_obj = ex_options[ex_choice]
            
            # Добавляем в session_state
            st.session_state.temp_exercises.append({
                'exercise_id': ex_obj.exercise_id,
                'exercise_name': ex_obj.name,
                'sets': ex_sets,
                'reps': ex_reps,
                'weight': ex_weight
            })
            st.success(f"✅ {ex_obj.name} добавлен в список!")
            st.rerun() # Перезагружаем, чтобы обновить список
        
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
            # Кнопка сохранения всей тренировки в БД
            if st.button("💾 Сохранить тренировку целиком", type="primary", use_container_width=True):
                # 1. Создаем запись Workout
                new_workout = Workout(
                    user_id=user.user_id,
                    date=w_date,
                    duration_minutes=w_duration
                )
                session.add(new_workout)
                session.flush() # Получаем workout_id
                
                # 2. Создаем записи WorkoutLog для каждого упражнения
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
                
                # 3. Коммитим и очищаем session_state
                session.commit()
                st.session_state.temp_exercises = [] 
                st.success("🎉 Тренировка успешно сохранена!")
                st.balloons()
                st.rerun()
        
        st.markdown("---")
        
        # ====== 4. ПРОСМОТР ТРЕНИРОВОК ЗА ВЫБРАННУЮ ДАТУ ======
        st.subheader(f"📋 Тренировки за {selected_date.strftime('%d.%m.%Y')}")
        
        day_workouts = session.query(Workout).filter(
            Workout.user_id == user.user_id,
            Workout.date == selected_date
        ).order_by(Workout.workout_id.desc()).all()
        
        if day_workouts:
            for workout in day_workouts:
                volume = calculate_workout_volume(workout.logs)
                # Берем интенсивность из первого упражнения (для простоты отображения)
                intensity_display = workout.logs[0].intensity if workout.logs else "N/A"
                
                with st.expander(f"🏋️ {workout.duration_minutes} мин | Интенсивность: {intensity_display} | Объем: {volume:.1f} кг"):
                    for log in workout.logs:
                        st.write(f"- **{log.exercise.name}**: {log.sets}×{log.reps} @ {log.weight} кг")
                    
                    st.markdown("")
                    if st.button("🗑️ Удалить тренировку", key=f"del_w_{workout.workout_id}"):
                        session.delete(workout)
                        session.commit()
                        st.rerun()
        else:
            st.info(f"📭 Тренировок за {selected_date.strftime('%d.%m.%Y')} не найдено")
    st.header("Дневник тренировок")
    
    user = session.query(User).first()
    
    if not user:
        st.error("Пользователь не найден!")
    else:
        # Форма добавления тренировки
        st.subheader("➕ Добавить тренировку")
        
        with st.form("add_workout_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Дата тренировки
                workout_date = st.date_input("Дата:", value=date.today())
                
                # Длительность
                duration = st.number_input(
                    "Длительность (минуты):",
                    min_value=1,
                    max_value=300,
                    value=60,
                    step=5
                )
            
            with col2:
                # Выбор упражнения
                exercises = session.query(Exercise).all()
                exercise_options = {e.name: e for e in exercises}
                selected_exercise_name = st.selectbox(
                    "Выбери упражнение:",
                    options=list(exercise_options.keys())
                )
                
                # Интенсивность
                intensity = st.selectbox(
                    "Интенсивность:",
                    ["Легкая", "Средняя", "Тяжелая", "Максимальная"]
                )
            
            st.subheader("Подходы")
            
            # Добавляем 3 подхода по умолчанию
            sets_data = []
            for i in range(3):
                col1, col2, col3 = st.columns(3)
                with col1:
                    weight = st.number_input(f"Подход {i+1} - Вес (кг):", min_value=0, value=20, step=5, key=f"weight_{i}")
                with col2:
                    reps = st.number_input(f"Подход {i+1} - Повторения:", min_value=0, value=10, step=1, key=f"reps_{i}")
                with col3:
                    sets = st.number_input(f"Подход {i+1} - Кол-во подходов:", min_value=0, value=3, step=1, key=f"sets_{i}")
                
                sets_data.append({
                    'weight': weight,
                    'reps': reps,
                    'sets': sets
                })
            
            submitted = st.form_submit_button("✅ Сохранить тренировку")
            
            if submitted and selected_exercise_name:
                selected_exercise = exercise_options[selected_exercise_name]
                
                # Создаем тренировку
                new_workout = Workout(
                    user_id=user.user_id,
                    date=workout_date,
                    duration_minutes=duration
                )
                session.add(new_workout)
                session.flush()  # Получаем workout_id
                
                # Добавляем подходы
                for set_data in sets_data:
                    if set_data['sets'] > 0 and set_data['reps'] > 0:
                        new_log = WorkoutLog(
                            workout_id=new_workout.workout_id,
                            exercise_id=selected_exercise.exercise_id,
                            sets=set_data['sets'],
                            reps=set_data['reps'],
                            weight=set_data['weight'],
                            intensity=intensity
                        )
                        session.add(new_log)
                
                session.commit()
                
                # Рассчитываем объем
                volume = calculate_workout_volume(new_workout.logs)
                st.success(f"✅ Тренировка сохранена! Объем: {volume:.1f} кг")
                st.balloons()
        
                # Показываем последние тренировки
        st.subheader("📋 Последние тренировки")
        
        recent_workouts = session.query(Workout).filter(
            Workout.user_id == user.user_id
        ).order_by(Workout.date.desc()).limit(10).all()
        
        if recent_workouts:
            for workout in recent_workouts:
                volume = calculate_workout_volume(workout.logs)
                
                with st.expander(f"🏋️ {workout.date.strftime('%d.%m.%Y')} - {workout.duration_minutes} мин | Объем: {volume:.1f} кг"):
                    # Список упражнений
                    for log in workout.logs:
                        st.write(f"- **{log.exercise.name}**: {log.sets}×{log.reps} @ {log.weight}кг")
                    
                    # Кнопка удаления
                    if st.button("🗑️ Удалить тренировку", key=f"del_workout_{workout.workout_id}"):
                        session.delete(workout)
                        session.commit()
                        st.rerun()
        else:
            st.info("Пока нет тренировок")

# ============================================================================
# СТРАНИЦА ПРОГРЕССА
# ============================================================================

elif page == "📊 Прогресс":
    st.header("Прогресс")
    
    user = session.query(User).first()
    
    if not user:
        st.error("Пользователь не найден!")
    else:
        st.info("🚧 Раздел в разработке. Здесь будут графики прогресса веса, силовых показателей и т.д.")
        
        # Временная заглушка - показываем историю замеров
        st.subheader("📈 История замеров веса")
        
        measurements = session.query(User).first().measurements
        
        if measurements:
            for m in measurements:
                st.write(f"{m.date}: {m.weight} кг")
        else:
            st.info("Нет данных о замерах")

# Закрываем сессию
session.close()