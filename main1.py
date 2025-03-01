from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Здесь нужно предоставить данные о товарах
    all_products = [
        {'name': 'Товар 1', 'price': 10},
        {'name': 'Товар 2', 'price': 20},
        # Добавьте другие товары
    ]

    favorite_products = [
        {'name': 'Избранный товар 1', 'price': 15},
        # Добавьте другие избранные товары
    ]

    return render_template('index.html', all_products=all_products, favorite_products=favorite_products)

if __name__ == 'main':
    app.run(debug=True)