from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import psycopg2
import hashlib
import sys

# ==============================================
#              CONFIGURACIÓN FLASK
# ==============================================
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True)

app.secret_key = "yecayork_supabase_secreto_2025"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# ==============================================
#           CONEXIÓN SUPABASE REAL
# ==============================================

SUPABASE_CONFIG = {
    "host": "34.107.113.39",  # IP DIRECTA
    "database": "postgres",
    "user": "postgres",
    "password": "yecayork123",  # ¡CONFIRMA QUE ESTA ES TU CONTRASEÑA!
    "port": "5432"
}

def get_supabase_connection():
    """Conectar a Supabase PostgreSQL con reintentos"""
    try:
        print(f"🔗 Conectando a Supabase ({SUPABASE_CONFIG['host']})...")
        conn = psycopg2.connect(
            host=SUPABASE_CONFIG["host"],
            database=SUPABASE_CONFIG["database"],
            user=SUPABASE_CONFIG["user"],
            password=SUPABASE_CONFIG["password"],
            port=SUPABASE_CONFIG["port"],
            sslmode='require',
            connect_timeout=10
        )
        print("✅ Conexión a Supabase exitosa")
        return conn
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {type(e).__name__}")
        print(f"   Detalle: {str(e)[:100]}")
        
        # Intentar con nombre por si el DNS ya funciona
        if SUPABASE_CONFIG["host"] == "34.107.113.39":
            print("🔄 Intentando con nombre de host...")
            try:
                conn = psycopg2.connect(
                    host="db.licmwbpjnzmkxjevxsj.supabase.co",
                    database=SUPABASE_CONFIG["database"],
                    user=SUPABASE_CONFIG["user"],
                    password=SUPABASE_CONFIG["password"],
                    port=SUPABASE_CONFIG["port"],
                    sslmode='require',
                    connect_timeout=10
                )
                print("✅ Conexión con nombre exitosa")
                return conn
            except Exception as e2:
                print(f"❌ Error con nombre también: {e2}")
        
        return None

def init_supabase_tables():
    """Inicializar tablas en Supabase"""
    conn = get_supabase_connection()
    if not conn:
        print("⚠️  No se pudo conectar para inicializar tablas")
        return False
    
    try:
        cursor = conn.cursor()
        
        # 1. Crear tabla usuarios si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                correo VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                rol VARCHAR(50) DEFAULT 'cliente',
                telefono VARCHAR(20),
                direccion TEXT,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'usuarios' verificada/creada")
        
        # 2. Crear tabla productos si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                descripcion TEXT,
                precio DECIMAL(10,2) NOT NULL,
                imagen_url VARCHAR(500),
                disponible BOOLEAN DEFAULT TRUE,
                categoria VARCHAR(50),
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla 'productos' verificada/creada")
        
        # 3. Verificar si hay productos
        cursor.execute("SELECT COUNT(*) FROM productos")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📦 Insertando productos de ejemplo...")
            productos = [
                ("Corte Cecina de res", "Carne de res de las cuartos traseros, que se filetea, sala, se seca al sol y se unta con manteca de cerdo.", 360.00, "img/corte1.jpg", "res"),
                ("Corte Longaniza", "Carne molida de puerco condimentada con pasas, almendras. Utilizando las tripas del cerdo para embutir.", 160.00, "img/corte2.jpg", "cerdo"),
                ("Corte Cecina enchilada", "Elaborada con la carne del cuarto trasero del puerco, enchilado con receta de la casa.", 240.00, "img/corte3.jpg", "cerdo"),
                ("Corte Gorditos o Gracitas", "Corte derivado de la cecina, quitándose como exceso, la grasa.", 120.00, "img/corte4.jpg", "mixto")
            ]
            
            for nombre, descripcion, precio, imagen, categoria in productos:
                cursor.execute("""
                    INSERT INTO productos (nombre, descripcion, precio, imagen_url, categoria)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nombre, descripcion, precio, imagen, categoria))
            
            print(f"✅ {len(productos)} productos insertados")
        else:
            print(f"✅ Ya existen {count} productos en la base de datos")
        
        # 4. Verificar si hay usuario admin
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE correo = 'admin@yecayork.com'")
        if cursor.fetchone()[0] == 0:
            print("👤 Creando usuario administrador...")
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, password_hash, rol)
                VALUES (%s, %s, %s, 'admin')
            """, ("Administrador Yecayork", "admin@yecayork.com", admin_hash))
            print("✅ Usuario admin creado: admin@yecayork.com / admin123")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Supabase inicializado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando Supabase: {type(e).__name__}")
        print(f"   Detalle: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

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
        nombre = data.get('nombre', '').strip()
        correo = data.get('correo', '').strip().lower()
        password = data.get('password', '').strip()
        
        print(f"📝 Registro intentado: {correo}")
        
        if not nombre or not correo or not password:
            return jsonify({"success": False, "message": "Todos los campos son obligatorios"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "message": "La contraseña debe tener al menos 6 caracteres"}), 400
        
        conn = get_supabase_connection()
        if not conn:
            return jsonify({"success": False, "message": "Error conectando al servidor. Intenta más tarde."}), 500
        
        cursor = conn.cursor()
        
        # Verificar si el correo ya existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "El correo ya está registrado"}), 400
        
        # Hashear la contraseña
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertar en Supabase
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, password_hash, rol)
            VALUES (%s, %s, %s, 'cliente')
            RETURNING id, nombre, correo, rol
        """, (nombre, correo, hashed_password))
        
        new_user = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        # Guardar en sesión
        session['user_id'] = new_user[0]
        session['user_name'] = new_user[1]
        session['user_email'] = new_user[2]
        session['user_role'] = new_user[3]
        
        print(f"✅ Usuario registrado: {correo} (ID: {new_user[0]})")
        
        return jsonify({
            "success": True,
            "message": "¡Registro exitoso en Yecayork!",
            "user": {
                "id": new_user[0],
                "nombre": new_user[1],
                "correo": new_user[2],
                "rol": new_user[3]
            }
        })
        
    except Exception as e:
        print(f"❌ Error en registro: {type(e).__name__}")
        print(f"   Detalle: {e}")
        return jsonify({"success": False, "message": f"Error en el servidor: {str(e)[:100]}"}), 500

@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.get_json()
        correo = data.get('correo', '').strip().lower()
        password = data.get('password', '').strip()
        
        print(f"🔐 Login intentado: {correo}")
        
        if not correo or not password:
            return jsonify({"success": False, "message": "Correo y contraseña son requeridos"}), 400
        
        conn = get_supabase_connection()
        if not conn:
            return jsonify({"success": False, "message": "Error de conexión al servidor"}), 500
        
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT id, nombre, correo, rol 
            FROM usuarios 
            WHERE correo = %s AND password_hash = %s
        """, (correo, hashed_password))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            session['user_role'] = user[3]
            
            print(f"✅ Login exitoso: {user[1]} (ID: {user[0]})")
            
            return jsonify({
                "success": True,
                "message": f"¡Bienvenido {user[1]}!",
                "user": {
                    "id": user[0],
                    "nombre": user[1],
                    "correo": user[2],
                    "rol": user[3]
                }
            })
        else:
            print(f"❌ Login fallido para: {correo}")
            return jsonify({"success": False, "message": "Correo o contraseña incorrectos"}), 401
        
    except Exception as e:
        print(f"❌ Error en login: {type(e).__name__}")
        print(f"   Detalle: {e}")
        return jsonify({"success": False, "message": "Error en el servidor"}), 500

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Sesión cerrada exitosamente"})

@app.route("/api/productos", methods=["GET"])
def api_productos():
    try:
        conn = get_supabase_connection()
        if not conn:
            print("⚠️  Fallback a productos estáticos por error de conexión")
            # Productos estáticos como fallback
            productos_estaticos = [
                {"id": 1, "nombre": "Corte Cecina de res", "descripcion": "Carne de res...", "precio": 360.00, "imagen": "img/corte1.jpg", "disponible": True},
                {"id": 2, "nombre": "Corte Longaniza", "descripcion": "Carne molida de puerco...", "precio": 160.00, "imagen": "img/corte2.jpg", "disponible": True},
                {"id": 3, "nombre": "Corte Cecina enchilada", "descripcion": "Elaborada con la carne...", "precio": 240.00, "imagen": "img/corte3.jpg", "disponible": True},
                {"id": 4, "nombre": "Corte Gorditos o Gracitas", "descripcion": "Corte derivado...", "precio": 120.00, "imagen": "img/corte4.jpg", "disponible": True}
            ]
            return jsonify({"success": True, "productos": productos_estaticos})
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, descripcion, precio, imagen_url, disponible, categoria
            FROM productos 
            WHERE disponible = TRUE
            ORDER BY id
        """)
        
        productos_db = cursor.fetchall()
        cursor.close()
        conn.close()
        
        productos = []
        for p in productos_db:
            productos.append({
                "id": p[0],
                "nombre": p[1],
                "descripcion": p[2],
                "precio": float(p[3]),
                "imagen": p[4] if p[4] else f"img/corte{p[0]}.jpg",
                "disponible": p[5],
                "categoria": p[6]
            })
        
        print(f"✅ Productos obtenidos de Supabase: {len(productos)}")
        return jsonify({"success": True, "productos": productos})
        
    except Exception as e:
        print(f"❌ Error obteniendo productos: {type(e).__name__}")
        print(f"   Detalle: {e}")
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
        
        conn = get_supabase_connection()
        if not conn:
            return jsonify({"success": False, "message": "Error de conexión"}), 500
        
        cursor = conn.cursor()
        
        # Crear orden en Supabase
        cursor.execute("""
            INSERT INTO ordenes (usuario_id, total, metodo_pago, estado)
            VALUES (%s, %s, %s, 'pendiente')
            RETURNING id
        """, (session['user_id'], total, payment_method))
        
        order_id = cursor.fetchone()[0]
        
        # Insertar items de la orden
        for item in items:
            cursor.execute("""
                INSERT INTO orden_items (orden_id, producto_id, producto_nombre, cantidad, precio, total)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_id, item['id'], f"Producto {item['id']}", item['cantidad'], item['precio'], item['cantidad'] * item['precio']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Orden creada: ID {order_id}, Total: ${total}, Usuario: {session['user_id']}")
        
        return jsonify({
            "success": True,
            "message": "¡Compra exitosa! Tu pedido ha sido registrado.",
            "order_id": order_id,
            "total": total
        })
        
    except Exception as e:
        print(f"❌ Error en checkout: {type(e).__name__}")
        print(f"   Detalle: {e}")
        return jsonify({"success": False, "message": "Error procesando la compra"}), 500

@app.route("/api/test", methods=["GET"])
def api_test():
    """Endpoint para probar conexión a Supabase"""
    conn = get_supabase_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test, version() as version")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Conexión a Supabase exitosa",
                "test": result[0],
                "version": result[1]
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"Error en consulta: {str(e)}"}), 500
    else:
        return jsonify({"success": False, "message": "No se pudo conectar a Supabase"}), 500

# ==============================================
#                 EJECUCIÓN
# ==============================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 YECAYORK - SUPABASE REAL")
    print("🌐 http://localhost:5000")
    print("📊 Base de datos: PostgreSQL en Supabase")
    print("=" * 60)
    
    # Inicializar tablas
    print("\n🔧 Inicializando Supabase...")
    if init_supabase_tables():
        print("✅ Supabase listo para usar")
    else:
        print("⚠️  Problema inicializando Supabase, continuando de todos modos...")
    
    print("\n📡 Endpoints disponibles:")
    print("  • GET  /api/test        → Probar conexión Supabase")
    print("  • POST /api/register    → Registrar usuario")
    print("  • POST /api/login       → Iniciar sesión")
    print("  • GET  /api/productos   → Obtener productos")
    print("  • POST /api/checkout    → Procesar compra")
    print("=" * 60 + "\n")
    
    app.run(debug=True, port=5000)