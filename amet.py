import pandas as pd
import random


df = pd.read_csv("new_table.csv")

#подготовка таблицы
df["Calories"] = df["Calories"].replace(" кКал", "", regex=True)
df["Proteins"] = df["Proteins"].replace(" г", "", regex=True)
df["Fats"] = df["Fats"].replace(" г", "", regex=True)
df["Carbohydrates"] = df["Carbohydrates"].replace(" г", "", regex=True)
df["Calories"] = df["Calories"].astype(float)
df["Proteins"] = df["Proteins"].astype(float)
df["Fats"] = df["Fats"].astype(float)
df["Carbohydrates"] = df["Carbohydrates"].astype(float)

# задаем норму потребления углеводов, белков и жиров в граммах для пользователя
def calculate_ptc(current_user):
    daily_calories = current_user.daily_cal
    goal = current_user.goal
    daily_carbs = 0
    daily_proteins = 0
    daily_fats = 0
    if goal=='lose_weight':
        daily_carbs += round(daily_calories/(2*4.1),0)
        daily_proteins += round(daily_calories/(4*4.1),0)
        daily_fats += round(daily_calories/(4*9.3),0)
    elif goal=='gain_weight':
        daily_carbs += round(((daily_calories*0.45)/4.1),0)
        daily_proteins += round(((daily_calories*0.3)/4.1),0)
        daily_fats += round(daily_calories/(4*9.3),0)
    else:
        daily_carbs += round(((daily_calories*0.5)/4.1),0)
        daily_proteins += round(((daily_calories*0.25)/4.1),0)
        daily_fats += round(daily_calories/(4*9.3),0)
    return daily_carbs, daily_proteins, daily_fats

# функция для подсчета калорий, белков, жиров и углеводов в блюде в зависимости от граммовки
def calculate_nutrients(dish, grams):
    calories = df.loc[df["Dish Name"] == dish, "Calories"].values[0] * grams / 100
    proteins = df.loc[df["Dish Name"] == dish, "Proteins"].values[0] * grams / 100
    fats = df.loc[df["Dish Name"] == dish, "Fats"].values[0] * grams / 100
    carbs = df.loc[df["Dish Name"] == dish, "Carbohydrates"].values[0] * grams / 100
    recipe=df.loc[df["Dish Name"] == dish, "Ingredients"].values[0]
    return calories, proteins, fats, carbs, recipe

# функция для рекомендации блюда для следующего приема пищи
def recommend_dish(meal_calories, dish_type, current_proteins, current_fats, current_carbs,current_user):
    preference = ""
    allergy = ""
    user_preference_names = [pref.preference_name for pref in current_user.preferences]
    preference = "; ".join(user_preference_names)

    user_allergies = [pref.allergy_name for pref in current_user.allergies]
    allergy = "; ".join(user_allergies)
    allergy = allergy.lower()
    preference = preference.lower()



    daily_carbs, daily_proteins, daily_fats = calculate_ptc(current_user)
    # создаем пустой список для хранения подходящих блюд
    suitable_dishes = []
    # перебираем все блюда из таблицы
    for dish in df["Dish Name"]:
        # для каждого блюда подбираем такую граммовку, чтобы не превысить суточную норму калорий
        max_grams = ((meal_calories) / df.loc[df["Dish Name"] == dish, "Calories"].values[0]) * 100
        # если граммовка положительная, то блюдо подходит
        
        d_type=str(df.loc[df["Dish Name"] == dish, "Dish_type"].values[0]).lower()
        aller=str(df.loc[df["Dish Name"] == dish, "Allergies"].values[0]).lower()
        prefer=str(df.loc[df["Dish Name"] == dish, "Preference"].values[0]).lower()
        allergens_list = [item.strip() for item in aller.split(';')]
        user_allergy_list = [item.strip() for item in allergy.split(';')]

        preferences_list = [item.strip() for item in preference.split(';')]
        user_prefer_list = [item.strip() for item in prefer.split(';')]
        print(type(allergy), ",",aller, not(any(user.lower() in allergen.lower() for allergen in allergens_list for user in user_allergy_list)))
        if allergy != "": 
            print("EMPTY ALLERGY")
            if max_grams > 10 and (dish_type in d_type) and not(any(user.lower() in allergen.lower() for allergen in allergens_list for user in user_allergy_list)) and any(user.lower() in preference.lower() for preference in preferences_list for user in user_prefer_list) :
                # добавляем блюдо и граммовку в список подходящих блюд
                suitable_dishes.append((dish, max_grams))
        else:
            if max_grams > 10 and (dish_type in d_type) and any(user.lower() in preference.lower() for preference in preferences_list for user in user_prefer_list) :
                # добавляем блюдо и граммовку в список подходящих блюд
                suitable_dishes.append((dish, max_grams))

        
    
    result_df = pd.DataFrame([], columns=['Dish Name', 'Grams', "Calories", 'Proteins', 'Fats', 'Carbs', "Recipe",'Ingredients',"Image main", 'Image for recipe', 'Preference','Allergy', "Dish type"])
    # если список подходящих блюд не пустой, то выбираем из него случайное блюдо
    if suitable_dishes:
        if len(suitable_dishes)>30:
            for i in range(30):
                с=random.choice(suitable_dishes)
                suitable_dishes.remove(с)
                dish, max_grams = с
                
                # для выбранного блюда подбираем такую граммовку, чтобы приблизиться к норме потребления углеводов, белков и жиров в граммах
                # для этого минимизируем функцию ошибки, которая равна сумме квадратов отклонений от нормы потребления углеводов, белков и жиров
                def error_function(grams):
                    calories, proteins, fats, carbs, recipe = calculate_nutrients(dish, grams)
                    total_proteins = current_proteins + proteins
                    total_fats = current_fats + fats
                    total_carbs = current_carbs + carbs
                    protein_error = (total_proteins - daily_proteins) ** 2
                    fat_error = (total_fats - daily_fats) ** 2
                    carb_error = (total_carbs - daily_carbs) ** 2
                    return protein_error + fat_error + carb_error
                # используем метод золотого сечения для поиска минимума функции ошибки на отрезке [0, max_grams]
                # задаем точность поиска
                epsilon = 0.01
                # задаем константу золотого сечения
                phi = (1 + 5 ** 0.5) / 2
                # инициализируем границы отрезка
                a = 0
                b = max_grams
                # инициализируем точки деления отрезка
                x1 = b - (b - a) / phi
                x2 = a + (b - a) / phi
                # инициализируем значения функции ошибки в точках деления
                y1 = error_function(x1)
                y2 = error_function(x2)
                # повторяем пока длина отрезка больше заданной точности
                while abs(b - a) > epsilon:
                    # сравниваем значения функции ошибки в точках деления
                    if y1 < y2:
                        # выбираем левую половину отрезка
                        b = x2
                        # пересчитываем правую точку деления
                        x2 = x1
                        y2 = y1
                        # находим новую левую точку деления
                        x1 = b - (b - a) / phi
                        y1 = error_function(x1)
                    else:
                        # выбираем правую половину отрезка
                        a = x1
                        # пересчитываем левую точку деления
                        x1 = x2
                        y1 = y2
                        # находим новую правую точку деления
                        x2 = a + (b - a) / phi
                        y2 = error_function(x2)
                # берем среднее арифметическое границ отрезка как оптимальную граммовку
                optimal_grams = (a + b) / 2
                try:
                # округляем граммовку до целого числа
                    optimal_grams = round(optimal_grams)
                except ValueError:
                    continue
                # добавляем проверку на граммовку больше 450 грамм
                # если граммовка больше 430 грамм, то уменьшаем ее до 350 грамм
                #if optimal_grams > 600:
                    
                #    optimal_grams = 600
                # добавляем проверку на суточную норму калорий
                # если рекомендованное блюдо с граммовкой закрывает суточную норму калорий, то уменьшаем граммовку так, чтобы оставалось 10% от суточной нормы калорий
                        # подсчитываем калории, белки, жиры и углеводы для выбранного блюда и граммовки
                calories, proteins, fats, carbs, recipe = calculate_nutrients(dish, optimal_grams)
                # возвращаем рекомендованное блюдо, граммовку и питательные вещества
                ingredients=df.loc[df["Dish Name"] == dish, "Ingredients"].values[0]
                recipe=df.loc[df["Dish Name"] == dish, "Recipe"].values[0]
                image_main=df.loc[df["Dish Name"] == dish, "Image"].values[0]
                image_recipe=df.loc[df["Dish Name"] == dish, "Recipe_Images"].values[0]
                pref=df.loc[df["Dish Name"] == dish, "Preference"].values[0]
                allerg=df.loc[df["Dish Name"] == dish, "Allergies"].values[0]
                d_type=df.loc[df["Dish Name"] == dish, "Dish_type"].values[0]
                #print(df.loc[df["Dish Name"] == dish, "Ingredients"].values[0])
                result_df.loc[len(result_df.index)]=[dish, optimal_grams, calories, proteins, fats, carbs, recipe, ingredients, image_main, image_recipe, pref, allerg, d_type]
            
                
            return result_df
        else:
            for i in range(len(suitable_dishes)):
                с=random.choice(suitable_dishes)
                suitable_dishes.remove(с)
                dish, max_grams = с
                
                # для выбранного блюда подбираем такую граммовку, чтобы приблизиться к норме потребления углеводов, белков и жиров в граммах
                # для этого минимизируем функцию ошибки, которая равна сумме квадратов отклонений от нормы потребления углеводов, белков и жиров
                def error_function(grams):
                    calories, proteins, fats, carbs, recipe = calculate_nutrients(dish, grams)
                    total_proteins = current_proteins + proteins
                    total_fats = current_fats + fats
                    total_carbs = current_carbs + carbs
                    protein_error = (total_proteins - daily_proteins) ** 2
                    fat_error = (total_fats - daily_fats) ** 2
                    carb_error = (total_carbs - daily_carbs) ** 2
                    return protein_error + fat_error + carb_error
                # используем метод золотого сечения для поиска минимума функции ошибки на отрезке [0, max_grams]
                # задаем точность поиска
                epsilon = 0.01
                # задаем константу золотого сечения
                phi = (1 + 5 ** 0.5) / 2
                # инициализируем границы отрезка
                a = 0
                b = max_grams
                # инициализируем точки деления отрезка
                x1 = b - (b - a) / phi
                x2 = a + (b - a) / phi
                # инициализируем значения функции ошибки в точках деления
                y1 = error_function(x1)
                y2 = error_function(x2)
                # повторяем пока длина отрезка больше заданной точности
                while abs(b - a) > epsilon:
                    # сравниваем значения функции ошибки в точках деления
                    if y1 < y2:
                        # выбираем левую половину отрезка
                        b = x2
                        # пересчитываем правую точку деления
                        x2 = x1
                        y2 = y1
                        # находим новую левую точку деления
                        x1 = b - (b - a) / phi
                        y1 = error_function(x1)
                    else:
                        # выбираем правую половину отрезка
                        a = x1
                        # пересчитываем левую точку деления
                        x1 = x2
                        y1 = y2
                        # находим новую правую точку деления
                        x2 = a + (b - a) / phi
                        y2 = error_function(x2)
                # берем среднее арифметическое границ отрезка как оптимальную граммовку
                optimal_grams = (a + b) / 2
                # округляем граммовку до целого числа
                optimal_grams = round(optimal_grams)
                # добавляем проверку на граммовку больше 450 грамм
                # если граммовка больше 430 грамм, то уменьшаем ее до 350 грамм
                if optimal_grams > 600:
                    optimal_grams = 600
                # добавляем проверку на суточную норму калорий
                # если рекомендованное блюдо с граммовкой закрывает суточную норму калорий, то уменьшаем граммовку так, чтобы оставалось 10% от суточной нормы калорий
                        # подсчитываем калории, белки, жиры и углеводы для выбранного блюда и граммовки
                calories, proteins, fats, carbs, recipe = calculate_nutrients(dish, optimal_grams)

                # возвращаем рекомендованное блюдо, граммовку и питательные вещества
                ingredients=df.loc[df["Dish Name"] == dish, "Ingredients"].values[0]
                recipe=df.loc[df["Dish Name"] == dish, "Recipe"].values[0]
                image_main=df.loc[df["Dish Name"] == dish, "Image"].values[0]
                image_recipe=df.loc[df["Dish Name"] == dish, "Recipe_Images"].values[0]
                pref=df.loc[df["Dish Name"] == dish, "Preference"].values[0]
                allerg=df.loc[df["Dish Name"] == dish, "Allergies"].values[0]
                d_type=df.loc[df["Dish Name"] == dish, "Dish_type"].values[0]
                result_df.loc[len(result_df.index)]=[dish, optimal_grams, calories, proteins, fats, carbs, recipe, ingredients, image_main, image_recipe, pref, allerg, d_type]
            
                
            return result_df

        # если список подходящих блюд пустой, то возвращаем None
    else:
        return None

def meal_type(dish_type,user):
    daily_calories = user.daily_cal
    dish_type=str(dish_type).lower()
    if dish_type=='завтрак':
        meal_calories=round(daily_calories*0.33)
        return meal_calories, dish_type
    elif dish_type=='обед':
        meal_calories=round(daily_calories*0.43)
        return meal_calories, dish_type
    elif dish_type=='ужин':
        meal_calories=round(daily_calories*0.24)
        return meal_calories, dish_type
    else:
        return None

def dish_choice(table_df, dish):
    dish=str(dish).capitalize()
    if dish in table_df["Dish Name"].values:
        return dish
    else:
        return None

def show_dish(dish, grams, calories, recipe, ingred):
    print(f"Рекомендуемое блюдо: {dish}")
    print(f"Граммовка: {grams} г")
    print(f"Калории: {calories} ккал")
    print(f"Ингредиенты: {ingred}")
    print(f"Рецепт: {recipe}")
# инициализируем текущие значения калорий и питательных веществ для пользователя
def update_nutrients(current_calories,current_proteins,current_fats,current_carbs, table_df, dish):
    current_calories = table_df.loc[table_df["Dish Name"] == dish, "Calories"].values
    current_proteins = table_df.loc[table_df["Dish Name"] == dish, "Proteins"].values
    current_fats = table_df.loc[table_df["Dish Name"] == dish, "Fats"].values
    current_carbs = table_df.loc[table_df["Dish Name"] == dish, "Carbs"].values
    return current_proteins,current_fats,current_carbs

def ratio_nutrients(user,current_calories,current_proteins,current_fats,current_carbs):
    daily_carbs, daily_proteins, daily_fats=calculate_ptc(user)
    total_nutrients = (daily_carbs + daily_proteins + daily_fats)
    return print(f"Текущее соотношение белков, жиров и углеводов: {current_proteins / total_nutrients * 100}% : {current_fats / total_nutrients * 100}% : {current_carbs / total_nutrients * 100}% \n Текущая калорийность: {current_calories} ккал из {user.daily_calories} ккал")

def work_recomnendation1(user, current_calories,current_proteins,current_fats,current_carbs,dish_type,choose_dish):
    # начинаем цикл приемов пищи

    ratio_nutrients(user,current_calories,current_proteins,current_fats,current_carbs)
    meal_calories, dish_type=meal_type(dish_type)
    # получаем рекомендованное блюдо, граммовку и питательные вещества от функции
    table_df = recommend_dish(meal_calories, dish_type,user[6],user[8], current_proteins, current_fats, current_carbs)
    # если функция вернула None, то значит, что нет подходящих блюд
    if table_df is None:
        print("Нет подходящих блюд для следующего приема пищи, пожалуйста, выберите другой вариант")
        return None

    # иначе, распаковываем рекомендацию в переменные
    else:
        print("Вот список всех блюд из таблицы:")
        print(table_df["Dish Name"])
        # спрашиваем пользователя, какое блюдо он хочет выбрать
        dish=dish_choice(table_df, choose_dish)
        # проверяем, есть ли такое блюдо в таблице
        if dish in table_df["Dish Name"].values:
            # обновляем текущие значения калорий и питательных веществ для пользователя
#    result_df = pd.DataFrame([], columns=['Dish Name', 'Grams', "Calories", 'Proteins', 'Fats', 'Carbs', "Recipe",'Ingredients',"Image main", 'Image for recipe', 'Preference','Allergy', "Dish type"])

            current_calories,current_proteins,current_fats,current_carbs = update_nutrients(current_calories,current_proteins,current_fats,current_carbs, table_df, dish)

            grams=table_df.loc[table_df["Dish Name"] == dish, "Grams"].values
            calories=table_df.loc[table_df["Dish Name"] == dish, "Calories"].values
            ingred=table_df.loc[table_df["Dish Name"] == dish, "Ingredients"].values
            recipe=table_df.loc[table_df["Dish Name"] == dish, "Recipe"].values
            # выводим выбранное блюдо, граммовку и питательные вещества на экран
            show_dish(dish, grams, calories, recipe, ingred)
            
        else:
            # если такого блюда нет в таблице, то выводим сообщение об ошибке
            print()
            print("Такого блюда нет в таблице, пожалуйста, выберите другое блюдо")
            return None

