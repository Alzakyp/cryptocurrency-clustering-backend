import codecs
import csv
import io
import logging

import pandas as pd

from models import db
from models.cryptocurrency import Cryptocurrency

# Setup logging
logger = logging.getLogger(__name__)


class CryptoService:
    @staticmethod
    def get_all_cryptocurrencies():
        cryptocurrencies = Cryptocurrency.query.all()
        return {
            "cryptocurrencies": [crypto.to_dict() for crypto in cryptocurrencies]
        }, 200

    @staticmethod
    def get_cryptocurrency(crypto_id):
        crypto = Cryptocurrency.query.get(crypto_id)
        if not crypto:
            return {"success": False, "message": "Cryptocurrency not found"}, 404

        return {"cryptocurrency": crypto.to_dict()}, 200

    @staticmethod
    def get_cryptocurrencies_by_dataset(dataset_id):
        """Get cryptocurrencies filtered by dataset ID"""
        try:
            cryptocurrencies = Cryptocurrency.query.filter_by(dataset_id=dataset_id).all()
            return {
                "cryptocurrencies": [crypto.to_dict() for crypto in cryptocurrencies],
                "success": True,
                "count": len(cryptocurrencies)
            }, 200
        except Exception as e:
            logger.exception(f"Error retrieving cryptocurrencies for dataset {dataset_id}: {str(e)}")
            return {"success": False, "message": f"Error retrieving cryptocurrencies: {str(e)}"}, 500

    @staticmethod
    def create_cryptocurrency(data):
        new_crypto = Cryptocurrency(
            symbol=data.get("symbol"),
            name=data.get("name"),
            price=data.get("price"),
            price_change_24h=data.get("price_change_24h"),
            percent_change_24h=data.get("percent_change_24h"),
            market_cap=data.get("market_cap"),
            volume_24h=data.get("volume_24h"),
            circulating_supply=data.get("circulating_supply"),
            dataset_id=data.get("dataset_id"),
        )

        db.session.add(new_crypto)
        db.session.commit()

        return {"success": True, "cryptocurrency": new_crypto.to_dict()}, 201

    @staticmethod
    def update_cryptocurrency(crypto_id, data):
        crypto = Cryptocurrency.query.get(crypto_id)
        if not crypto:
            return {"success": False, "message": "Cryptocurrency not found"}, 404

        for key, value in data.items():
            if hasattr(crypto, key):
                setattr(crypto, key, value)

        db.session.commit()

        return {"success": True, "cryptocurrency": crypto.to_dict()}, 200

    @staticmethod
    def delete_cryptocurrency(crypto_id):
        crypto = Cryptocurrency.query.get(crypto_id)
        if not crypto:
            return {"success": False, "message": "Cryptocurrency not found"}, 404

        db.session.delete(crypto)
        db.session.commit()

        return {"success": True, "message": "Cryptocurrency deleted successfully"}, 200

    @staticmethod
    def import_from_csv(file_content, dataset_id=None):
        """Import cryptocurrency data from CSV file"""
        logger.debug("=== Starting CSV import process ===")

        try:
            # Decode content and handle different encodings
            try:
                csv_content = file_content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    csv_content = file_content.decode("latin-1")
                except:
                    csv_content = file_content.decode("utf-8", errors="replace")

            # Create StringIO object from content
            csv_data = io.StringIO(csv_content)

            # Detect and remove BOM (Byte Order Mark) if present
            if csv_content.startswith("\ufeff"):
                csv_content = csv_content[1:]
                csv_data = io.StringIO(csv_content)

            # Parse CSV with pandas using semicolon separator
            try:
                df = pd.read_csv(csv_data, sep=";", on_bad_lines="skip")
                logger.debug(
                    f"Successfully parsed CSV with separator ';' - {len(df)} rows"
                )
            except Exception as e:
                logger.error(f"Error parsing CSV with semicolon: {str(e)}")
                return {
                    "success": False,
                    "message": f"Failed to parse CSV file: {str(e)}",
                }, 400

            # Log columns found
            logger.debug(f"Found CSV columns: {df.columns.tolist()}")

            # Map columns from CSV to cryptocurrency model columns
            column_mapping = {
                "symbol": "Symbol",
                "name": "Name",
                "price": "Price (Intraday)",  # Changed from 'Price' to 'Price (Intraday)'
                "price_change_24h": "Change",
                "percent_change_24h": "% Change",
                "market_cap": "Market Cap",
                "volume_24h": "Volume in Currency (24Hr)",
                "circulating_supply": "Circulating Supply",
            }

            # Verify required columns
            required_columns = ["Symbol", "Name", "Price (Intraday)"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                error_msg = f"Missing required column(s): {', '.join(missing_columns)}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}, 400

            # Delete existing cryptocurrencies linked to this dataset
            if dataset_id:
                old_records = Cryptocurrency.query.filter_by(
                    dataset_id=dataset_id
                ).all()
                for record in old_records:
                    db.session.delete(record)

            # Function to clean numeric values
            def clean_numeric(value):
                if pd.isna(value):
                    return None

                if not isinstance(value, (int, float)):
                    value_str = str(value)

                    # Replace comma with dot for European decimal format
                    if "," in value_str and "." not in value_str:
                        value_str = value_str.replace(",", ".")
                    elif "," in value_str and "." in value_str:
                        # Handle European number format with thousands: 1.234,56
                        value_str = value_str.replace(".", "").replace(",", ".")

                    # Handle suffixes (B=Billion, M=Million, K=Thousand, T=Trillion)
                    try:
                        if value_str.endswith("B"):
                            return float(value_str[:-1]) * 1_000_000_000
                        elif value_str.endswith("M"):
                            return float(value_str[:-1]) * 1_000_000
                        elif value_str.endswith("K"):
                            return float(value_str[:-1]) * 1_000
                        elif value_str.endswith("T"):
                            return float(value_str[:-1]) * 1_000_000_000_000
                        else:
                            return float(value_str)
                    except ValueError:
                        logger.warning(
                            f"Could not convert value to number: {value_str}"
                        )
                        return None

                return value

            # Process rows
            success_count = 0
            error_rows = []

            for idx, row in df.iterrows():
                try:
                    # Skip rows with missing required values
                    if (
                        pd.isna(row["Symbol"])
                        or pd.isna(row["Name"])
                        or pd.isna(row["Price (Intraday)"])
                    ):
                        logger.warning(f"Row {idx} skipped: Missing required values")
                        error_rows.append(
                            {
                                "row": idx,
                                "error": "Missing required values (Symbol, Name, or Price)",
                                "symbol": row.get("Symbol", "Unknown"),
                            }
                        )
                        continue

                    logger.debug(f"Processing row {idx}: {row['Symbol']}")

                    # Find cryptocurrency by symbol and dataset_id
                    query = Cryptocurrency.query
                    if dataset_id:
                        query = query.filter_by(
                            symbol=row["Symbol"], dataset_id=dataset_id
                        )
                    else:
                        query = query.filter_by(symbol=row["Symbol"])

                    crypto = query.first()

                    # Create cryptocurrency data
                    crypto_data = {
                        "symbol": row["Symbol"],
                        "name": row["Name"],
                        "price": clean_numeric(row["Price (Intraday)"]),
                        "dataset_id": dataset_id,
                    }

                    # Add other fields if columns exist in the CSV
                    for model_col, csv_col in column_mapping.items():
                        # Skip symbol, name, price (already handled), and dataset_id
                        if model_col in ["symbol", "name", "price", "dataset_id"]:
                            continue

                        if csv_col in df.columns:
                            crypto_data[model_col] = clean_numeric(row[csv_col])

                    # Update or create cryptocurrency
                    if crypto:
                        logger.debug(
                            f"Updating existing cryptocurrency: {row['Symbol']}"
                        )
                        for key, value in crypto_data.items():
                            setattr(crypto, key, value)
                    else:
                        logger.debug(f"Creating new cryptocurrency: {row['Symbol']}")
                        crypto = Cryptocurrency(**crypto_data)
                        db.session.add(crypto)

                    success_count += 1

                except Exception as e:
                    error_rows.append(
                        {
                            "row": idx,
                            "symbol": row.get("Symbol", "Unknown"),
                            "error": str(e),
                        }
                    )
                    logger.exception(f"Error processing row {idx}: {str(e)}")

            # Commit changes
            db.session.commit()

            # Generate response
            if success_count == 0:
                # Get the most common errors (up to 3)
                error_examples = error_rows[:3] if error_rows else []
                error_messages = []

                # Check for missing required columns
                for column in required_columns:
                    if column not in df.columns:
                        error_messages.append(f"Missing required column: '{column}'")

                # Check for data type or missing value errors in the examples
                if error_examples:
                    error_messages.append("Sample error rows:")
                    for i, error in enumerate(error_examples, 1):
                        if "row" in error and "error" in error:
                            error_messages.append(
                                f"  Row {error['row']}: {error['error']}"
                            )

                # If we have specific errors, show them, otherwise fall back to generic message
                error_detail = (
                    ". ".join(error_messages)
                    if error_messages
                    else "Please check your CSV format"
                )

                return {
                    "success": False,
                    "message": f"Import failed: {error_detail}",
                    "error_rows": len(error_rows),
                    "total_rows": len(df) if not df.empty else 0,
                }, 400

            return {
                "success": True,
                "message": f"Successfully imported {success_count} cryptocurrencies",
                "errors": len(error_rows),
                "error_details": (
                    error_rows[:5] if error_rows else []
                ),  # Include first 5 errors for debugging
            }, 200

        except Exception as e:
            logger.exception(f"Error during CSV import: {str(e)}")
            db.session.rollback()
            return {"success": False, "message": f"Error importing CSV: {str(e)}"}, 500

    @staticmethod
    def export_to_csv():
        """Export all cryptocurrency data to CSV"""
        try:
            cryptocurrencies = Cryptocurrency.query.all()

            if not cryptocurrencies:
                return {
                    "success": False,
                    "message": "No cryptocurrency data to export",
                }, 404

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(
                [
                    "id",
                    "symbol",
                    "name",
                    "price",
                    "price_change_24h",
                    "percent_change_24h",
                    "market_cap",
                    "volume_24h",
                    "circulating_supply",
                    "dataset_id",
                ]
            )

            for crypto in cryptocurrencies:
                writer.writerow(
                    [
                        crypto.id,
                        crypto.symbol,
                        crypto.name,
                        crypto.price,
                        crypto.price_change_24h,
                        crypto.percent_change_24h,
                        crypto.market_cap,
                        crypto.volume_24h,
                        crypto.circulating_supply,
                        crypto.dataset_id,
                    ]
                )

            return output.getvalue(), 200

        except Exception as e:
            logger.exception(f"Error exporting CSV: {str(e)}")
            return {"success": False, "message": f"Error exporting CSV: {str(e)}"}, 500