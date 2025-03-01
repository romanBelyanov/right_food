from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, jsonify, redirect,url_for,flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, session
from amet import recommend_dish,meal_type
import pandas as pd
from flask_login import logout_user





app = Flask(__name__)
app.static_folder = 'static'
app.config['SECRET_KEY'] = '93422'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
cache = Cache(app)
app.permanent_session_lifetime = timedelta(days=30)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(10))
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    age = db.Column(db.Integer)
    goal = db.Column(db.String(20))
    phy_act = db.Column(db.Float)
    daily_cal = db.Column(db.Float)
    daily_carbs = db.Column(db.Integer)
    daily_fats = db.Column(db.Integer)
    daily_proteins = db.Column(db.Integer)
    daily_water = db.Column(db.Float)
    preferences = db.relationship('Preference', backref='user', lazy=True)
    allergies = db.relationship('Allergy', backref='user', lazy=True)
    glasses = db.relationship('WaterGlass', backref='user', lazy=True)

class WaterGlass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class UserData1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))  # Замените на ваш тип данных
    dish_data = db.Column(db.PickleType())  # Это для хранения DataFrame как бинарных данных

    def __init__(self, user_id, dish_data):
        self.user_id = user_id
        self.dish_data = dish_data
class UserData2(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))  # Замените на ваш тип данных
    dish_data = db.Column(db.PickleType())  # Это для хранения DataFrame как бинарных данных

    def __init__(self, user_id, dish_data):
        self.user_id = user_id
        self.dish_data = dish_data
class UserData3(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))  # Замените на ваш тип данных
    dish_data = db.Column(db.PickleType())  # Это для хранения DataFrame как бинарных данных

    def __init__(self, user_id, dish_data):
        self.user_id = user_id
        self.dish_data = dish_data



class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    preference_name = db.Column(db.String(50))


class Allergy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    allergy_name = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('start1.html')
@app.route('/start2')
def index1():
    return render_template('start2.html')

@app.route('/allergy', methods=['GET', 'POST'])
@login_required
def allergy():
    if request.method == 'POST':
        selected_allergies = request.form.getlist('allergy')
        current_user.allergies = []  # Измените 'allergy' на 'allergies'

        for allergy_name in selected_allergies:
            allergy = Allergy.query.filter_by(user_id=current_user.id, allergy_name=allergy_name).first()
            if not allergy:
                allergy = Allergy(user_id=current_user.id, allergy_name=allergy_name)
                db.session.add(allergy)
            current_user.allergies.append(allergy)  # Измените 'allergy' на 'allergies'

        db.session.commit()
        flash('Allergies saved.', 'success')
        return redirect(url_for('main'))


    return render_template('allergy.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')


        if not username or not password or not email:
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password,email = email)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)


        return redirect(url_for('userinfo'))

    return render_template('register.html')

@app.route('/indpref', methods=['GET', 'POST'])
@login_required
def indpref():
    if request.method == 'POST':
        selected_preferences = request.form.getlist('preferences')
        current_user.preferences = []

        for preference_name in selected_preferences:
            preference = Preference.query.filter_by(user_id=current_user.id, preference_name=preference_name).first()
            if not preference:
                preference = Preference(user_id=current_user.id, preference_name=preference_name)
                db.session.add(preference)
            current_user.preferences.append(preference)

        db.session.commit()

        flash('Preferences saved.', 'success')
        return redirect(url_for('choose'))

    return render_template('indpref.html')


@app.route('/choose', methods=['GET', 'POST'])
def choose():
    return render_template('choose.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main'))
        else:
            flash('Login failed. Check your username and password.', 'error')

    return render_template('login.html')

def calculate_daily_cal(gender, weight, height, age, phy_act, goal):
    daily_cal = 0
    if gender == "male":
        daily_cal += (10 * weight + 6.25 * height - 5 * age + 5) * float(phy_act)
    elif gender == "female":
        daily_cal += (10*weight + 6.25 * height - 5 * age - 161) * float(phy_act)
    if goal == "lose_weight":
        k = daily_cal * 0.1
        daily_cal -= k
    elif goal == "gain_weight":
        k = daily_cal * 0.1
        daily_cal += k
    return daily_cal


def calculate_daily_water(gender, weight):
    daily_water = 0
    if gender == "male":
        daily_water = weight * 0.035
    elif gender == "female":
        daily_water = weight * 0.031
    return daily_water

def calculate_ptc(goal,daily_calories):
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


@app.route('/userinfo', methods=['GET', 'POST'])
def userinfo():

    if request.method == 'POST':
        current_user.gender = request.form.get('gender')
        current_user.weight = float(request.form.get('weight'))
        current_user.height = float(request.form.get('height'))
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.age = int(request.form.get('age'))
        current_user.goal = request.form.get('goal')
        current_user.phy_act = float(request.form.get('phy_act'))
        current_user.daily_cal = round(calculate_daily_cal(str(current_user.gender), current_user.weight,current_user.height,current_user.age,current_user.phy_act, current_user.goal),2)
        current_user.daily_carbs, current_user.daily_proteins, current_user.daily_fats = calculate_ptc(current_user.goal,current_user.daily_cal)
        current_user.daily_water = calculate_daily_water(str(current_user.gender),current_user.weight)
        db.session.commit()



        flash('User information saved.', 'success')
        return redirect(url_for('indpref'))

    return render_template('userinfo.html')

@login_required
@app.route('/main', methods=['GET'])
def main():
    user = User.query.get(current_user.id)
    daily_water = int(user.daily_water/0.25)
    daily_water1 = round(float(user.daily_water),2)
    return render_template('main.html',user=user,daily_water=daily_water,daily_water1=daily_water1)

def split_text_to_lines(text):
    # Разделяем текст на строки
    lines = text.split(';')

    # Формируем строку с использованием символов переноса строки
    result = "<br>".join(line.strip() for line in lines)

    return result

app.jinja_env.globals.update(split_text_to_lines=split_text_to_lines)

@login_required
@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if request.method == 'POST':
        data = request.get_json()
        selected_dish_data = data.get('selectedDish')
        meal_type = data.get('mealType')  # Assuming mealType is sent in the AJAX request

        if meal_type == 'breakfast':
            user_data = UserData1.query.filter_by(user_id=current_user.id).first()
        elif meal_type == 'lunch':
            user_data = UserData2.query.filter_by(user_id=current_user.id).first()
        elif meal_type == 'dinner':
            user_data = UserData3.query.filter_by(user_id=current_user.id).first()
        else:
            return jsonify({'error': 'Invalid meal type'})

        if user_data:
            if meal_type == 'lunch':
                user_data.dish_data = selected_dish_data
            elif meal_type == 'dinner':
                user_data.dish_data = selected_dish_data
            elif meal_type == 'breakfast':
                user_data.dish_data = selected_dish_data
        else:
            if meal_type == 'breakfast':
                user_data = UserData1(user_id=current_user.id)
            elif meal_type == 'lunch':
                user_data = UserData2(user_id=current_user.id)
            elif meal_type == 'dinner':
                user_data = UserData3(user_id=current_user.id)

            db.session.add(user_data)

        db.session.commit()

        return jsonify({'message': 'Selected dish received successfully!'})

    user_data_breakfast = UserData1.query.filter_by(user_id=current_user.id).first()
    user_data_lunch = UserData2.query.filter_by(user_id=current_user.id).first()
    user_data_dinner = UserData3.query.filter_by(user_id=current_user.id).first()

    df_breakfast = user_data_breakfast.dish_data if user_data_breakfast else None
    df_breakfast = pd.DataFrame([df_breakfast]) if df_breakfast else None

    df_lunch = user_data_lunch.dish_data if user_data_lunch else None
    df_lunch = pd.DataFrame([df_lunch]) if df_lunch else None

    df_dinner = user_data_dinner.dish_data if user_data_dinner else None
    df_dinner = pd.DataFrame([df_dinner]) if df_dinner else None

    return render_template('calendar.html', df_breakfast=df_breakfast, df_lunch=df_lunch, df_dinner=df_dinner)

@login_required
@app.route('/products')
def products():
    return render_template('products.html')
@login_required
@app.route('/etc')
def etc():
    user = User.query.get(current_user.id)
    return render_template('etc.html',user=user)

@login_required
@app.route('/breakfast')
def breakfast():
    user = User.query.get(current_user.id)
    meal_calories, dish_type= meal_type("завтрак",user)
    table = recommend_dish(meal_calories,dish_type,0,0,0,user)
    print(table)
    l = len(table)
    return render_template('breakfast.html',table=table, l = l)

@login_required
@app.route('/lunch')
def lunch():
    user = User.query.get(current_user.id)
    meal_calories, dish_type= meal_type("обед",user)
    table = recommend_dish(meal_calories,dish_type,0,0,0,user)
    l = len(table)
    print(table["Calories"])
    return render_template('lunch.html',table=table, l = l)

@login_required
@app.route('/dinner')
def dinner():
    user = User.query.get(current_user.id)
    meal_calories, dish_type= meal_type("ужин",user)
    table = recommend_dish(meal_calories,dish_type,0,0,0,user)
    l = len(table)
    print(table["Calories"])
    return render_template('dinner.html',table=table, l = l)

@app.route('/process_selected_dish', methods=['POST'])
def process_selected_dish():
    data = request.get_json()
    selected_dish_data = data.get('selectedDish')

    # Проверяем, существует ли запись для данного пользователя
    user_data = UserData1.query.filter_by(user_id=current_user.id).first()

    if user_data:
        # Обновляем существующую запись
        user_data.dish_data = selected_dish_data
    else:
        # Создаем новую запись
        user_data = UserData1(user_id=current_user.id, dish_data=selected_dish_data)
        db.session.add(user_data)

    db.session.commit()

    return jsonify({'message': 'Selected dish received successfully!'})

@app.route('/process_selected_dish1', methods=['POST'])
def process_selected_dish1():
    data = request.get_json()
    selected_dish_data = data.get('selectedDish')

    # Проверяем, существует ли запись для данного пользователя
    user_data = UserData2.query.filter_by(user_id=current_user.id).first()

    if user_data:
        # Обновляем существующую запись
        user_data.dish_data = selected_dish_data
    else:
        # Создаем новую запись
        user_data = UserData2(user_id=current_user.id, dish_data=selected_dish_data)
        db.session.add(user_data)

    db.session.commit()

    return jsonify({'message': 'Selected dish received successfully!'})

@app.route('/process_selected_dish2', methods=['POST'])
def process_selected_dish2():
    data = request.get_json()
    selected_dish_data = data.get('selectedDish')

    # Проверяем, существует ли запись для данного пользователя
    user_data = UserData3.query.filter_by(user_id=current_user.id).first()

    if user_data:
        # Обновляем существующую запись
        user_data.dish_data = selected_dish_data
    else:
        # Создаем новую запись
        user_data = UserData3(user_id=current_user.id, dish_data=selected_dish_data)
        db.session.add(user_data)

    db.session.commit()

    return jsonify({'message': 'Selected dish received successfully!'})

@app.route('/update_data', methods=['POST'])
def update_data():
    index = request.form.get('index')  # Получение данных из запроса
    # Ваш код для обновления данных, основанный на индексе
    # Отправьте обновленные данные в ответе
    return jsonify({"status": "success", "message": "Data updated successfully"})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

from flask import request, jsonify

@app.route('/update_water_glass', methods=['POST'])
def update_water_glass():
    data = request.get_json()
    glass_id = data.get('glassId')

    # Найдите соответствующий объект WaterGlass в базе данных и обновите его
    glass = WaterGlass.query.filter_by(id=glass_id, user_id=current_user.id).first()

    if glass and glass.index < 6:
        glass.index += 1
        db.session.commit()

        return jsonify({'message': 'Water glass updated successfully!'})
    else:
        return jsonify({'error': 'Unable to update water glass.'}), 400


if __name__ == '__main__':
    app.run(debug=True)