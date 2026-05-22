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
│   ├── firma_oficina.png   # Firma digitalizada general
│   └── firma_ruben.png     # Firma digitalizada del verificador técnico
│
└── templates/              # Plantillas e interfaces HTML (Vistas)
    ├── login.html          # Pantalla de acceso restringido
    ├── registro.html       # Formulario de alta para nuevos operadores
    ├── index.html          # Panel de control y seguimiento central
    ├── editar.html         # Formulario de modificación de expedientes
    ├── remito_recepcion.html # Plantilla dinámica del remito de entrada
    └── remito_envio.html   # Plantilla dinámica del remito de salida (Entrega)


