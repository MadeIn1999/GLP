import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
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
    """Recibe los datos del formulario, incluyendo la fecha elegida, y guarda el PDF."""
    nro_legajo = request.form['nro_legajo']
    nombre = request.form['nombre']
    revisor = request.form['revisor']
    # MODIFICACIÓN: Tomamos la fecha seleccionada por el usuario en el formulario
    fecha = request.form['fecha_entrada'] # Aseguramos que el campo de fecha se llene correctamente en el formulario HTML
    archivo = request.files['archivo_pdf']
    
    if archivo:
        nombre_archivo = f"{nro_legajo}_{archivo.filename}"
        archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO legajos (fecha_entrada, nro_legajo, nombre, revisor_asignado, recepcion_documentos)
        VALUES (?, ?, ?, ?, 'sí')
    ''', (fecha, nro_legajo, nombre, revisor))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/generar_remito_recepcion', methods=['POST'])
def generar_remito_recepcion():
    """Filtra los legajos sin remito, genera el HTML y actualiza la BD."""
    nuevo_nro_remito = request.form['nuevo_nro_remito']
    archivo_firma = request.form['firmante'] # Captura el nombre del archivo de imagen seleccionado
    conn = sqlite3.connect(DB_NAME)
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

@app.route('/generar_remito_envio', methods=['POST']) # Recomendado: usar 'envio' sin tilde en la URL
def generar_remito_envio():
    """Filtra los legajos aprobados para el Centro Auditor y genera el remito de salida."""
    # 1. Usar el nombre del campo que definimos en el HTML para el remito de salida
    nuevo_nro_remito = request.form['nro_remito_envio'] 
    archivo_firma = request.form['firmante'] 
    
    conn = sqlite3.connect(DB_NAME)
    
    # 2. FILTRO CRÍTICO: Solo legajos con pase_a_definitivo='sí' que NO tengan remito de envío aún
    df = pd.read_sql_query(
        "SELECT * FROM legajos WHERE pase_a_definitivo='sí' AND nro_remito_envio IS NULL", 
        conn
    )
    
    if not df.empty:
        c = conn.cursor()
        # 3. ACTUALIZACIÓN: Guardar el número de remito de ENVÍO
        c.execute('''
            UPDATE legajos 
            SET nro_remito_envio = ? 
            WHERE pase_a_definitivo='sí' AND nro_remito_envio IS NULL
        ''', (nuevo_nro_remito,))
        conn.commit()
        
        legajos_remito = df.to_dict('records')
        conn.close()
        
        # 4. PLANTILLA: Llamar a remito_envio.html en lugar del de recepción
        return render_template('remito_envio.html', 
                               nro_remito=nuevo_nro_remito, 
                               fecha=datetime.now().strftime("%d/%m/%Y"),
                               legajos=legajos_remito,
                               firma_imagen=archivo_firma)
    
    conn.close()
    return "No hay legajos con 'Pase a Definitivo' pendientes de envío."

@app.route('/registrar_respuesta_ba', methods=['POST'])
def registrar_respuesta_ba():
    """Registra el nro de certificado y confirma la devolución desde Bs. As."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    ids = request.form.getlist('id_legajo')
    
    for legajo_id in ids:
        # Capturamos el nro de certificado si se ingresó uno
        certificado = request.form.get(f'cert_{legajo_id}', '')
        # Si tiene certificado, marcamos la devolución como 'sí'
        devuelto = 'sí' if certificado else 'no'
        
        c.execute('''
            UPDATE legajos 
            SET nro_certificado = ?, devolucion_ba = ?
            WHERE id = ?
        ''', (certificado, devuelto, legajo_id))
        
    conn.commit()
    conn.close()
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
