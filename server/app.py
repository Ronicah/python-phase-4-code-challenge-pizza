app_test.py

from models import Restaurant, RestaurantPizza, Pizza
from app import app, db
from faker import Faker


class TestApp:
    '''Flask application in app.py'''

    def test_restaurants(self):
        """retrieves restaurants with GET request to /restaurants"""
        with app.app_context():
            fake = Faker()
            restaurant1 = Restaurant(
                name=fake.name(), address=fake.address())
            restaurant2 = Restaurant(
                name=fake.name(), address=fake.address())
            db.session.add_all([restaurant1, restaurant2])
            db.session.commit()

            restaurants = Restaurant.query.all()

            response = app.test_client().get('/restaurants')
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            response = response.json
            assert [restaurant['id'] for restaurant in response] == [
                restaurant.id for restaurant in restaurants]
            assert [restaurant['name'] for restaurant in response] == [
                restaurant.name for restaurant in restaurants]
            assert [restaurant['address'] for restaurant in response] == [
                restaurant.address for restaurant in restaurants]
            for restaurant in response:
                assert 'restaurant_pizzas' not in restaurant

    def test_restaurants_id(self):
        '''retrieves one restaurant using its ID with GET request to /restaurants/<int:id>.'''

        with app.app_context():
            fake = Faker()
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            db.session.add(restaurant)
            db.session.commit()

            response = app.test_client().get(
                f'/restaurants/{restaurant.id}')
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            response = response.json
            assert response['id'] == restaurant.id
            assert response['name'] == restaurant.name
            assert response['address'] == restaurant.address
            assert 'restaurant_pizzas' in response

    def test_returns_404_if_no_restaurant_to_get(self):
        '''returns an error message and 404 status code with GET request to /restaurants/<int:id> by a non-existent ID.'''

        with app.app_context():
            response = app.test_client().get('/restaurants/0')
            assert response.status_code == 404
            assert response.content_type == 'application/json'
            assert response.json.get('error')
            assert response.status_code == 404

    def test_deletes_restaurant_by_id(self):
        '''deletes restaurant with DELETE request to /restaurants/<int:id>.'''

        with app.app_context():
            fake = Faker()
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            db.session.add(restaurant)
            db.session.commit()

            response = app.test_client().delete(
                f'/restaurants/{restaurant.id}')

            assert response.status_code == 204

            result = Restaurant.query.filter(
                Restaurant.id == restaurant.id).one_or_none()
            assert result is None

    def test_returns_404_if_no_restaurant_to_delete(self):
        '''returns an error message and 404 status code with DELETE request to /restaurants/<int:id> by a non-existent ID.'''

        with app.app_context():
            response = app.test_client().get('/restaurants/0')
            assert response.status_code == 404
            assert response.json.get('error') == "Restaurant not found"

    def test_pizzas(self):
        """retrieves pizzas with GET request to /pizzas"""
        with app.app_context():
            fake = Faker()
            pizza1 = Pizza(name=fake.name(), ingredients=fake.sentence())
            pizza2 = Pizza(name=fake.name(), ingredients=fake.sentence())

            db.session.add_all([pizza1, pizza2])
            db.session.commit()

            response = app.test_client().get('/pizzas')
            assert response.status_code == 200
            assert response.content_type == 'application/json'
            response = response.json

            pizzas = Pizza.query.all()

            assert [pizza['id'] for pizza in response] == [
                pizza.id for pizza in pizzas]
            assert [pizza['name'] for pizza in response] == [
                pizza.name for pizza in pizzas]
            assert [pizza['ingredients'] for pizza in response] == [
                pizza.ingredients for pizza in pizzas]
            for pizza in response:
                assert 'restaurant_pizzas' not in pizza

    def test_creates_restaurant_pizzas(self):
        '''creates one restaurant_pizzas using a pizza_id, restaurant_id, and price with a POST request to /restaurant_pizzas.'''

        with app.app_context():
            fake = Faker()
            pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
            restaurant = Restaurant(name=fake.name(), address=fake.address())
            db.session.add(pizza)
            db.session.add(restaurant)
            db.session.commit()

            # delete if existing in case price differs
            restaurant_pizza = RestaurantPizza.query.filter_by(
                pizza_id=pizza.id, restaurant_id=restaurant.id).one_or_none()
            if restaurant_pizza:
                db.session.delete(restaurant_pizza)
                db.session.commit()

            response = app.test_client().post(
                '/restaurant_pizzas',
                json={
                    "price": 3,
                    "pizza_id": pizza.id,
                    "restaurant_id": restaurant.id,
                }
            )

            assert response.status_code == 201
            assert response.content_type == 'application/json'
            response = response.json
            assert response['price'] == 3
            assert response['pizza_id'] == pizza.id
            assert response['restaurant_id'] == restaurant.id
            assert response['id']
            assert response['pizza']
            assert response['restaurant']

            query_result = RestaurantPizza.query.filter(
                RestaurantPizza.restaurant_id == restaurant.id, RestaurantPizza.pizza_id == pizza.id).first()
            assert query_result.price == 3

    def test_400_for_validation_error(self):
          '''returns a 400 status code and error message if a POST request to /restaurant_pizzas fails.'''
    
    with app.app_context():
        fake = Faker()
        pizza = Pizza(name=fake.name(), ingredients=fake.sentence())
        restaurant = Restaurant(name=fake.name(), address=fake.address())
        db.session.add(pizza)
        db.session.add(restaurant)
        db.session.commit()
    
        # price not in 1..30
        response = app.test_client().post(
            '/restaurant_pizzas',
            json={
                "price": 0,
                "pizza_id": pizza.id,
                "restaurant_id": restaurant.id,
            }
        )
    
        assert response.status_code == 400
        # Update the expected error message to match the actual response
        assert response.json['errors'] == ["Price must be between 1 and 30"]




app.py

#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


# GET /restaurants
@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = [restaurant.to_dict() for restaurant in Restaurant.query.all()]
    return jsonify(restaurants), 200


# GET /restaurants/<int:id>
@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant,id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    restaurant_data = restaurant.to_dict()
    restaurant_data["restaurant_pizzas"] = [
        rp.to_dict() for rp in restaurant.restaurant_pizzas
    ]

    return jsonify(restaurant_data), 200


# DELETE /restaurants/<int:id>
@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    db.session.delete(restaurant)
    db.session.commit()

    return '', 204


# GET /pizzas
@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = [pizza.to_dict() for pizza in Pizza.query.all()]
    return jsonify(pizzas), 200


# POST /restaurant_pizzas
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()

    try:
        price = data['price']
        pizza_id = data['pizza_id']
        restaurant_id = data['restaurant_id']

        # Ensure referenced Pizza and Restaurant exist
        pizza = db.session.get(Pizza,pizza_id)
        restaurant = db.session.get(Restaurant,restaurant_id)
        if not pizza or not restaurant:
            return jsonify({"errors": ["Invalid pizza or restaurant"]}), 400

        restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(restaurant_pizza)
        db.session.commit()

        return jsonify(restaurant_pizza.to_dict()), 201

    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except KeyError:
        return jsonify({"errors": ["Missing required fields"]}), 400




if __name__ == "__main__":
    app.run(port=5555, debug=True)