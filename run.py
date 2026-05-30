from app import app
from app.routes.admin_routes import admin_bp
from app.routes.auth_routes import auth_bp # අලුතින් ගෙනාපු කොටස
from app.routes.sync_routes import sync_bp

# Routes ටික App එකට සම්බන්ධ කිරීම
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp) # අලුතින් ගෙනාපු කොටස
app.register_blueprint(sync_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5000)