from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import hashlib
import json
import os

# ==============================================
#              CONFIGURACIÓN FLASK
# ==============================================
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True)

app.secret_key = "yecayork_secreto_2025"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# ==============================================
#           BASE DE DATOS LOCAL (JSON)
# ==============================================

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products.json')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')

def init_data_dir():
    """Crear directorio de datos si no existe"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_users():
    """Cargar usuarios desde JSON"""
    init_data_dir()
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Usuario admin por defecto
        default_users = [
            {
                "id": 1,
                "nombre": "Admin Yecayork",
                "correo": "admin@yecayork.com",
                "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
                "rol": "admin",
                "telefono": "7352152870"
            }
        ]
        save_users(default_users)
        return default_users

def save_users(users):
    """Guardar usuarios en JSON"""
    init_data_dir()
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_products():
    """Cargar productos desde JSON"""
    init_data_dir()
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Productos por defecto
        default_products = [
            {
                "id": 1,
                "nombre": "Corte Cecina de res",
                "descripcion": "Carne de res de las cuartos traseros, que se filetea, sala, se seca al sol y se unta con manteca de cerdo.",
                "precio": 360.00,
                "imagen": "img/corte1.jpg",
                "disponible": True,
                "categoria": "res"
            },
            {
                "id": 2,
                "nombre": "Corte Longaniza",
                "descripcion": "Carne molida de puerco condimentada con pasas, almendras. Utilizando las tripas del cerdo para embutir.",
                "precio": 160.00,
                "imagen": "img/corte2.jpg",
                "disponible": True,
                "categoria": "cerdo"
            },
            {
                "id": 3,
                "nombre": "Corte Cecina enchilada",
                "descripcion": "Elaborada con la carne del cuarto trasero del puerco, enchilado con receta de la casa.",
                "precio": 240.00,
                "imagen": "img/corte3.jpg",
                "disponible": True,
                "categoria": "cerdo"
            },
            {
                "id": 4,
                "nombre": "Corte Gorditos o Gracitas",
                "descripcion": "Corte derivado de la cecina, quitándose como exceso, la grasa.",
                "precio": 120.00,
                "imagen": "img/corte4.jpg",
                "disponible": True,
                "categoria": "mixto"
            }
        ]
        save_products(default_products)
        return default_products

def save_products(products):
    """Guardar productos en JSON"""
    init_data_dir()
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

# ==============================================
#                   RUTAS
# ==============================================

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/session", methods=["GET"])
def api_session():
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "user": {
                "id": session['user_id'],
                "nombre": session.get('user_name', 'Usuario'),
                "correo": session.get('user_email', ''),
                "rol": session.get('user_role', 'cliente')
            }
        })
    return jsonify({"logged_in": False})

@app.route("/api/register", methods=["POST"])
def api_register():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        correo = data.get('correo')
        password = data.get('password')
        
        if not nombre or not correo or not password:
            return jsonify({"success": False, "message": "Todos los campos son obligatorios"}), 400
        
        # Validar email
        if '@' not in correo or '.' not in correo:
            return jsonify({"success": False, "message": "Correo electrónico no válido"}), 400
        
        # Validar contraseña
        if len(password) < 6:
            return jsonify({"success": False, "message": "La contraseña debe tener al menos 6 caracteres"}), 400
        
        users = load_users()
        
        # Verificar si el correo ya existe
        for user in users:
            if user['correo'].lower() == correo.lower():
                return jsonify({"success": False, "message": "El correo ya está registrado"}), 400
        
        # Hashear la contraseña
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Generar nuevo ID
        new_id = max([u['id'] for u in users], default=0) + 1
        
        # Crear nuevo usuario
        new_user = {
            "id": new_id,
            "nombre": nombre,
            "correo": correo.lower(),
            "password_hash": hashed_password,
            "rol": "cliente",
            "telefono": "",
            "direccion": ""
        }
        
        # Guardar usuario
        users.append(new_user)
        save_users(users)
        
        # Iniciar sesión automáticamente
        session['user_id'] = new_id
        session['user_name'] = nombre
        session['user_email'] = correo.lower()
        session['user_role'] = 'cliente'
        
        return jsonify({
            "success": True,
            "message": "¡Registro exitoso! Bienvenido a Yecayork",
            "user": {
                "id": new_id,
                "nombre": nombre,
                "correo": correo.lower(),
                "rol": "cliente"
            }
        })
        
    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({"success": False, "message": "Error en el servidor. Intenta nuevamente."}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.get_json()
        correo = data.get('correo')
        password = data.get('password')
        
        if not correo or not password:
            return jsonify({"success": False, "message": "Correo y contraseña son requeridos"}), 400
        
        users = load_users()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        for user in users:
            if user['correo'].lower() == correo.lower() and user['password_hash'] == hashed_password:
                # Guardar en sesión
                session['user_id'] = user['id']
                session['user_name'] = user['nombre']
                session['user_email'] = user['correo']
                session['user_role'] = user.get('rol', 'cliente')
                
                return jsonify({
                    "success": True,
                    "message": f"¡Bienvenido {user['nombre']}!",
                    "user": {
                        "id": user['id'],
                        "nombre": user['nombre'],
                        "correo": user['correo'],
                        "rol": user.get('rol', 'cliente')
                    }
                })
        
        return jsonify({"success": False, "message": "Correo o contraseña incorrectos"}), 401
        
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"success": False, "message": "Error en el servidor"}), 500

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Sesión cerrada exitosamente"})

@app.route("/api/productos", methods=["GET"])
def api_productos():
    try:
        products = load_products()
        return jsonify({"success": True, "productos": products})
    except Exception as e:
        print(f"Error obteniendo productos: {e}")
        return jsonify({"success": False, "message": "Error al obtener productos", "productos": []}), 500

@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Debes iniciar sesión para comprar"}), 401
        
        data = request.get_json()
        items = data.get('items', [])
        total = data.get('total', 0)
        payment_method = data.get('payment_method', 'oxxo')
        
        if not items or total <= 0:
            return jsonify({"success": False, "message": "Carrito vacío"}), 400
        
        # Simular orden exitosa
        order_id = 1000 + len(load_users())
        
        return jsonify({
            "success": True,
            "message": "¡Compra exitosa! Tu pedido será procesado.",
            "order_id": order_id,
            "total": total,
            "payment_method": payment_method
        })
        
    except Exception as e:
        print(f"Error en checkout: {e}")
        return jsonify({"success": False, "message": "Error procesando la compra"}), 500

@app.route("/api/user/profile", methods=["GET"])
def get_profile():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "No autenticado"}), 401
    
    users = load_users()
    for user in users:
        if user['id'] == session['user_id']:
            return jsonify({
                "success": True,
                "user": {
                    "id": user['id'],
                    "nombre": user['nombre'],
                    "correo": user['correo'],
                    "rol": user.get('rol', 'cliente'),
                    "telefono": user.get('telefono', ''),
                    "direccion": user.get('direccion', '')
                }
            })
    
    return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

# ==============================================
#                 EJECUCIÓN
# ==============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 YECAYORK TIENDA DE CARNES")
    print("🌐 http://localhost:5000")
    print("📁 Datos guardados en: data/")
    print("=" * 60)
    print("\n✅ Usuarios: data/users.json")
    print("✅ Productos: data/products.json")
    print("=" * 60 + "\n")
    
    app.run(debug=True, port=5000)