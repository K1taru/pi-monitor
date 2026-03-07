"""
Frontend static file serving — catch-all for the built React SPA.
"""
import os
from flask import Blueprint, send_from_directory, jsonify
from datetime import datetime

frontend_bp = Blueprint('frontend', __name__)

_FRONTEND_DIR = os.path.abspath(
    os.environ.get(
        'FRONTEND_DIR',
        os.path.join(os.path.dirname(__file__), '../../frontend/dist'),
    )
)


@frontend_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


@frontend_bp.route('/', defaults={'path': ''})
@frontend_bp.route('/<path:path>')
def serve_frontend(path):
    target = os.path.join(_FRONTEND_DIR, path)
    if path and os.path.isfile(target):
        return send_from_directory(_FRONTEND_DIR, path)
    return send_from_directory(_FRONTEND_DIR, 'index.html')
