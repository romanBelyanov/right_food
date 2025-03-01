import pandas as pd
import random
import math
import sqlite3

df = pd.read_csv("new_table.csv")

user_id=12
conn = sqlite3.connect('users.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
user = cur.fetchone()



df["Calories"] = df["Calories"].replace(" кКал", "", regex=True)
df["Proteins"] = df["Proteins"].replace(" г", "", regex=True)
df["Fats"] = df["Fats"].replace(" г", "", regex=True)
df["Carbohydrates"] = df["Carbohydrates"].replace(" г", "", regex=True)

df["Calories"] = df["Calories"].astype(float)
df["Proteins"] = df["Proteins"].astype(float)
df["Fats"] = df["Fats"].astype(float)
df["Carbohydrates"] = df["Carbohydrates"].astype(float)



# функция для подсчета калорий, белков, жиров и углеводов в блюде в зависимости от граммовки
def calculate_nutrients(dish, grams):
    calories = df.loc[df["Dish Name"] == dish, "Calories"].values[0] * grams / 100
    proteins = df.loc[df["Dish Name"] == dish, "Proteins"].values[0] * grams / 100
    fats = df.loc[df["Dish Name"] == dish, "Fats"].values[0] * grams / 100
    carbs = df.loc[df["Dish Name"] == dish, "Carbohydrates"].values[0] * grams / 100
    recipe=df.loc[df["Dish Name"] == dish, "Ingredients"].values[0]
    return calories, proteins, fats, carbs, recipe

# функция для рекомендации блюда для следующего приема пищи
def recommend_dish(meal_calories, dish_type, preference, allergy, current_proteins, current_fats, current_carbs,daily_proteins,daily_fats,daily_carbs):
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
        if max_grams > 10 and (dish_type in d_type) and (allergy not in aller) and (preference in prefer) :
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

# функция для вывода рекомендации на экран

# инициализируем текущие значения калорий и питательных веществ для пользователя
current_calories = 0
current_proteins = 0
current_fats = 0
current_carbs = 0
flag=True
# начинаем цикл приемов пищи
while flag:
    # выводим текущие значения калорий и питательных веществ для пользователя
    print(f"Текущая калорийность: {current_calories} ккал из {daily_calories} ккал")
    # если текущая калорийность не равна нулю, то выводим текущее соотношение белков, жиров и углеводов
    if current_calories != 0:
        # находим сумму текущих белков, жиров и углеводов, умноженную на 4
        total_nutrients = (current_proteins + current_fats + current_carbs)
        # делим текущее количество белков, жиров и углеводов на сумму нутриентов и умножаем на 100, чтобы получить проценты
        print(f"Текущее соотношение белков, жиров и углеводов: {current_proteins / total_nutrients * 100}% : {current_fats / total_nutrients * 100}% : {current_carbs / total_nutrients * 100}%")
        print()
    # иначе, выводим сообщение, что соотношение пока не определено
    else:
        print("Текущее соотношение белков, жиров и углеводов: пока не определено")
        print()
    # спрашиваем пользователя, хочет ли он выбрать блюдо сам или получить рекомендацию от программы

    dish_type=input('Блюдо для какого приема пищи Вы подбираете? (Завтрак/Обед/Ужин)\n')
    dish_type=dish_type.lower()
    if dish_type=='завтрак':
        meal_calories=round(daily_calories*0.33)
    elif dish_type=='обед':
        meal_calories=round(daily_calories*0.43)
    elif dish_type=='ужин':
        meal_calories=round(daily_calories*0.24)
        flag=False
    else:
        print('ошибка')
        break
    # получаем рекомендованное блюдо, граммовку и питательные вещества от функции
    table_df = recommend_dish(meal_calories, dish_type,user[6],user[8], current_proteins, current_fats, current_carbs)
    # если функция вернула None, то значит, что нет подходящих блюд
    if table_df is None:
        print()
        print("Нет подходящих блюд для следующего приема пищи, пожалуйста, выберите другой вариант")
        continue
    # иначе, распаковываем рекомендацию в переменные
    else:
        print("Вот список всех блюд из таблицы:")
        print()
        print(table_df["Dish Name"])
        # спрашиваем пользователя, какое блюдо он хочет выбрать
        print()
        dish = input("Какое блюдо вы хотите выбрать? (введите название блюда)\n")
        dish=dish.capitalize()
        # проверяем, есть ли такое блюдо в таблице
        if dish in table_df["Dish Name"].values:
            # обновляем текущие значения калорий и питательных веществ для пользователя
#    result_df = pd.DataFrame([], columns=['Dish Name', 'Grams', "Calories", 'Proteins', 'Fats', 'Carbs', "Recipe",'Ingredients',"Image main", 'Image for recipe', 'Preference','Allergy', "Dish type"])

            current_calories += table_df.loc[table_df["Dish Name"] == dish, "Calories"].values
            current_proteins += table_df.loc[table_df["Dish Name"] == dish, "Proteins"].values
            current_fats += table_df.loc[table_df["Dish Name"] == dish, "Fats"].values
            current_carbs += table_df.loc[table_df["Dish Name"] == dish, "Carbs"].values
            grams=table_df.loc[table_df["Dish Name"] == dish, "Grams"].values
            calories=table_df.loc[table_df["Dish Name"] == dish, "Calories"].values
            ingred=table_df.loc[table_df["Dish Name"] == dish, "Ingredients"].values
            recipe=table_df.loc[table_df["Dish Name"] == dish, "Recipe"].values
            # выводим выбранное блюдо, граммовку и питательные вещества на экран
            print()
            print(f"Рекомендуемое блюдо: {dish}")
            print(f"Граммовка: {grams} г")
            print(f"Калории: {calories} ккал")
            print(f"Ингредиенты: {ingred}")
            print(f"Рецепт: {recipe}")
            print()
            if current_calories != 0:
                total_nutrients = (current_proteins + current_fats + current_carbs)

                print(f"Текущее соотношение белков, жиров и углеводов: {current_proteins / total_nutrients * 100}% : {current_fats / total_nutrients * 100}% : {current_carbs / total_nutrients * 100}%")

        else:
            # если такого блюда нет в таблице, то выводим сообщение об ошибке
            print()
            print("Такого блюда нет в таблице, пожалуйста, выберите другое блюдо")
            continue
        #dish, grams, calories, proteins, fats, carbs, recipe = recommendation
        # обновляем текущие значения калорий и питательных веществ для пользователя
        #current_calories += calories
        #current_proteins += proteins
        #current_fats += fats
        #current_carbs += carbs
        # выводим рекомендованное блюдо, граммовку и питательные вещества на экран
        #print_recommendation(dish, grams, calories, proteins, fats, carbs, recipe)
# если пользователь ввел что-то другое, то выводим сообщение об ошибке

# спрашиваем пользователя, хочет ли он продолжить приемы пищи или закончить программу
    print()
    answer = input("Вы хотите продолжить приемы пищи или закончить программу? (введите 1 или 2)\n1. Продолжить\n2. Закончить\n")
    # если пользователь выбрал 1, то продолжаем цикл
    if answer == "1":
        continue
    # если пользователь выбрал 2, то завершаем цикл и программу
    elif answer == "2":
        print("Спасибо за использование программы, до свидания!")
        break
    # если пользователь ввел что-то другое, то выводим сообщение об ошибке и продолжаем цикл
    else:
        print("Неверный выбор, пожалуйста, введите 1 или 2")
        continue
