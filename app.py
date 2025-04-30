import logging
from decimal import Decimal

import pymysql
from flask import Flask, jsonify, request
from flask.json import JSONEncoder
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate


# Custom JSON Encoder untuk mengatasi masalah Decimal
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Konversi Decimal ke float
            return float(obj)
        return super().default(obj)


# Setup logging globally
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use pymysql as MySQLdb
pymysql.install_as_MySQLdb()

from config import Config
from models import db
from routes.auth_routes import auth_bp
from routes.crypto_routes import crypto_bp
from routes.dataset_routes import dataset_bp  # Import dataset routes
from services.auth_service import AuthService


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder

    # Configure CORS properly - IMPORTANT CHANGE HERE
    CORS(
        app,
        supports_credentials=True,  # Add this for credentials support
        origins=["http://localhost:3000"],  # Explicitly list allowed origins
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Add explicit OPTIONS handler for all routes
    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def options_handler(path):
        response = app.make_default_options_response()
        return response

    # Add after_request handler to ensure CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(crypto_bp, url_prefix="/api/crypto")
    app.register_blueprint(
        dataset_bp, url_prefix="/api/datasets"
    )  # Register dataset routes
    app.register_blueprint(dataset_bp, url_prefix="/api/dataset")

    # Rest of your routes...

    return app


if __name__ == "__main__":
    app = create_app()

    # Create default admin user if none exists
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        if AuthService.create_admin_if_not_exists():
            print("Default admin user created with username: admin, password: admin123")

    app.run(debug=True)
