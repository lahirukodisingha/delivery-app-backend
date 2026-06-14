from flask import Blueprint, request, jsonify
from app import db
from datetime import datetime

sync_bp = Blueprint('sync', __name__)

@sync_bp.route('/api/sync/backup-all', methods=['POST'])
def backup_all_data():
    data = request.get_json()
    username = data.get('username')
    
    # යූසර් කෙනෙක් නැත්නම් දත්ත සේව් කරන්නේ නෑ
    if not username:
        return jsonify({"error": "පරිශීලක නාමය (Username) හඳුනාගත නොහැක."}), 400

    try:
        # දත්ත Upsert කිරීම සඳහා සාදන ලද පොදු Function එකක්
        def sync_collection(collection_name, local_data_list):
            if not local_data_list:
                return
            for item in local_data_list:
                # React පැත්තේ තිබුණු 'id' එක MongoDB එකට යද්දි 'local_id' කරමු
                local_id = item.pop('id', None)
                if local_id is not None:
                    item['local_id'] = local_id
                    
                item['username'] = username # දත්තය අයිති ඩ්‍රයිවර් කවුද යන්න සටහන් කිරීම
                item['synced_at'] = datetime.now()
                
                # MongoDB එකේ මේ local_id එක සහ username එක තියෙනවා නම් Update කරයි, නැත්නම් Insert කරයි
                db[collection_name].update_one(
                    {"username": username, "local_id": local_id},
                    {"$set": item},
                    upsert=True
                )

        # Frontend එකෙන් එවන සියලුම Tables මෙසේ MongoDB වෙත යැවීම
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
        # අදාල යූසර්ගේ දත්ත පමණක් ලබාගැනීම
        settings = list(db.settings.find({"username": username}, {'_id': 0}))
        profile = list(db.profile.find({"username": username}, {'_id': 0}))
        routes = list(db.routes.find({"username": username}, {'_id': 0}))
        shops = list(db.shops.find({"username": username}, {'_id': 0}))
        items = list(db.items.find({"username": username}, {'_id': 0}))
        bills = list(db.bills.find({"username": username}, {'_id': 0}))
        bill_items = list(db.billItems.find({"username": username}, {'_id': 0}))
        expenses = list(db.expenses.find({"username": username}, {'_id': 0}))

        # --- අලුතින් එක්කළ කොටස: App Settings ලබා ගැනීම ---
        app_settings = db.app_settings.find_one({}, {'_id': 0})
        if not app_settings:
            app_settings = {
                "notifications": [], # වෙනස් කළ කොටස
                "units": ["kg", "g", "ml", "l", "packet", "box", "bottle"],
                "expense_categories": ["fuel", "food", "vehicle", "other_expense"],
                "income_categories": ["tip", "found_money", "advance"]
            }
        # ------------------------------------------------

        # සර්වර් එකේ තියෙන 'local_id' එක React එකට තේරෙන විදිහට ආපසු 'id' බවට පත් කිරීම
        def format_for_frontend(data_list):
            for item in data_list:
                item.pop('username', None)
                item.pop('synced_at', None)
                if 'local_id' in item:
                    item['id'] = item.pop('local_id')
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
            "appSettings": app_settings # <--- අලුතින් එක් කළ පේළිය
        }), 200

        # සර්වර් එකේ තියෙන 'local_id' එක React එකට තේරෙන විදිහට ආපසු 'id' බවට පත් කිරීම
        def format_for_frontend(data_list):
            for item in data_list:
                item.pop('username', None) # යූසර් නම React එකට යැවීම අනවශ්‍යයි
                item.pop('synced_at', None) # සර්වර් එකේ සේව් වුන වෙලාව අනවශ්‍යයි
                if 'local_id' in item:
                    item['id'] = item.pop('local_id')
            return data_list

        return jsonify({
            "settings": format_for_frontend(settings),
            "profile": format_for_frontend(profile),
            "routes": format_for_frontend(routes),
            "shops": format_for_frontend(shops),
            "items": format_for_frontend(items),
            "bills": format_for_frontend(bills),
            "billItems": format_for_frontend(bill_items),
            "expenses": format_for_frontend(expenses)
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"දත්ත ලබාගැනීමේ දෝෂයකි: {str(e)}"}), 500