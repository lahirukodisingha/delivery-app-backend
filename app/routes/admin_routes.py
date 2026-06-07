from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/register-driver', methods=['POST'])
def register_driver():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    # 1. යූසර් නමයි පාස්වර්ඩ් එකයි එවලා තියෙනවද කියලා බලනවා
    if not username or not password:
        return jsonify({"error": "පරිශීලක නාමය සහ මුරපදය අනිවාර්යයි"}), 400
        
    # 2. මේ නමින් කලින් කෙනෙක් ඉන්නවද බලනවා
    if db.users.find_one({"username": username}):
        return jsonify({"error": "මෙම නමින් දැනටමත් ගිණුමක් ඇත"}), 400
        
    # 3. මාසයකින් (දවස් 30) කල් ඉකුත් වෙන දවස හදනවා
    valid_until = datetime.now() + timedelta(days=30)
    
    # 4. අලුත් ඩ්‍රයිවර්ගේ විස්තර ටික ලෑස්ති කරනවා (පාස්වර්ඩ් එක Hash කරලා සේව් කරන්නේ ආරක්ෂාවට)
    new_driver = {
        "username": username,
        "password": generate_password_hash(password),
        "role": "driver",
        "is_active": True,
        "account_valid_until": valid_until,
        "created_at": datetime.now(),
        "last_login_date": None
    }
    
    # 5. Database එකට සේව් කරනවා
    db.users.insert_one(new_driver)
    
    return jsonify({
        "message": "නව රියදුරු ගිණුම සාර්ථකව නිර්මාණය කරන ලදී!",
        "username": username,
        "valid_until": valid_until.strftime('%Y-%m-%d')
    }), 201