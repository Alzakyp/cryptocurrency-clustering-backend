from models import db
from models.dataset import Dataset
from services.crypto_service import CryptoService
import io
import pandas as pd
import csv
import logging

logger = logging.getLogger(__name__)

class DatasetService:
    @staticmethod
    def get_all_datasets():
        """Get all datasets"""
        try:
            datasets = Dataset.query.all()
            return {
                'success': True,
                'datasets': [dataset.to_dict() for dataset in datasets]
            }, 200
        except Exception as e:
            logger.exception(f"Error retrieving datasets: {str(e)}")
            return {'success': False, 'message': f'Error retrieving datasets: {str(e)}'}, 500
    
    @staticmethod
    def get_dataset(dataset_id):
        """Get dataset by id"""
        try:
            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return {'success': False, 'message': 'Dataset not found'}, 404
                
            return {'success': True, 'dataset': dataset.to_dict()}, 200
        except Exception as e:
            logger.exception(f"Error retrieving dataset: {str(e)}")
            return {'success': False, 'message': f'Error retrieving dataset: {str(e)}'}, 500
    
    @staticmethod
    def upload_dataset(filename, file_content):
        """Upload new dataset"""
        try:
            # Validate CSV file
            try:
                # Decode content and handle different encodings
                try:
                    csv_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        csv_content = file_content.decode('latin-1')
                    except:
                        csv_content = file_content.decode('utf-8', errors='replace')
                
                csv_data = io.StringIO(csv_content)
                
                # Check if file uses semicolon as separator
                if ';' in csv_content[:1000]:
                    logger.debug("Detected semicolon separator")
                    df = pd.read_csv(csv_data, sep=';')
                else:
                    logger.debug("Using default comma separator")
                    df = pd.read_csv(csv_data)
                
                logger.debug(f"Successfully parsed CSV with {len(df)} rows")
            except Exception as e:
                logger.error(f"CSV validation error: {str(e)}")
                return {'success': False, 'message': f'Invalid CSV file: {str(e)}'}, 400
            
            # Create new dataset
            dataset = Dataset(
                filename=filename,
                content=file_content
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            # Automatically import cryptocurrencies from the dataset
            try:
                logger.debug(f"Auto-importing cryptocurrencies from dataset ID {dataset.id}")
                DatasetService.import_cryptocurrencies(dataset.id)
                import_message = " Data imported to crypto table."
            except Exception as e:
                logger.warning(f"Auto-import failed: {str(e)}")
                import_message = " (Warning: Auto-import to crypto table failed)"
            
            return {
                'success': True, 
                'message': f'Dataset uploaded successfully.{import_message}',
                'dataset': dataset.to_dict()
            }, 201
        except Exception as e:
            logger.exception(f"Error uploading dataset: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'Error uploading dataset: {str(e)}'}, 500
    
    @staticmethod
    def upload_dataset(filename, file_content):
        """Upload new dataset"""
        try:
        # Validate CSV file
            try:
            # Decode content and handle different encodings
                try:
                    csv_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        csv_content = file_content.decode('latin-1')
                    except:
                        csv_content = file_content.decode('utf-8', errors='replace')
            
                csv_data = io.StringIO(csv_content)
            
                if csv_content.startswith('\ufeff'):
                    csv_content = csv_content[1:]
                    csv_data = io.StringIO(csv_content)
            
                # Baca dengan pandas menggunakan delimiter yang terdeteksi
                if ';' in csv_content[:1000]:
                    df = pd.read_csv(csv_data, sep=';', on_bad_lines='skip')
                else:
                    df = pd.read_csv(csv_data, on_bad_lines='skip')
            
                logger.debug(f"Successfully parsed CSV with {len(df)} rows")
            except Exception as e:
                logger.error(f"CSV validation error: {str(e)}")
                return {'success': False, 'message': f'Invalid CSV file: {str(e)}'}, 400
        
            # Create new dataset
            dataset = Dataset(
                filename=filename,
                content=file_content
            )
        
            db.session.add(dataset)
            db.session.commit()
        
            # Automatically import cryptocurrencies from the dataset
            result, status_code = DatasetService.import_cryptocurrencies(dataset.id)
        
            try:
                result, status_code = DatasetService.import_cryptocurrencies(dataset.id)
                import_message = " and data imported to crypto table."
            except Exception as e:
                logger.warning(f"Auto-import failed: {str(e)}")
                import_message = " (Note: Auto-import to crypto table failed)"
        
            return {
                'success': True, 
                'message': 'Dataset uploaded successfully',
                'dataset': dataset.to_dict()
            }, 201
        except Exception as e:
            logger.exception(f"Error uploading dataset: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'Error uploading dataset: {str(e)}'}, 500
    
    @staticmethod
    def delete_dataset(dataset_id):
        """Delete dataset"""
        try:
            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return {'success': False, 'message': 'Dataset not found'}, 404
            
            db.session.delete(dataset)
            db.session.commit()
            
            return {'success': True, 'message': 'Dataset deleted successfully'}, 200
        except Exception as e:
            logger.exception(f"Error deleting dataset: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'Error deleting dataset: {str(e)}'}, 500
    
    @staticmethod
    def import_cryptocurrencies(dataset_id):
        """Import cryptocurrencies from dataset"""
        try:
            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return {'success': False, 'message': 'Dataset not found'}, 404
            
            if not dataset.content:
                return {'success': False, 'message': 'Dataset content is empty'}, 400
            
            # Import from CSV content with dataset_id
            result, status_code = CryptoService.import_from_csv(dataset.content, dataset_id)
            
            # Update dataset to show it's been processed
            db.session.commit()
            
            return result, status_code
        except Exception as e:
            logger.exception(f"Error importing cryptocurrencies from dataset: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'Error importing cryptocurrencies: {str(e)}'}, 500
    
    @staticmethod
    def get_dataset_content(dataset_id):
        """Get dataset content for download"""
        try:
            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return {'success': False, 'message': 'Dataset not found'}, 404
            
            if not dataset.content:
                return {'success': False, 'message': 'Dataset content is empty'}, 400
            
            return {
                'success': True,
                'content': dataset.content,
                'filename': dataset.filename,
                'content_type': 'text/csv'
            }, 200
        except Exception as e:
            logger.exception(f"Error retrieving dataset content: {str(e)}")
            return {'success': False, 'message': f'Error retrieving dataset content: {str(e)}'}, 500
    
    @staticmethod
    def preview_dataset(dataset_id):
        """Preview dataset content as JSON"""
        try:
            dataset = Dataset.query.get(dataset_id)
            if not dataset:
                return {'success': False, 'message': 'Dataset not found'}, 404
            
            if not dataset.content:
                return {'success': False, 'message': 'Dataset content is empty'}, 400
            
            # Parse CSV content
            try:
                # Handle different file encodings and separators
                try:
                    csv_content = dataset.content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        csv_content = dataset.content.decode('latin-1')
                    except:
                        csv_content = dataset.content.decode('utf-8', errors='replace')
                
                csv_data = io.StringIO(csv_content)
                
                # Check if file uses semicolon as separator
                if ';' in csv_content[:1000]:
                    df = pd.read_csv(csv_data, sep=';')
                else:
                    df = pd.read_csv(csv_data)
                
                # Get basic information
                columns = df.columns.tolist()
                row_count = len(df)
                
                # Get sample rows (max 10)
                sample_data = df.head(10).to_dict('records')
                
                return {
                    'success': True,
                    'filename': dataset.filename,
                    'columns': columns,
                    'row_count': row_count,
                    'sample_data': sample_data
                }, 200
            except Exception as e:
                return {'success': False, 'message': f'Error parsing CSV: {str(e)}'}, 500
        except Exception as e:
            logger.exception(f"Error previewing dataset: {str(e)}")
            return {'success': False, 'message': f'Error previewing dataset: {str(e)}'}, 500