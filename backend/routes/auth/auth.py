"""
Authentication routes — /auth/*
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt,
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import db_connection
from utils.logger import app_log, ops_log

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    data     = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        ops_log.warning('Login attempt with missing credentials from %s', request.remote_addr)
        return jsonify({'error': 'Username and password required'}), 400

    ops_log.info('Login attempt for user "%s" from %s', username, request.remote_addr)

    with db_connection() as conn:
        row = conn.execute(
            'SELECT id, username, password_hash, is_admin FROM users WHERE username = ?',
            (username,),
        ).fetchone()

    if row and check_password_hash(row['password_hash'], password):
        token = create_access_token(
            identity=str(row['id']),
            additional_claims={'username': row['username'], 'is_admin': bool(row['is_admin'])},
        )
        ops_log.info('Login SUCCESS — user "%s" (id=%s, admin=%s)', row['username'], row['id'], bool(row['is_admin']))
        return jsonify({
            'access_token': token,
            'username':     row['username'],
            'is_admin':     bool(row['is_admin']),
        }), 200

    ops_log.warning('Login FAILED — invalid credentials for user "%s" from %s', username, request.remote_addr)
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    claims = get_jwt()
    return jsonify({'user': {
        'id':       get_jwt_identity(),
        'username': claims.get('username'),
        'is_admin': claims.get('is_admin', False),
    }}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id      = get_jwt_identity()
    data         = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        ops_log.warning('Password change attempt with missing fields (user_id=%s)', user_id)
        return jsonify({'error': 'Old and new password required'}), 400
    if len(new_password) < 8:
        ops_log.warning('Password change rejected — too short (user_id=%s)', user_id)
        return jsonify({'error': 'New password must be at least 8 characters'}), 400

    ops_log.info('Password change requested by user_id=%s', user_id)

    with db_connection() as conn:
        row = conn.execute(
            'SELECT password_hash FROM users WHERE id = ?', (user_id,)
        ).fetchone()

        if row and check_password_hash(row['password_hash'], old_password):
            conn.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (generate_password_hash(new_password), user_id),
            )
            ops_log.info('Password changed successfully for user_id=%s', user_id)
            return jsonify({'message': 'Password changed successfully'}), 200

    ops_log.warning('Password change FAILED — invalid old password (user_id=%s)', user_id)
    return jsonify({'error': 'Invalid old password'}), 401
