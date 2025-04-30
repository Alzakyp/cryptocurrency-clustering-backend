import logging

from flask import Response, jsonify, make_response, request
from flask_jwt_extended import get_jwt_identity

from services.dataset_service import DatasetService

logger = logging.getLogger(__name__)


class DatasetController:
    @staticmethod
    def get_all():
        """Get all datasets"""
        result, status_code = DatasetService.get_all_datasets()
        return jsonify(result), status_code

    @staticmethod
    def get_one(dataset_id):
        """Get one dataset by id"""
        result, status_code = DatasetService.get_dataset(dataset_id)
        return jsonify(result), status_code

    @staticmethod
    def upload_dataset():
        """Upload new dataset"""
        logger.debug("=== Dataset Upload Request ===")

        if "file" not in request.files:
            return jsonify({"success": False, "message": "No file part"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"success": False, "message": "No selected file"}), 400

        if file and file.filename.endswith(".csv"):
            file_content = file.read()
            result, status_code = DatasetService.upload_dataset(
                file.filename, file_content
            )
            return jsonify(result), status_code
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Invalid file format. Please upload a CSV file.",
                    }
                ),
                400,
            )

    @staticmethod
    def update_dataset(dataset_id):
        """Update dataset"""
        logger.debug(f"=== Dataset Update Request for ID: {dataset_id} ===")

        data = {}

        # Check if new filename provided
        if "filename" in request.form:
            data["filename"] = request.form.get("filename")

        # Check if new file provided
        if "file" in request.files:
            file = request.files["file"]
            if file.filename != "":
                data["content"] = file.read()

        if not data:
            return (
                jsonify({"success": False, "message": "No update data provided"}),
                400,
            )

        result, status_code = DatasetService.update_dataset(dataset_id, data)
        return jsonify(result), status_code

    @staticmethod
    def delete_dataset(dataset_id):
        """Delete dataset"""
        result, status_code = DatasetService.delete_dataset(dataset_id)
        return jsonify(result), status_code

    @staticmethod
    def import_from_dataset(dataset_id):
        """Import cryptocurrencies from dataset"""
        result, status_code = DatasetService.import_cryptocurrencies(dataset_id)
        return jsonify(result), status_code

    @staticmethod
    def get_dataset_content(dataset_id):
        """Download dataset content"""
        result, status_code = DatasetService.get_dataset_content(dataset_id)

        if status_code != 200:
            return jsonify(result), status_code

        # Set response headers to force CSV download
        response = Response(
            result["content"],
            mimetype="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"',
                "Content-Type": "text/csv",
            },
        )
        return response

    @staticmethod
    def preview_dataset(dataset_id):
        """Preview dataset content as JSON"""
        result, status_code = DatasetService.preview_dataset(dataset_id)
        return jsonify(result), status_code
