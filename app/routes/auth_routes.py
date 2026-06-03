import jwt
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import os
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 1. ඩේටාබේස් එකෙන් යූසර්ව හොයනවා
    user = db.users.find_one({"username": username})

    # 2. යූසර් නැත්නම් හෝ පාස්වර්ඩ් එක වැරදිනම්
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "පරිශීලක නාමය හෝ මුරපදය වැරදියි"}), 401

    # 3. එකවුන්ට් එක ඇක්ටිව් ද කියලා බලනවා
    if not user.get('is_active'):
        return jsonify({"error": "මෙම ගිණුම අක්‍රිය කර ඇත. කරුණාකර පරිපාලක අමතන්න."}), 403
    
    # 4. එකවුන්ට් එක කල් ඉකුත් වෙලාද කියලා බලනවා
    if user.get('account_valid_until') and user['account_valid_until'] < datetime.now():
        # කල් ඉකුත් වෙලා නම් එකවුන්ට් එක අක්‍රිය (is_active: False) කරනවා
        db.users.update_one({"_id": user['_id']}, {"$set": {"is_active": False}})
        return jsonify({"error": "ඔබගේ ගිණුමේ වලංගු කාලය අවසන් වී ඇත."}), 403

    # 5. අන්තිමට ලොග් වුන වෙලාව අප්ඩේට් කරනවා
    db.users.update_one({"_id": user['_id']}, {"$set": {"last_login_date": datetime.now()}})

    # 6. ටෝකන් එක සඳහා වලංගු කාලය තීරණය කිරීම
    token_exp_date = datetime.now() + timedelta(days=30)
    account_valid_until = user.get('account_valid_until')

    # ගිණුමේ කාලය දවස් 30කට කලින් අවසන් වනවා නම්, ටෝකන් එකේ Expire Date එක ලෙස එයම ලබා දෙන්න
    if account_valid_until and account_valid_until < token_exp_date:
        token_exp_date = account_valid_until

    token = jwt.encode({
        "username": user['username'],
        "role": user['role'],
        "exp": token_exp_date
    }, os.getenv("SECRET_KEY"), algorithm="HS256")

    return jsonify({
        "message": "සාර්ථකව ඇතුල් විය!",
        "token": token,
        "user": {
            "username": user['username'],
            "role": user['role'],
            # %Y-%m-%d වෙනුවට isoformat() භාවිතා කර සම්පූර්ණ වේලාව යවන්න
            "valid_until": user['account_valid_until'].isoformat() if user.get('account_valid_until') else None
        }
    }), 200


@auth_bp.route('/api/auth/change-password', methods=['POST'])
def change_password():
    data = request.get_json()
    username = data.get('username')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not username or not current_password or not new_password:
        return jsonify({"error": "සියලුම තොරතුරු ඇතුලත් කරන්න"}), 400

    # යූසර්ව හොයාගෙන පරණ පාස්වර්ඩ් එක හරියටම ගැලපෙනවද බලනවා
    user = db.users.find_one({"username": username})
    if not user or not check_password_hash(user['password'], current_password):
        return jsonify({"error": "දැනට ඇති මුරපදය වැරදියි"}), 401

    # අලුත් පාස්වර්ඩ් එක Hash කරලා සේව් කරනවා
    hashed_password = generate_password_hash(new_password)
    db.users.update_one(
        {"_id": user['_id']},
        {"$set": {"password": hashed_password}}
    )

    return jsonify({"message": "මුරපදය සාර්ථකව යාවත්කාලීන කරන ලදී!"}), 200