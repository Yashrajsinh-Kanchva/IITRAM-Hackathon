import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from buyer.routes.auth import auth_bp
from buyer.routes.products import products_bp
from buyer.routes.cart import cart_bp
from buyer.routes.orders import orders_bp
from buyer.routes.negotiation import negotiation_bp
from buyer.routes.wishlist import wishlist_bp

def create_app():
    # Set static_folder to the frontend directory relative to this script
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'buyer'))
    app = Flask(__name__, static_folder=frontend_dir)
    CORS(app) 

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(negotiation_bp, url_prefix='/api/negotiate')
    app.register_blueprint(wishlist_bp, url_prefix='/api/wishlist')

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_proxy(path):
        return send_from_directory(app.static_folder, path)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
