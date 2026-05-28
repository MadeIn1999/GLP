# Sistema de Gestión de Auditorías de GLP - Oficina Técnica UTN FRTDF

Este software es una aplicación web local desarrollada en Python utilizando el entorno web **Flask** y **Pandas** para la automatización del flujo de trabajo de control, verificación y seguimiento de legajos técnicos de instalaciones de GLP. 

El sistema actúa como nexo documental entre la empresa instaladora (**Gas Austral S.A.**), el **Centro Auditor de la Universidad Tecnológica Nacional** en Buenos Aires y la **Secretaría de Energía**.

## 📌 Características Principales

* **Control de Acceso Seguro:** Sistema de inicio de sesión y registro de operadores técnicos con encriptación de contraseñas mediante hashing (`werkzeug.security`).
* **Gestión de Expedientes (CRUD):** Carga, modificación y eliminación lógica y física de legajos técnicos.
* **Procesamiento por Lotes (Batch Processing):** Filtrado inteligente de datos mediante Pandas para agrupar expedientes según su estado actual.
* **Generación de Remitos Dinámicos:** Inyección automatizada de datos a través de Jinja2 sobre plantillas institucionales HTML preexistentes para remitos de Recepción y Entrega.
* **Limpieza Automatizada:** Al eliminar un legajo, el sistema purga de forma física los documentos PDF anexados (actas, informes, listados de verificación) del almacenamiento local del servidor.
* **Firmas Digitales Seleccionables:** Selector interactivo para determinar qué firma autorizada e imagen transparente se estampa sobre las líneas de puntos del documento final.

## 📖 Manual de Uso para el Operador Técnico (Paso a Paso)

Este sistema digitaliza y organiza el camino que recorre cada expediente de GLP. A continuación se detalla cómo operar el sistema según el estado del trámite en la realidad.

### ➡️ Paso 1: Llega documentación física o digital de Gas Austral
Cuando la empresa ingresa un nuevo trámite a la facultad:
1. Inicia sesión con tu usuario y contraseña.
2. En el primer bloque (**Ingresar Nuevo Legajo**), completa los campos:
   * **Nro de Legajo:** El código identificador que trae el expediente.
   * **Razón Social:** El nombre de la obra o instalación.
   * **Revisor Asignado:** El técnico a cargo de la verificación (por ejemplo, `Rubén`).
   * **Fecha de Ingreso:** Por defecto muestra el día de hoy, pero puedes hacer clic para seleccionar una fecha pasada si estás registrando un historial antiguo.
3. Adjunta el archivo PDF correspondiente y haz clic en **Cargar Legajo**. El expediente aparecerá inmediatamente en la tabla de abajo.

### 📄 Paso 2: Emitir el comprobante de recepción
Para entregarle a Gas Austral un remito institucional que certifique que la Oficina Técnica recibió sus carpetas:
1. Ve al bloque **Generar Remito de Recepción**.
2. Escribe el número de remito correspondiente (ej. `REC-2026-001`).
3. En el menú desplegable, selecciona quién firma el documento (ej. `Demian Ferreyra`).
4. Haz clic en **Generar Remito**. Se abrirá una pestaña nueva lista para imprimir o guardar como PDF. *El sistema asociará automáticamente este número de remito a todos los legajos que estaban pendientes de ingreso.*

### 🛠️ Paso 3: Trabajo interno y control de avance
A medida que el equipo técnico (junto con el revisor asignado) avanza en el análisis de las instalaciones de GLP, debes mantener actualizada la tabla central (**Seguimiento Interno y Control**):
* **Revisión / Aviso Auditoría / Firmas Insertadas:** Ve tildando las casillas según el progreso real del expediente. (Puedes usar los enlaces de "📝 Llenar formulario" para agilizar las notificaciones).
* **Corregir datos:** Si un nombre u obra se tipeó mal, haz clic en el botón azul ✏️ **Editar** al final de la fila para corregirlo.
* **Eliminar:** Si un legajo se cargó por error, el botón rojo 🗑️ **Eliminar** borrará el registro y destruirá de forma segura sus archivos PDF del disco.
* **Pase a Definitivo:** Una vez aprobado el control en la facultad, tilda esta opción. El expediente pasará físicamente a enviarse a Buenos Aires.
* **¡Muy Importante!** Al finalizar cada cambio en las casillas, recuerda presionar el botón verde **Guardar Estados** abajo de la tabla para asegurar los cambios.

### 🏁 Paso 4: Retorno de Buenos Aires y Certificación Final
Cuando el Centro Auditor y la Secretaría de Energía devuelven el correo con los 4 documentos finales aprobados:
1. Ve a la tabla del fondo llamada **Respuesta y Certificación (Buenos Aires)**. Allí verás los legajos que enviamos en el paso anterior.
2. Busca el legajo correspondiente y escribe en el casillero el **Nro. de Certificado** emitido (ej. `UTN-00000/Año/404-G`).
3. Haz clic en el botón **Registrar Certificados**. El estado cambiará automáticamente a **✅ Certificado**, habilitando el legajo para su devolución al cliente.

### 🛫 Paso 5: Devolución a Gas Austral (Remito de Envío)
Para devolver la documentación final ya certificada a la empresa instaladora:
1. Ve al bloque **Generar Remito de Envío (Centro Auditor)**.
2. Escribe el número de remito de salida (ej. `ENV-2026-001`) y presiona el botón.
3. El sistema buscará de forma automática todos los legajos que ya tienen su certificado cargado y armará el remito de entrega final para Gas Austral.

## 📂 Estructura del Proyecto

```text
sistema-def/
│
├── app.py                  # Motor principal de la aplicación (Flask + SQLite)
├── auditorias.db           # Base de datos local (se genera automáticamente)
│
├── uploads/                # Directorio de almacenamiento para PDFs técnicos
│
├── static/                 # Archivos estáticos del sistema
│   ├── 1.png               # Logo institucional Oficina Técnica
│   ├── firma_Demian.png    # Firma digitalizada general (Demian)
│
└── templates/              # Plantillas e interfaces HTML (Vistas)
    ├── login.html          # Pantalla de acceso restringido
    ├── registro.html       # Formulario de alta para nuevos operadores
    ├── index.html          # Panel de control y seguimiento central
    ├── editar.html         # Formulario de modificación de expedientes
    ├── remito_recepcion.html # Plantilla dinámica del remito de entrada
    └── remito_envio.html   # Plantilla dinámica del remito de salida (Entrega)
```
## Requisitos e Instalación
1. Configurar el entorno: Asegurarse de tener Python instalado. Abrir una terminal en la carpeta sistema-def.
2. Instalar dependencias: Ejecutar el siguiente comando para instalar el motor web y el gestor de datos:
`pip install flask pandas`
3. Ejecutar el sistema:
`python app.py`
4. Acceso: Abrir navegador de internet (el de confianza) e ingresar a `http://127.0.0.1:5000`
