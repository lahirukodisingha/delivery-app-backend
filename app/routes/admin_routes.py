from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import db
from bson.objectid import ObjectId

admin_bp = Blueprint('admin', __name__)

# ==========================================
# 1. නව රියදුරු ගිණුමක් සෑදීම
# ==========================================
@admin_bp.route('/api/admin/register-driver', methods=['POST'])
def register_driver():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    first_name = data.get('first_name', '') # අලුතින් එක්කළ කොටස
    last_name = data.get('last_name', '')   # අලුතින් එක්කළ කොටස
    
    if not username or not password:
        return jsonify({"error": "පරිශීලක නාමය සහ මුරපදය අනිවාර්යයි"}), 400
        
    if db.users.find_one({"username": username}):
        return jsonify({"error": "මෙම නමින් දැනටමත් ගිණුමක් ඇත"}), 400
        
    valid_until = datetime.now() + timedelta(days=30)
    
    new_driver = {
        "first_name": first_name, # අලුතින් එක්කළ කොටස
        "last_name": last_name,   # අලුතින් එක්කළ කොටස
        "username": username,
        "password": generate_password_hash(password),
        "role": "driver",
        "is_active": True,
        "account_valid_until": valid_until,
        "created_at": datetime.now(),
        "last_login_date": None
    }
    
    db.users.insert_one(new_driver)
    
    return jsonify({
        "message": "නව රියදුරු ගිණුම සාර්ථකව නිර්මාණය කරන ලදී!",
        "username": username,
        "valid_until": valid_until.strftime('%Y-%m-%d')
    }), 201


# ==========================================
# 2. සියලුම රියදුරන්ගේ දත්ත ලබා ගැනීම
# ==========================================
@admin_bp.route('/api/admin/drivers', methods=['GET'])
def get_drivers():
    drivers = list(db.users.find({"role": "driver"}, {"password": 0}))
    for driver in drivers:
        driver['_id'] = str(driver['_id'])
        if driver.get('account_valid_until'):
            driver['account_valid_until'] = driver['account_valid_until'].strftime('%Y-%m-%d')
        if driver.get('last_login_date'):
            driver['last_login_date'] = driver['last_login_date'].strftime('%Y-%m-%d %H:%M')
        else:
            driver['last_login_date'] = "තාම ලොග් වී නැත"
            
    return jsonify(drivers), 200

# ==========================================
# 3. රියදුරෙකුගේ ගිණුමේ වලංගු කාලය වෙනස් කිරීම
# ==========================================
@admin_bp.route('/api/admin/drivers/<user_id>/validity', methods=['PUT'])
def update_validity(user_id):
    data = request.get_json()
    new_date_str = data.get('valid_until')
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
        db.users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": {"account_valid_until": new_date, "is_active": True}}
        )
        return jsonify({"message": "කාලය සාර්ථකව වෙනස් කරන ලදී!"}), 200
    except Exception as e:
        return jsonify({"error": "දිනය වෙනස් කිරීමේ දෝෂයකි."}), 400

# ==========================================
# 4. රියදුරෙකුගේ පාස්වර්ඩ් එක අලුතින් සැකසීම
# ==========================================
@admin_bp.route('/api/admin/drivers/<user_id>/reset-password', methods=['PUT'])
def reset_password(user_id):
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "මුරපදය අවම වශයෙන් අකුරු 6ක් විය යුතුය"}), 400
        
    hashed_password = generate_password_hash(new_password)
    db.users.update_one(
        {"_id": ObjectId(user_id)}, 
        {"$set": {"password": hashed_password}}
    )
    return jsonify({"message": "මුරපදය සාර්ථකව වෙනස් කරන ලදී!"}), 200

# ==========================================
# 5. රියදුරෙකුගේ නම වෙනස් කිරීම (අලුත් API එක)
# ==========================================
@admin_bp.route('/api/admin/drivers/<user_id>/name', methods=['PUT'])
def update_name(user_id):
    data = request.get_json()
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    try:
        db.users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": {"first_name": first_name, "last_name": last_name}}
        )
        return jsonify({"message": "නම සාර්ථකව යාවත්කාලීන කරන ලදී!"}), 200
    except Exception as e:
        return jsonify({"error": "නම වෙනස් කිරීමේ දෝෂයකි."}), 400

# ==========================================
# 6. ගිණුමක් මකා දැමීම (Delete - අලුත් API එක)
# ==========================================
@admin_bp.route('/api/admin/drivers/<user_id>', methods=['DELETE'])
def delete_driver(user_id):
    try:
        db.users.delete_one({"_id": ObjectId(user_id)})
        return jsonify({"message": "ගිණුම සාර්ථකව මකා දමන ලදී!"}), 200
    except Exception as e:
        return jsonify({"error": "ගිණුම මකා දැමීමේ දෝෂයකි."}), 400

# ==========================================
# 7. App Settings (Notifications & Dropdowns) ලබා ගැනීම
# ==========================================
@admin_bp.route('/api/admin/settings', methods=['GET'])
def get_settings():
    settings = db.app_settings.find_one({})
    if not settings:
        settings = {
            "notifications": [], 
            "units": ["kg", "g", "ml", "l", "packet", "box", "bottle"],
            "expense_categories": ["fuel", "food", "vehicle", "other_expense"],
            "income_categories": ["tip", "found_money", "advance"]
        }
        db.app_settings.insert_one(settings)
    
    settings['_id'] = str(settings.get('_id', ''))
    return jsonify(settings), 200

# ==========================================
# 8. App Settings යාවත්කාලීන කිරීම
# ==========================================
@admin_bp.route('/api/admin/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()
    try:
        db.app_settings.update_one({}, {"$set": {
            "notifications": data.get('notifications', []), 
            "units": data.get('units', []),
            "expense_categories": data.get('expense_categories', []),
            "income_categories": data.get('income_categories', [])
        }}, upsert=True)
        return jsonify({"message": "සැකසුම් සාර්ථකව යාවත්කාලීන කරන ලදී!"}), 200
    except Exception as e:
        return jsonify({"error": "සැකසුම් සුරැකීමේදී දෝෂයක් මතු විය."}), 500