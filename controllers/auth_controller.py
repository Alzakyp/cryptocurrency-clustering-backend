from flask import request, jsonify
from services.auth_service import AuthService

class AuthController:
    @staticmethod
    def register():
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        is_admin = data.get('is_admin', False)
        
        if not all([username, email, password]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        result, status_code = AuthService.register_user(username, email, password, is_admin)
        return jsonify(result), status_code
    
    @staticmethod
    def login():
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        result, status_code = AuthService.login_user(username, password)
        return jsonify(result), status_code