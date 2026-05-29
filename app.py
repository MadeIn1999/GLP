import os
import re
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
# CLAVE SECRETA: Necesaria para que Flask maneje las sesiones de usuario de forma segura
app.secret_key = 'clave_secreta_ot_frtdf_2026' 
DB_NAME = 'auditorias.db'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS legajos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_entrada TEXT,
            nro_legajo TEXT UNIQUE,
            nombre TEXT,
            revisor_asignado TEXT,
            recepcion_documentos TEXT DEFAULT 'sí',
            nro_remito_recepcion TEXT,
            revision TEXT DEFAULT 'no',
            aviso_auditoria TEXT DEFAULT 'no',
            insercion_firmas TEXT DEFAULT 'no',
            pase_a_definitivo TEXT DEFAULT 'no',
            nro_remito_envio TEXT,
            devolucion_ba TEXT DEFAULT 'no',
            nro_certificado TEXT
        )
    ''')
    # NUEVA TABLA: Usuarios para el control de acceso
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            contrasena_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# PROTECTOR DE PANTALLAS: Verifica la sesión antes de cargar cualquier ruta
@app.before_request
def comprobar_autenticacion():
    # Rutas que no requieren haber iniciado sesión obligatoriamente
    rutas_publicas = ['login', 'registro', 'static']
    if request.endpoint not in rutas_publicas and 'usuario' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT contrasena_hash FROM usuarios WHERE usuario = ?", (usuario,))
        res = c.fetchone()
        conn.close()
        
        # Validamos que el usuario exista y la contraseña coincida con su hash encriptado
        if res and check_password_hash(res[0], contrasena):
            session['usuario'] = usuario # Guardamos el usuario en la sesión activa
            return redirect(url_for('index'))
            
        return render_template('login.html', error="Usuario o contraseña incorrectos.")
        
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        # Encriptación segura de la contraseña
        hash_contrasena = generate_password_hash(contrasena)
        
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO usuarios (usuario, contrasena_hash) VALUES (?, ?)", (usuario, hash_contrasena))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('registro.html', error="El nombre de usuario ya se encuentra registrado.")
            
    return render_template('registro.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None) # Destruye la sesión activa
    return redirect(url_for('login'))

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM legajos", conn)
        legajos = df.to_dict('records')
    except:
        legajos = []
    conn.close()
    # Pasamos el nombre del usuario logueado a la plantilla
    return render_template('index.html', legajos=legajos, usuario_actual=session.get('usuario'))

@app.route('/nuevo_legajo', methods=['POST'])
def nuevo_legajo():
    nro_legajo = request.form['nro_legajo']
    nombre = request.form['nombre']
    revisor = request.form['revisor']
    fecha = request.form['fecha_entrada'] 
    archivo = request.files['archivo_pdf']
    
    # 1. VALIDACIÓN: Que la fecha no sea a futuro
    fecha_ingresada = datetime.strptime(fecha, "%Y-%m-%d").date()
    hoy = datetime.now().date()
    if fecha_ingresada > hoy:
        flash("Error: La fecha de ingreso no puede ser posterior al día de hoy.", "error")
        return redirect(url_for('index'))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT id FROM legajos WHERE nro_legajo = ?", (nro_legajo,))
    existe = c.fetchone()
    
    if existe:
        conn.close()
        # MENSAJE FLASH DE ERROR
        flash(f"Error: El legajo {nro_legajo} ya se encuentra registrado.", "error")
        return redirect(url_for('index'))

    if archivo:
        nombre_archivo = f"{nro_legajo}_{archivo.filename}"
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))

    c.execute('''
        INSERT INTO legajos (fecha_entrada, nro_legajo, nombre, revisor_asignado, recepcion_documentos)
        VALUES (?, ?, ?, ?, 'sí')
    ''', (fecha, nro_legajo, nombre, revisor))
    
    conn.commit()
    conn.close()
    
    # MENSAJE FLASH DE ÉXITO
    flash(f"El legajo {nro_legajo} se cargó correctamente.", "success")
    return redirect(url_for('index'))

def obtener_legajos():
    """Función auxiliar para leer la tabla de legajos rápidamente."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM legajos", conn)
        legajos = df.to_dict('records')
    except:
        legajos = []
    conn.close()
    return legajos

@app.route('/generar_remito_recepcion', methods=['POST'])
def generar_remito_recepcion():
    """Filtra los legajos sin remito, genera el HTML y actualiza la BD."""
    nuevo_nro_remito = request.form['nuevo_nro_remito']
    archivo_firma = request.form['firmante'] # Captura el nombre del archivo de imagen seleccionado
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # VALIDACIÓN: Controlar que el nro de remito de recepción no exista
    c.execute("SELECT id FROM legajos WHERE nro_remito_recepcion = ?", (nuevo_nro_remito,))
    if c.fetchone():
        flash(f"Error: El remito de recepción {nuevo_nro_remito} ya fue utilizado en el sistema.", "error")
        conn.close()
        return redirect(url_for('index'))

    # Filtramos con Pandas los que entraron pero no tienen remito asignado
    df = pd.read_sql_query(
        "SELECT * FROM legajos WHERE recepcion_documentos='sí' AND nro_remito_recepcion IS NULL", 
        conn
    )
    
    if not df.empty:
        # Actualizamos la base de datos
        c = conn.cursor()
        c.execute('''
            UPDATE legajos 
            SET nro_remito_recepcion = ? 
            WHERE recepcion_documentos='sí' AND nro_remito_recepcion IS NULL
        ''', (nuevo_nro_remito,))
        conn.commit()
        
        legajos_remito = df.to_dict('records')
        conn.close()
        
        # Renderizamos el HTML del remito con los datos inyectados
        return render_template('remito_recepcion.html', 
                               nro_remito=nuevo_nro_remito, 
                               fecha=datetime.now().strftime("%d/%m/%Y"),
                               legajos=legajos_remito,
                               firma_imagen=archivo_firma)
    
    conn.close()
    return "No hay legajos pendientes de remito."

@app.route('/generar_remito_envio', methods=['POST'])
def generar_remito_envio():
    """Filtra los legajos que YA tienen certificado de Bs As y genera el remito para Gas Austral."""
    nuevo_nro_remito = request.form['nro_remito_envio']
    archivo_firma = request.form['firmante']
    
    conn = sqlite3.connect(DB_NAME)
    
    # VALIDACIÓN: Controlar que el nro de remito de envío no exista
    c = conn.cursor()
    c.execute("SELECT id FROM legajos WHERE nro_remito_envio = ?", (nuevo_nro_remito,))
    if c.fetchone():
        flash(f"Error: El remito de envío {nuevo_nro_remito} ya fue generado anteriormente.", "error")
        conn.close()
        return redirect(url_for('index'))

    # EL CAMBIO CLAVE: Buscamos legajos devueltos por BA (con certificado) que no tengan remito asignado
    df = pd.read_sql_query(
        "SELECT * FROM legajos WHERE devolucion_ba='sí' AND nro_remito_envio IS NULL", 
        conn
    )
    
    if not df.empty:
        c = conn.cursor()
        # Guardamos el número de remito de entrega en la base de datos
        c.execute('''
            UPDATE legajos 
            SET nro_remito_envio = ? 
            WHERE devolucion_ba='sí' AND nro_remito_envio IS NULL
        ''', (nuevo_nro_remito,))
        conn.commit()
        
        legajos_remito = df.to_dict('records')
        conn.close()
        
        # Generamos el documento final
        return render_template('remito_envio.html', 
                               nro_remito=nuevo_nro_remito, 
                               fecha=datetime.now().strftime("%d/%m/%Y"),
                               legajos=legajos_remito,
                               firma_imagen=archivo_firma)
    
    conn.close()
    return "No hay legajos con certificados registrados pendientes de entrega."

@app.route('/registrar_respuesta_ba', methods=['POST'])
def registrar_respuesta_ba():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ids = request.form.getlist('id_legajo')
    
    hubo_error = False
    
    for legajo_id in ids:
        certificado = request.form.get(f'cert_{legajo_id}', '').strip()
        
        if certificado:
            # 1. VALIDACIÓN ESTRUCTURAL (Formato y Año)
            # \d{5} exige exactamente 5 números. (\d{4}) captura el año de 4 dígitos.
            patron = r'^UTN-\d{5}/(\d{4})/404-G$'
            match = re.match(patron, certificado)
            
            if not match:
                flash(f"Error: El certificado {certificado} no respeta la estructura requerida (UTN-00000/Año/404-G).", "error")
                hubo_error = True
                continue
                
            anio_cert = int(match.group(1)) # Extrae el año que pusimos entre paréntesis
            anio_actual = datetime.now().year
            
            if anio_cert < 2022 or anio_cert > anio_actual:
                flash(f"Error: El año del certificado {certificado} debe estar entre 2022 y {anio_actual}.", "error")
                hubo_error = True
                continue

            # 2. VALIDACIÓN DE DUPLICADO (Tu código actual)
            c.execute("SELECT nro_legajo FROM legajos WHERE nro_certificado = ? AND id != ?", (certificado, legajo_id))
            duplicado = c.fetchone()
            
            if duplicado:
                flash(f"Error: El certificado {certificado} ya está asignado al legajo {duplicado[0]}.", "error")
                hubo_error = True
                continue 
                
            # 3. ACTUALIZACIÓN (Tu código actual)
            c.execute("UPDATE legajos SET nro_certificado = ?, devolucion_ba = 'sí' WHERE id = ?", (certificado, legajo_id))
            
    conn.commit()
    conn.close()
    
    # MENSAJE FLASH DE ÉXITO (solo si no hubo errores en el lote)
    if not hubo_error:
        flash("Los certificados se actualizaron correctamente.", "success")
        
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>')
def eliminar_legajo(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Obtener el número de legajo antes de borrar el registro
    c.execute("SELECT nro_legajo FROM legajos WHERE id = ?", (id,))
    resultado = c.fetchone()
    
    if resultado:
        nro_legajo = resultado[0]
        ruta_carpetas = app.config['UPLOAD_FOLDER']
        
        # 2. Escanear la carpeta de descargas/subidas
        if os.path.exists(ruta_carpetas):
            for nombre_archivo in os.listdir(ruta_carpetas):
                # Filtramos todos los archivos que comiencen con el número de legajo
                # (Ej: "1024_acta.pdf", "1024_informe.pdf", "1024_listado.pdf")
                if nombre_archivo.startswith(f"{nro_legajo}_") or nombre_archivo == nro_legajo:
                    ruta_completa = os.path.join(ruta_carpetas, nombre_archivo)
                    try:
                        os.remove(ruta_completa)
                        print(f"Archivo eliminado con éxito: {nombre_archivo}")
                    except Exception as e:
                        print(f"No se pudo eliminar el archivo físico {nombre_archivo}: {e}")
    
    # 3. Eliminar el registro de la base de datos
    c.execute("DELETE FROM legajos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/actualizar_estados', methods=['POST'])
def actualizar_estados():
    """Guarda los cambios de las casillas de verificación."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Obtenemos todos los IDs que están en la tabla actualmente
    ids = request.form.getlist('id_legajo')
    
    for legajo_id in ids:
        # Si el checkbox está marcado, recibimos 'sí', sino usamos 'no'
        revision = request.form.get(f'revision_{legajo_id}', 'no')
        aviso = request.form.get(f'aviso_{legajo_id}', 'no')
        firmas = request.form.get(f'firmas_{legajo_id}', 'no')
        definitivo = request.form.get(f'definitivo_{legajo_id}', 'no')
        
        c.execute('''
            UPDATE legajos 
            SET revision = ?, aviso_auditoria = ?, insercion_firmas = ?, pase_a_definitivo = ?
            WHERE id = ?
        ''', (revision, aviso, firmas, definitivo, legajo_id))
        
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_legajo(id):
    """Permite modificar los datos principales de un legajo técnico."""
    conn = sqlite3.connect(DB_NAME)
    
    if request.method == 'POST':
        # 1. Capturar los datos modificados desde el formulario de edición
        nuevo_nro = request.form['nro_legajo']
        nuevo_nombre = request.form['nombre']
        nuevo_revisor = request.form['revisor']
        
        c = conn.cursor()
        # 2. Actualizar el registro en la base de datos
        c.execute('''
            UPDATE legajos 
            SET nro_legajo = ?, nombre = ?, revisor_asignado = ?
            WHERE id = ?
        ''', (nuevo_nro, nuevo_nombre, nuevo_revisor, id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))
        
    else:
        # 3. Método GET: Buscar los datos actuales para precargarlos en la interfaz
        c = conn.cursor()
        c.execute("SELECT nro_legajo, nombre, revisor_asignado FROM legajos WHERE id = ?", (id,))
        res = c.fetchone()
        conn.close()
        
        if res:
            # Creamos un diccionario temporal para enviar a la plantilla
            legajo = {
                'id': id,
                'nro_legajo': res[0],
                'nombre': res[1],
                'revisor_asignado': res[2]
            }
            return render_template('editar.html', legajo=legajo)
            
        return "El legajo solicitado no fue encontrado."    

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
