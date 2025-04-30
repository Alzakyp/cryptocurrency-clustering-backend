from flask import Blueprint
from controllers.dataset_controller import DatasetController
from flask_jwt_extended import jwt_required

# Create blueprint for dataset routes
dataset_bp = Blueprint('dataset', __name__)

# Define routes
# Get all datasets
dataset_bp.route('/', methods=['GET'])(DatasetController.get_all)

# Get single dataset
dataset_bp.route('/<int:dataset_id>', methods=['GET'])(DatasetController.get_one)

# Upload new dataset
dataset_bp.route('/', methods=['POST'])(DatasetController.upload_dataset)

# Update dataset
dataset_bp.route('/<int:dataset_id>', methods=['PUT'])(DatasetController.update_dataset)

# Delete dataset
dataset_bp.route('/<int:dataset_id>', methods=['DELETE'])(DatasetController.delete_dataset)

# Import cryptocurrencies from dataset
dataset_bp.route('/<int:dataset_id>/import', methods=['POST'])(DatasetController.import_from_dataset)

# Get dataset content for download
dataset_bp.route('/<int:dataset_id>/content', methods=['GET'])(DatasetController.get_dataset_content)

# Preview dataset content
dataset_bp.route('/<int:dataset_id>/preview', methods=['GET'])(DatasetController.preview_dataset)