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
* **Revisión / Aviso Auditoría / Firmas Insertadas:** Ve tildando las casillas según el progreso real del expediente.
* **Corregir datos:** Si un nombre u obra se tipeó mal, haz clic en el botón azul ✏️ **Editar** al final de la fila para corregirlo.
* **Eliminar:** Si un legajo se cargó por error, el botón rojo 🗑️ **Eliminar** borrará el registro y destruirá de forma segura sus archivos PDF del disco.
* **¡Muy Importante!** Al finalizar cada cambio en las casillas, recuerda presionar el botón verde **Guardar Estados** abajo de la tabla para asegurar los cambios.

### 🛫 Paso 4: Envío de paquetes al Centro Auditor (Buenos Aires)
Cuando un legajo pasa todos los controles de la facultad, se tilda la casilla **Pase a Definitivo** y se guardan los cambios. Para enviar el lote de expedientes aprobados a Buenos Aires:
1. Ve al bloque **Generar Remito de Envío**.
2. Escribe el número de remito de salida (ej. `ENV-2026-001`) y presiona el botón.
3. El sistema buscará de forma automática todos los legajos aprobados ("Definitivos") que aún no se hayan mandado, armará el remito de salida y estampará la firma seleccionada sobre la línea de puntos.

### 🏁 Paso 5: Retorno de Buenos Aires y Certificación Final
Cuando el Centro Auditor y la Secretaría de Energía devuelven el sobre con las aprobaciones:
1. Ve a la tabla del fondo llamada **Respuesta y Certificación (Buenos Aires)**. Allí solo verás los legajos que ya fueron enviados en remitos de salida.
2. Busca el legajo correspondiente y escribe en el casillero el **Nro. de Certificado** final que emitieron en Buenos Aires.
3. Haz clic en el botón **Registrar Certificados**. El estado cambiará automáticamente a **✅ Devuelto**, indicando que el ciclo del expediente ha concluido exitosamente y la documentación está lista para ser retirada por el cliente.

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
│   ├── 1.png               # Logo institucional UTN
│   ├── firma_Demian.png    # Firma digitalizada general
│
└── templates/              # Plantillas e interfaces HTML (Vistas)
    ├── login.html          # Pantalla de acceso restringido
    ├── registro.html       # Formulario de alta para nuevos operadores
    ├── index.html          # Panel de control y seguimiento central
    ├── editar.html         # Formulario de modificación de expedientes
    ├── remito_recepcion.html # Plantilla dinámica del remito de entrada
    └── remito_envio.html   # Plantilla dinámica del remito de salida (Entrega)


