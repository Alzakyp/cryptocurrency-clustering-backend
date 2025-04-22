from models import db
from models.user import User
from flask_jwt_extended import create_access_token

class AuthService:
    @staticmethod
    def register_user(username, email, password, is_admin=False):
        if User.query.filter_by(username=username).first():
            return {'success': False, 'message': 'Username already exists'}, 400
        
        if User.query.filter_by(email=email).first():
            return {'success': False, 'message': 'Email already exists'}, 400
        
        new_user = User(username=username, email=email, is_admin=is_admin)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return {'success': True, 'message': 'User registered successfully'}, 201
    
    @staticmethod
    def login_user(username, password):
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return {'success': False, 'message': 'Invalid username or password'}, 401
        
        # For admin login, verify the user is an admin
        if not user.is_admin:
            return {'success': False, 'message': 'Access denied. Admin privileges required.'}, 403
            
        access_token = create_access_token(identity=user.id)
        
        return {
            'success': True,
            'access_token': access_token,
            'user': user.to_dict()
        }, 200
    
    @staticmethod
    def create_admin_if_not_exists():
        """Create a default admin user if no admin exists"""
        if not User.query.filter_by(is_admin=True).first():
            admin = User(
                username="admin",
                email="admin@example.com",
                is_admin=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            return True
        return False