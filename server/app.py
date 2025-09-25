#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
from sqlalchemy.exc import IntegrityError
import os

# Define the base directory and database URI
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

# Create the Flask application
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

# Initialize database migration and API
migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)


# Define a custom home route using Flask-RESTful Resource
class Home(Resource):
    def get(self):
        return make_response(jsonify({"message": "Welcome to the Pizza Restaurant API!"}), 200)

api.add_resource(Home, "/")


# Route to get all restaurants
class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        restaurant_list = [r.to_dict(rules=('-restaurant_pizzas',)) for r in restaurants]
        return make_response(jsonify(restaurant_list), 200)

api.add_resource(Restaurants, "/restaurants")


# Route to get and delete a specific restaurant by ID
class RestaurantById(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        # Serialize the restaurant and its associated pizzas
        restaurant_data = restaurant.to_dict(rules=('-restaurant_pizzas.restaurant',))
        return make_response(jsonify(restaurant_data), 200)

    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        db.session.delete(restaurant)
        db.session.commit()
        
        return make_response("", 204)

api.add_resource(RestaurantById, "/restaurants/<int:id>")


# Route to get all pizzas
class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        pizza_list = [p.to_dict(rules=('-restaurant_pizzas',)) for p in pizzas]
        return make_response(jsonify(pizza_list), 200)

api.add_resource(Pizzas, "/pizzas")


# Route to create a new RestaurantPizza entry
class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        
        # Check if the required fields are in the request
        if "price" not in data or "pizza_id" not in data or "restaurant_id" not in data:
            return make_response(jsonify({"errors": ["validation errors"]}), 400)
        
        # Use a try-except block to handle validation errors
        try:
            # Check if restaurant and pizza exist
            restaurant = Restaurant.query.filter_by(id=data["restaurant_id"]).first()
            pizza = Pizza.query.filter_by(id=data["pizza_id"]).first()

            if not restaurant or not pizza:
                return make_response(jsonify({"errors": ["validation errors"]}), 400)
            
            # Create new RestaurantPizza instance
            new_rp = RestaurantPizza(
                price=data["price"],
                pizza_id=data["pizza_id"],
                restaurant_id=data["restaurant_id"]
            )
            
            # Add to the session and commit
            db.session.add(new_rp)
            db.session.commit()

            # Return the newly created object with its relationships
            response_data = new_rp.to_dict(rules=('-restaurant.restaurant_pizzas', '-pizza.restaurant_pizzas'))
            return make_response(jsonify(response_data), 201)

        except (ValueError, IntegrityError) as e:
            # Rollback the session in case of a database error
            db.session.rollback()
            return make_response(jsonify({"errors": ["validation errors"]}), 400)

api.add_resource(RestaurantPizzas, "/restaurant_pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
