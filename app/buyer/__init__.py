from app.buyer.auth_routes import auth_bp
from app.buyer.cart_routes import cart_bp
from app.buyer.negotiation_routes import negotiation_bp
from app.buyer.orders_routes import orders_bp
from app.buyer.products_routes import products_bp
from app.buyer.web_routes import buyer_web_bp
from app.buyer.wishlist_routes import wishlist_bp


BUYER_BLUEPRINTS = (
    (auth_bp, "/api"),
    (products_bp, "/api/products"),
    (cart_bp, "/api/cart"),
    (orders_bp, "/api/orders"),
    (negotiation_bp, "/api/negotiate"),
    (wishlist_bp, "/api/wishlist"),
    (buyer_web_bp, None),
)
