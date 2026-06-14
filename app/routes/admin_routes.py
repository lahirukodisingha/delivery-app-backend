from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import db
from bson.objectid import ObjectId
from datetime import datetime

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


from bson.objectid import ObjectId
from datetime import datetime

# ==========================================
# 1. සියලුම රියදුරන්ගේ දත්ත ලබා ගැනීම
# ==========================================
@admin_bp.route('/api/admin/drivers', methods=['GET'])
def get_drivers():
    # 'driver' role එක තියෙන අය පමණක් ලබාගනී (පාස්වර්ඩ් එක යවන්නේ නැත)
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
# 2. රියදුරෙකුගේ ගිණුමේ වලංගු කාලය වෙනස් කිරීම
# ==========================================
@admin_bp.route('/api/admin/drivers/<user_id>/validity', methods=['PUT'])
def update_validity(user_id):
    data = request.get_json()
    new_date_str = data.get('valid_until')
    try:
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
        # දිනය අප්ඩේට් කරනවා වගේම ගිණුම නැවත Active කරනවා
        db.users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": {"account_valid_until": new_date, "is_active": True}}
        )
        return jsonify({"message": "කාලය සාර්ථකව වෙනස් කරන ලදී!"}), 200
    except Exception as e:
        return jsonify({"error": "දිනය වෙනස් කිරීමේ දෝෂයකි."}), 400

# ==========================================
# 3. රියදුරෙකුගේ පාස්වර්ඩ් එක අලුතින් සැකසීම
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
# 4. App Settings (Notifications & Dropdowns) ලබා ගැනීම
# ==========================================
@admin_bp.route('/api/admin/settings', methods=['GET'])
def get_settings():
    settings = db.app_settings.find_one({})
    
    if not settings:
        settings = {
            "notifications": [], # වෙනස් කළ කොටස
            "units": ["kg", "g", "ml", "l", "packet", "box", "bottle"],
            "expense_categories": ["fuel", "food", "vehicle", "other_expense"],
            "income_categories": ["tip", "found_money", "advance"]
        }
        db.app_settings.insert_one(settings)
    
    settings['_id'] = str(settings.get('_id', ''))
    return jsonify(settings), 200

# ==========================================
# 5. App Settings (Notifications & Dropdowns) යාවත්කාලීන කිරීම
# ==========================================
@admin_bp.route('/api/admin/settings', methods=['PUT'])
def update_settings():
    data = request.get_json()
    try:
        db.app_settings.update_one({}, {"$set": {
            "notifications": data.get('notifications', []), # වෙනස් කළ කොටස
            "units": data.get('units', []),
            "expense_categories": data.get('expense_categories', []),
            "income_categories": data.get('income_categories', [])
        }}, upsert=True)
        return jsonify({"message": "සැකසුම් සාර්ථකව යාවත්කාලීන කරන ලදී!"}), 200
    except Exception as e:
        return jsonify({"error": "සැකසුම් සුරැකීමේදී දෝෂයක් මතු විය."}), 500