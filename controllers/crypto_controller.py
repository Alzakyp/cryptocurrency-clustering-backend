from flask import request, jsonify, make_response
from services.crypto_service import CryptoService
import io
import logging

# Setup logging
logger = logging.getLogger(__name__)

class CryptoController:
    @staticmethod
    def get_all():
        """Get all cryptocurrencies or filter by dataset_id if provided"""
        # Check for dataset_id query parameter
        dataset_id = request.args.get('dataset_id')
    
        if dataset_id:
            try:
                dataset_id = int(dataset_id)
                result, status_code = CryptoService.get_cryptocurrencies_by_dataset(dataset_id)
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid dataset_id parameter'}), 400
        else:
            result, status_code = CryptoService.get_all_cryptocurrencies()
    
        return jsonify(result), status_code
    
    @staticmethod
    def get_one(crypto_id):
        result, status_code = CryptoService.get_cryptocurrency(crypto_id)
        return jsonify(result), status_code
    
    @staticmethod
    def create():
        data = request.get_json()
        
        required_fields = ['symbol', 'name', 'price']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        result, status_code = CryptoService.create_cryptocurrency(data)
        return jsonify(result), status_code
    
    @staticmethod
    def update(crypto_id):
        data = request.get_json()
        
        result, status_code = CryptoService.update_cryptocurrency(crypto_id, data)
        return jsonify(result), status_code
    
    @staticmethod
    def delete(crypto_id):
        result, status_code = CryptoService.delete_cryptocurrency(crypto_id)
        return jsonify(result), status_code
    
    @staticmethod
    def import_csv():
        logger.debug("=== CSV Import Request ===")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Form Data: {request.form}")
        logger.debug(f"Files: {list(request.files.keys())}")
        logger.debug(f"Request JSON (if any): {request.get_json(silent=True)}")
        
        # Check if file is in request
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'success': False, 'message': 'No file part'}), 400
            
        file = request.files['file']
        logger.debug(f"File name: {file.filename}")
        logger.debug(f"File content type: {file.content_type}")
        
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'success': False, 'message': 'No selected file'}), 400
            
        if file and file.filename.endswith('.csv'):
            logger.debug(f"Reading file content for {file.filename}")
            file_content = file.read()
            logger.debug(f"File content length: {len(file_content)} bytes")
            
            try:
                result, status_code = CryptoService.import_from_csv(file_content)
                logger.debug(f"Import result: {result}, status code: {status_code}")
                return jsonify(result), status_code
            except Exception as e:
                logger.exception(f"Exception during CSV import: {str(e)}")
                return jsonify({'success': False, 'message': f'Error processing CSV: {str(e)}'}), 500
        else:
            logger.error(f"Invalid file format: {file.filename}")
            return jsonify({'success': False, 'message': 'Invalid file format. Please upload a CSV file.'}), 400
    
    @staticmethod
    def export_csv():
        result, status_code = CryptoService.export_to_csv()
        
        if status_code == 200:
            response = make_response(result)
            response.headers["Content-Disposition"] = "attachment; filename=cryptocurrencies.csv"
            response.headers["Content-type"] = "text/csv"
            return response
        else:
            return jsonify(result), status_code