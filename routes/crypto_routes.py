from flask import Blueprint
from controllers.crypto_controller import CryptoController
from flask_jwt_extended import jwt_required

crypto_bp = Blueprint('crypto', __name__)

crypto_bp.route('/', methods=['GET'])(CryptoController.get_all)
crypto_bp.route('/<int:crypto_id>', methods=['GET'])(CryptoController.get_one)
crypto_bp.route('/', methods=['POST'])(jwt_required()(CryptoController.create))
crypto_bp.route('/<int:crypto_id>', methods=['PUT'])(jwt_required()(CryptoController.update))
crypto_bp.route('/<int:crypto_id>', methods=['DELETE'])(jwt_required()(CryptoController.delete))
crypto_bp.route('/import', methods=['POST'])(jwt_required()(CryptoController.import_csv))
crypto_bp.route('/export', methods=['GET'])(jwt_required()(CryptoController.export_csv))  