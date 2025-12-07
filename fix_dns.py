import socket
import subprocess
import os
import sys

def test_dns(hostname):
    """Probar resolución DNS"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS funciona: {hostname} → {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ DNS falló para: {hostname}")
        print(f"   Error: {e}")
        return False

def fix_dns_windows():
    """Reparar DNS en Windows"""
    print("\n🔧 Reparando DNS en Windows...")
    print("=" * 50)
    
    commands = [
        ("ipconfig /flushdns", "Limpiando cache DNS..."),
        ("ipconfig /registerdns", "Registrando DNS..."),
        ("ipconfig /release", "Liberando IP..."),
        ("ipconfig /renew", "Renovando IP..."),
        ("netsh winsock reset", "Reseteando Winsock...")
    ]
    
    for cmd, desc in commands:
        print(f"\n{desc}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Comando exitoso")
            else:
                print(f"  ⚠️  Comando falló: {result.stderr[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n🔄 Reiniciando servicio DNS...")
    try:
        subprocess.run("net stop dnscache", shell=True, capture_output=True)
        subprocess.run("net start dnscache", shell=True, capture_output=True)
        print("  ✅ Servicio DNS reiniciado")
    except Exception as e:
        print(f"  ⚠️  Error reiniciando servicio: {e}")

def set_google_dns():
    """Configurar Google DNS"""
    print("\n🌐 Configurando Google DNS (8.8.8.8, 8.8.4.4)...")
    print("=" * 50)
    
    try:
        # Obtener todas las interfaces de red
        result = subprocess.run(
            "netsh interface show interface", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        interfaces = []
        lines = result.stdout.split('\n')
        
        # Buscar interfaces conectadas
        for line in lines:
            if 'Connected' in line and 'Dedicated' in line:
                parts = line.split()
                if len(parts) >= 4:
                    interface_name = parts[-1]
                    interfaces.append(interface_name)
        
        if not interfaces:
            print("  ⚠️  No se encontraron interfaces conectadas")
            return
        
        print(f"  📡 Interfaces encontradas: {', '.join(interfaces)}")
        
        # Configurar Google DNS en cada interfaz
        for interface in interfaces:
            print(f"\n  Configurando interfaz: {interface}")
            
            # Configurar DNS primario (Google)
            cmd1 = f'netsh interface ip set dns name="{interface}" static 8.8.8.8'
            result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
            
            if result1.returncode == 0:
                print(f"    ✅ DNS primario configurado: 8.8.8.8")
            else:
                print(f"    ⚠️  Error DNS primario: {result1.stderr[:100]}")
            
            # Configurar DNS secundario (Google)
            cmd2 = f'netsh interface ip add dns name="{interface}" 8.8.4.4 index=2'
            result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
            
            if result2.returncode == 0:
                print(f"    ✅ DNS secundario configurado: 8.8.4.4")
            else:
                print(f"    ⚠️  Error DNS secundario: {result2.stderr[:100]}")
        
        print("\n✅ Google DNS configurado en todas las interfaces")
        
    except Exception as e:
        print(f"  ❌ Error configurando DNS: {e}")

def test_connection_to_supabase():
    """Probar conexión específica a Supabase"""
    print("\n🧪 Probando conexión específica...")
    print("=" * 50)
    
    hostname = "db.licmwbpjnzmkxjevxsj.supabase.co"
    
    # Probar ping (1 intento, timeout 3 segundos)
    print(f"Ping a {hostname}...")
    try:
        result = subprocess.run(
            f"ping -n 1 -w 3000 {hostname}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "Reply from" in result.stdout:
            print("  ✅ Ping exitoso")
            return True
        else:
            print("  ❌ Ping falló")
            print(f"    Salida: {result.stdout[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error en ping: {e}")
        return False

def main():
    """Función principal"""
    print("🛠️  REPARADOR DE DNS PARA YECAYORK")
    print("=" * 60)
    
    hostname = "db.licmwbpjnzmkxjevxsj.supabase.co"
    
    print(f"🔍 Probando conexión a: {hostname}")
    print("-" * 60)
    
    # Probar DNS actual
    dns_works = test_dns(hostname)
    
    if dns_works:
        print("\n🎉 ¡El DNS ya funciona correctamente!")
        print("Puedes volver a ejecutar tu app.py normal")
        return
    
    print("\n⚠️  Problema de DNS detectado")
    print("-" * 60)
    
    # Mostrar opciones
    print("\n¿Qué quieres hacer?")
    print("1. Reparar DNS automáticamente (RECOMENDADO)")
    print("2. Solo configurar Google DNS")
    print("3. Probar conexión después de reparar")
    print("4. Salir")
    
    try:
        choice = input("\nElige una opción (1-4): ").strip()
        
        if choice == "1":
            # Reparación completa
            fix_dns_windows()
            set_google_dns()
            
            print("\n🔄 Probando conexión después de reparar...")
            test_dns(hostname)
            test_connection_to_supabase()
            
        elif choice == "2":
            # Solo Google DNS
            set_google_dns()
            
        elif choice == "3":
            # Solo probar
            test_dns(hostname)
            test_connection_to_supabase()
            
        elif choice == "4":
            print("Saliendo...")
            return
            
        else:
            print("Opción no válida")
            return
        
        print("\n" + "=" * 60)
        print("🔄 Es posible que necesites reiniciar algunos programas")
        print("o incluso reiniciar Windows para que los cambios surtan efecto.")
        print("=" * 60)
        
        # Preguntar si probar app.py
        test_app = input("\n¿Quieres probar tu app.py ahora? (s/n): ").lower()
        if test_app == 's':
            print("\nEjecutando prueba rápida de app.py...")
            try:
                # Crear un test rápido
                import psycopg2
                from dotenv import load_dotenv
                load_dotenv()
                
                print("  🔗 Conectando a Supabase...")
                conn = psycopg2.connect(
                    host=os.getenv("DB_HOST"),
                    database=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    port=os.getenv("DB_PORT"),
                    connect_timeout=5
                )
                print("  ✅ ¡Conexión exitosa!")
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Error de conexión: {e}")
                print("\n💡 Sugerencia: Usa app_local.py temporalmente")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Operación cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    # Verificar si se ejecuta como administrador (recomendado)
    try:
        # Intenta crear un archivo en una ubicación protegida
        test_file = r"C:\Windows\Temp\dns_test.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Ejecutando con permisos adecuados")
    except PermissionError:
        print("⚠️  ADVERTENCIA: Este script funciona mejor como Administrador")
        print("   Ejecuta PowerShell como Administrador y luego:")
        print("   cd C:\\Ruth\\yecayork")
        print("   python fix_dns.py")
        print("\n   ¿Continuar de todos modos? (algunas funciones podrían fallar)")
        if input("   (s/n): ").lower() != 's':
            sys.exit()
    
    main()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN:")
    print("- Si el DNS funciona: Usa tu app.py normal")
    print("- Si sigue fallando: Usa app_local.py temporalmente")
    print("=" * 60)
    
    input("\nPresiona Enter para salir...")