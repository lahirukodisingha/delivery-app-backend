from flask import Blueprint, request, jsonify
from app import db
from datetime import datetime

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/api/sync/backup-all', methods=['POST'])
def backup_all_data():
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "පරිශීලක නාමය (Username) හඳුනාගත නොහැක."}), 400

    try:
        def sync_collection(collection_name, local_data_list):
            if not local_data_list:
                return
            for item in local_data_list:
                local_id = item.pop('id', None)
                if local_id is not None:
                    item['local_id'] = local_id
                    
                item['username'] = username 
                item['synced_at'] = datetime.now()
                
                # වැදගත්ම වෙනස: MongoDB එකේ සේව් වෙද්දී syncStatus එක අනිවාර්යයෙන්ම synced කිරීම
                item['syncStatus'] = 'synced' 
                
                db[collection_name].update_one(
                    {"username": username, "local_id": local_id},
                    {"$set": item},
                    upsert=True
                )

        sync_collection('settings', data.get('settings'))
        sync_collection('profile', data.get('profile'))
        sync_collection('routes', data.get('routes'))
        sync_collection('shops', data.get('shops'))
        sync_collection('items', data.get('items'))
        sync_collection('bills', data.get('bills'))
        sync_collection('billItems', data.get('billItems'))
        sync_collection('expenses', data.get('expenses'))

        return jsonify({"message": "සියලුම දත්ත සාර්ථකව සර්වර් එකට Backup කරන ලදී!"}), 200

    except Exception as e:
        return jsonify({"error": f"සර්වර් දෝෂයකි: {str(e)}"}), 500
    

@sync_bp.route('/api/sync/initial-data', methods=['GET'])
def get_initial_data():
    username = request.args.get('username')
    
    if not username:
        return jsonify({"error": "පරිශීලක නාමය අනිවාර්යයි"}), 400

    try:
        settings = list(db.settings.find({"username": username}, {'_id': 0}))
        profile = list(db.profile.find({"username": username}, {'_id': 0}))
        routes = list(db.routes.find({"username": username}, {'_id': 0}))
        shops = list(db.shops.find({"username": username}, {'_id': 0}))
        items = list(db.items.find({"username": username}, {'_id': 0}))
        bills = list(db.bills.find({"username": username}, {'_id': 0}))
        bill_items = list(db.billItems.find({"username": username}, {'_id': 0}))
        expenses = list(db.expenses.find({"username": username}, {'_id': 0}))

        app_settings = db.app_settings.find_one({}, {'_id': 0})
        if not app_settings:
            app_settings = {
                "notifications": [], 
                "units": ["kg", "g", "ml", "l", "packet", "box", "bottle"],
                "expense_categories": ["fuel", "food", "vehicle", "other_expense"],
                "income_categories": ["tip", "found_money", "advance"]
            }
        
        def format_for_frontend(data_list):
            for item in data_list:
                item.pop('username', None)
                item.pop('synced_at', None)
                if 'local_id' in item:
                    item['id'] = item.pop('local_id')
                
                # වැදගත්ම වෙනස: ඩ්‍රයිවර්ට යවද්දීත් අනිවාර්යයෙන්ම synced කර යැවීම
                item['syncStatus'] = 'synced'
            return data_list

        return jsonify({
            "settings": format_for_frontend(settings),
            "profile": format_for_frontend(profile),
            "routes": format_for_frontend(routes),
            "shops": format_for_frontend(shops),
            "items": format_for_frontend(items),
            "bills": format_for_frontend(bills),
            "billItems": format_for_frontend(bill_items),
            "expenses": format_for_frontend(expenses),
            "appSettings": app_settings 
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"දත්ත ලබාගැනීමේ දෝෂයකි: {str(e)}"}), 500
    

# ==========================================
# ඩ්‍රයිවර් කියවූ පණිවිඩ (Read Notifications) කෙලින්ම සේව් කිරීම සහ ලබාගැනීම
# ==========================================
@sync_bp.route('/api/sync/user-notifs', methods=['GET', 'POST'])
def handle_user_notifs():
    if request.method == 'GET':
        username = request.args.get('username')
        user = db.users.find_one({"username": username})
        read_notifs = user.get("read_notifications", []) if user else []
        return jsonify({"readNotifs": read_notifs}), 200
        
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        notif_ids = data.get('notif_ids', [])
        
        # තනි ID එකක් ආවොත් ඒක Array එකක් බවට පත් කිරීම
        if isinstance(notif_ids, str):
            notif_ids = [notif_ids]
            
        if username and notif_ids:
            # $addToSet සහ $each මගින් අලුත් ID පමණක් duplicate නොවි එකතු කරයි
            db.users.update_one(
                {"username": username}, 
                {"$addToSet": {"read_notifications": {"$each": notif_ids}}}
            )
        return jsonify({"success": True}), 200