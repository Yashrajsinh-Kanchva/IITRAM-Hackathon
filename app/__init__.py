import time
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.admin.routes import admin_bp
from app.buyer import BUYER_BLUEPRINTS
from app.cli import register_commands
from app.config import CONFIG_BY_NAME
from app.extensions import csrf
from app.farmer.portal_routes import farmer_portal_bp, farmer_public_api_bp
from app.farmer.routes import farmer_bp
from app.offers.routes import offers_bp
from app.repositories.schema import ensure_database_structure

load_dotenv()


def _resolve_db_name(app):
    configured = app.config.get("DATABASE_NAME")
    if configured:
        return configured

    parsed = urlparse(app.config["MONGO_URI"])
    name_from_uri = (parsed.path or "").strip("/")
    return name_from_uri or "farm_to_market"


def _connect_mongo_with_retry(app):
    explicit_client = app.config.get("MONGO_CLIENT")
    if explicit_client is not None:
        return explicit_client

    retries = max(1, int(app.config.get("MONGO_CONNECT_RETRIES", 2)))
    timeout_ms = max(1000, int(app.config.get("MONGO_SERVER_SELECTION_TIMEOUT_MS", 8000)))
    primary_uri = app.config["MONGO_URI"]
    fallback_uri = (app.config.get("MONGO_FALLBACK_URI") or "").strip()
    targets = [("primary", primary_uri)]
    if fallback_uri and fallback_uri != primary_uri:
        targets.append(("fallback", fallback_uri))

    errors = []
    for label, uri in targets:
        for attempt in range(1, retries + 1):
            try:
                client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=timeout_ms,
                    connectTimeoutMS=timeout_ms,
                    socketTimeoutMS=timeout_ms,
                )
                client.admin.command("ping")
                if label == "fallback":
                    app.logger.warning(
                        "Connected using MONGO_FALLBACK_URI because primary MONGO_URI failed."
                    )
                return client
            except PyMongoError as exc:
                errors.append(f"{label} attempt {attempt}/{retries}: {exc}")
                if attempt < retries:
                    time.sleep(min(1.2 * attempt, 3.0))

    hint = (
        "MongoDB connection failed. Check DNS/network access to Atlas, verify IP allowlist, "
        "or set MONGO_FALLBACK_URI (for example mongodb://127.0.0.1:27017/farm_to_market). "
        "You can also retry after a few seconds when SRV DNS fails intermittently."
    )
    if errors:
        hint = f"{hint}\nLast error: {errors[-1]}"
    raise RuntimeError(hint)


def create_app(config_name=None, test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.from_mapping(test_config)
    else:
        env = config_name or "development"
        app.config.from_object(CONFIG_BY_NAME.get(env, CONFIG_BY_NAME["development"]))

    if app.config.get("DEBUG"):
        app.config["SESSION_COOKIE_SECURE"] = False

    csrf.init_app(app)

    mongo_client = _connect_mongo_with_retry(app)
    app.mongo_client = mongo_client
    app.db = mongo_client[_resolve_db_name(app)]

    ensure_database_structure(app.db, apply_validators=True)

    register_commands(app)
    app.register_blueprint(admin_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(farmer_portal_bp)
    app.register_blueprint(farmer_public_api_bp)
    csrf.exempt(farmer_portal_bp)
    for blueprint, prefix in BUYER_BLUEPRINTS:
        if prefix:
            app.register_blueprint(blueprint, url_prefix=prefix)
        else:
            app.register_blueprint(blueprint)
        if prefix and prefix.startswith("/api"):
            csrf.exempt(blueprint)

    @app.get("/")
    def healthcheck():
        return jsonify({"status": "ok", "service": "farm-to-market-admin"})

    @app.get("/login")
    def unified_login():
        return render_template("login_selector.html")

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def handle_http_errors(error):
        wants_json = (
            request.path.startswith("/admin/api")
            or request.path.startswith("/api")
            or request.path.startswith("/offers")
            or request.path.startswith("/farmer/api")
            or request.accept_mimetypes.best == "application/json"
        )
        code = getattr(error, "code", 500)
        description = getattr(error, "description", "Unexpected error")
        if wants_json:
            return jsonify({"error": description, "status": code}), code
        return render_template("admin/error.html", code=code, message=description), code

    return app
