from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
import pymysql
import logging
from decimal import Decimal
from flask.json import JSONEncoder

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
from services.auth_service import AuthService

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    # Initialize extensions
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Welcome to Cryptocurrency Clustering API'})
    
    @app.route('/db-test')
    def db_test():
        try:
            # Try to execute a simple query
            result = db.session.execute('SELECT 1').fetchone()
            if result:
                return jsonify({'message': 'Database connected successfully!'})
            else:
                return jsonify({'error': 'Unknown database error'}), 500
        except Exception as e:
            return jsonify({'error': f'Database connection failed: {str(e)}'}), 500
    
    @app.route('/test-upload', methods=['POST'])
    def test_upload():
        print("Headers:", dict(request.headers))
        print("Form:", request.form)
        print("Files:", request.files)
        
        if 'file' in request.files:
            file = request.files['file']
            return jsonify({
                'success': True,
                'filename': file.filename,
                'content_type': file.content_type,
                'form_data': {k: v for k, v in request.form.items()}
            })
        return jsonify({'success': False, 'message': 'No file received'})

    @app.route('/api/crypto/direct-import', methods=['POST'])
    def direct_import():
        from services.crypto_service import CryptoService
        
        print("Headers:", dict(request.headers))
        print("Form:", request.form)
        print("Files:", request.files)
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'File tidak ditemukan'})
            
        file = request.files['file']
        file_content = file.read()
        
        try:
            result, status_code = CryptoService.import_from_csv(file_content)
            return jsonify(result), status_code
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create default admin user if none exists
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        if AuthService.create_admin_if_not_exists():
            print("Default admin user created with username: admin, password: admin123")
    
    app.run(debug=True)