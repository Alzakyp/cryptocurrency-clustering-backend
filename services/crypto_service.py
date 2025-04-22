from models import db
from models.cryptocurrency import Cryptocurrency
import pandas as pd
import io
import csv
import logging

# Setup logging
logger = logging.getLogger(__name__)

class CryptoService:
    @staticmethod
    def get_all_cryptocurrencies():
        cryptocurrencies = Cryptocurrency.query.all()
        return {'cryptocurrencies': [crypto.to_dict() for crypto in cryptocurrencies]}, 200

    @staticmethod
    def get_cryptocurrency(crypto_id):
        crypto = Cryptocurrency.query.get(crypto_id)
        if not crypto:
            return {'success': False, 'message': 'Cryptocurrency not found'}, 404

        return {'cryptocurrency': crypto.to_dict()}, 200

    @staticmethod
    def create_cryptocurrency(data):
        new_crypto = Cryptocurrency(
            symbol=data.get('symbol'),
            name=data.get('name'),
            price=data.get('price'),
            price_change_24h=data.get('price_change_24h'),
            percent_change_24h=data.get('percent_change_24h'),
            market_cap=data.get('market_cap'),
            volume_24h=data.get('volume_24h'),
            circulating_supply=data.get('circulating_supply')
        )

        db.session.add(new_crypto)
        db.session.commit()

        return {'success': True, 'cryptocurrency': new_crypto.to_dict()}, 201

    @staticmethod
    def update_cryptocurrency(crypto_id, data):
        crypto = Cryptocurrency.query.get(crypto_id)
        if not crypto:
            return {'success': False, 'message': 'Cryptocurrency not found'}, 404

        for key, value in data.items():
            if hasattr(crypto, key):
                setattr(crypto, key, value)

        db.session.commit()

        return {'success': True, 'cryptocurrency': crypto.to_dict()}, 200

    @staticmethod
    def delete_cryptocurrency(crypto_id):
        crypto = Cryptocurrency.query.get(crypto_id)
        if not crypto:
            return {'success': False, 'message': 'Cryptocurrency not found'}, 404

        db.session.delete(crypto)
        db.session.commit()

        return {'success': True, 'message': 'Cryptocurrency deleted successfully'}, 200

    @staticmethod
    def import_from_csv(file_content):
        """Import cryptocurrency data from CSV file"""
        logger.debug("=== Starting CSV import process ===")

        try:
            logger.debug(f"Decoding CSV content, length: {len(file_content)} bytes")
            csv_data = io.StringIO(file_content.decode('utf-8'))

            logger.debug("Parsing CSV with pandas")
            df = pd.read_csv(csv_data, sep=';')
        
            logger.debug(f"Original CSV columns: {df.columns.tolist()}")
            df.columns = [col.strip() for col in df.columns]

            required_columns = ['Symbol', 'Name', 'Price']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return {'success': False, 'message': f'Missing required column: {col}'}, 400

            # Fungsi untuk membersihkan nilai numerik
            def clean_numeric(value):
                if pd.isna(value):
                    return None
            
                if not isinstance(value, str):
                    return value
                
                # Menghapus koma pemisah ribuan
                value = str(value).replace(',', '')
            
                # Menangani suffix B, M, K
                if value.endswith('B'):
                    value = float(value[:-1]) * 1_000_000_000
                elif value.endswith('M'):
                    value = float(value[:-1]) * 1_000_000
                elif value.endswith('K'):
                    value = float(value[:-1]) * 1_000
            
                try:
                    return float(value)
                except:
                    return None

            success_count = 0
            error_rows = []

            for idx, row in df.iterrows():
                try:
                    logger.debug(f"Processing row {idx}: {row['Symbol']}")

                    crypto = Cryptocurrency.query.filter_by(symbol=row['Symbol']).first()

                    # Bersihkan dan konversi nilai numerik
                    crypto_data = {
                        'symbol': row['Symbol'],
                        'name': row['Name'],
                        'price': clean_numeric(row['Price']),
                        'price_change_24h': clean_numeric(row['Change']) if 'Change' in row else None,
                        'percent_change_24h': clean_numeric(row['% Change']) if '% Change' in row else None,
                        'market_cap': clean_numeric(row['Market Cap']) if 'Market Cap' in row else None,
                        'volume_24h': clean_numeric(row['Volume in Currency (24Hr)']) if 'Volume in Currency (24Hr)' in row else None,
                        'circulating_supply': clean_numeric(row['Circulating Supply']) if 'Circulating Supply' in row else None
                }

                    if crypto:
                        for key, value in crypto_data.items():
                            setattr(crypto, key, value)
                    else:
                        crypto = Cryptocurrency(**crypto_data)
                        db.session.add(crypto)

                    success_count += 1

                except Exception as e:
                    error_rows.append({'row': idx, 'symbol': row.get('Symbol'), 'error': str(e)})
                    logger.exception(f"Error processing row {idx}: {str(e)}")

            if error_rows:
                logger.warning(f"Errors in {len(error_rows)} rows: {error_rows}")

            db.session.commit()
            return {'success': True, 'message': f'Successfully imported {success_count} cryptocurrencies'}, 200

        except Exception as e:
            logger.exception(f"Error during CSV import: {str(e)}")
            db.session.rollback()
            return {'success': False, 'message': f'Error importing CSV: {str(e)}'}, 500

    @staticmethod
    def export_to_csv():
        """Export all cryptocurrency data to CSV"""
        try:
            cryptocurrencies = Cryptocurrency.query.all()

            if not cryptocurrencies:
                return {'success': False, 'message': 'No cryptocurrency data to export'}, 404

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(['id', 'symbol', 'name', 'price', 'price_change_24h', 'percent_change_24h',
                             'market_cap', 'volume_24h', 'circulating_supply', 'cluster'])

            for crypto in cryptocurrencies:
                writer.writerow([
                    crypto.id,
                    crypto.symbol,
                    crypto.name,
                    crypto.price,
                    crypto.price_change_24h,
                    crypto.percent_change_24h,
                    crypto.market_cap,
                    crypto.volume_24h,
                    crypto.circulating_supply,
                    crypto.cluster
                ])

            return output.getvalue(), 200

        except Exception as e:
            logger.exception(f"Error exporting CSV: {str(e)}")
            return {'success': False, 'message': f'Error exporting CSV: {str(e)}'}, 500
