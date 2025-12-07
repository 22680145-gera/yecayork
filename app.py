from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_cors import CORS
import psycopg2
from dotenv import load_dotenv
import os
import hashlib
from urllib.parse import urlparse

# ==============================================
#              CONFIGURACIÓN FLASK
# ==============================================
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "super_secret_key_default")
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# ==============================================
#           CONEXIÓN CON SUPABASE
# ==============================================

def get_db():
    try:
        # PRIMERO intentar con DATABASE_URL (formato completo)
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            print(f"🔗 Intentando conectar con DATABASE_URL...")
            # Asegurar que la URL tenga el formato correcto
            if not database_url.startswith('postgresql://'):
                database_url = database_url.replace('postgres://', 'postgresql://')
            
            conn = psycopg2.connect(database_url, sslmode='require')
            print("✅ Conexión exitosa usando DATABASE_URL")
            return conn
        
        # SEGUNDO intentar con variables separadas
        print(f"🔗 Intentando conectar con variables separadas...")
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT"),
            sslmode='require'  # IMPORTANTE para Supabase
        )
        print("✅ Conexión exitosa usando variables separadas")
        return conn
        
    except Exception as e:
        print(f"❌ Error al conectar a Supabase: {e}")
        print(f"📝 DATABASE_URL disponible: {'Sí' if os.getenv('DATABASE_URL') else 'No'}")
        print(f"📝 DB_HOST: {os.getenv('DB_HOST')}")
        return None

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
        
        conn = get_db()
        if not conn:
            return jsonify({"success": False, "message": "Error de conexión a la base de datos. Verifica tu internet."}), 500
        
        cursor = conn.cursor()
        
        # Verificar si el correo ya existe
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "El correo ya está registrado"}), 400
        
        # Hashear la contraseña
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertar nuevo usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, password_hash) 
            VALUES (%s, %s, %s) 
            RETURNING id, nombre, correo
        """, (nombre, correo, hashed_password))
        
        new_user = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Usuario registrado exitosamente",
            "user": {
                "id": new_user[0],
                "nombre": new_user[1],
                "correo": new_user[2]
            }
        })
        
    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({"success": False, "message": f"Error en el servidor: {str(e)}"}), 500

# ... (el resto del código se mantiene igual)

if __name__ == "__main__":
    app.run(debug=True, port=5000)