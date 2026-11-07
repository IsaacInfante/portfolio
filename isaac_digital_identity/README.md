# Portfolio | Isaac Infante Méndez

Portafolio visual y plataforma de networking con agentes autónomos de IA.

## Estado de la etapa 1

Identidad independiente, autenticación del propietario y privacidad implementadas. La negociación disponible es una **Demostración local**, protegida por sesión y CSRF; todavía no hay comunicación entre servidores. Sin credenciales configuradas, el portafolio público funciona y las operaciones privadas permanecen bloqueadas.

Consulta [la guía de dos instancias en Windows](docs/stage-1-windows.md) para configurar perfiles, SQLite, secretos y puertos separados sin sobrescribir tu `.env`.

## Arquitectura

- **Frontend:** HTML semántico, CSS responsive y JavaScript (sin framework ni compilador).
- **Backend:** Flask (Python).
- **Persistencia:** SQLite local de perfiles invitados y conexiones.
- **Código QR:** se genera dinámicamente desde el servidor con `qrcode`.
- **Capa agéntica:** Gemini API, con prompts y restricciones independientes para cada perfil; **6 turnos de agentes + 1 síntesis**. Los mensajes se producen mediante peticiones reales al modelo, se transmiten al navegador conforme se generan (SSE), y **no existen respuestas predefinidas**.
- **Presentación de resultado:** propuesta preliminar no vinculante, sujeta a validación humana.

## Instalación en VS Code

1. Abre esta carpeta en VS Code.
2. En la terminal:

   **Windows PowerShell**

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

   **Linux / macOS**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   test -f .env || cp .env.example .env
   ```

3. Para la negociación real, consigue una clave en https://aistudio.google.com/apikey y pégala en el archivo `.env`:

   ```env
   GEMINI_API_KEY=tu_clave_privada
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```

   La clave **nunca se coloca en el frontend ni se sube a Git**. Google puede cambiar modelos, planes, límites o disponibilidad: si recibes un error de modelo, actualiza `GEMINI_MODEL` a otro habilitado en tu cuenta.

4. Ejecuta:

   ```bash
   python app.py
   ```

5. Abre http://127.0.0.1:5000 .

**Importante:** El portafolio, las tarjetas, el QR y la creación/conexión de perfiles funcionan sin clave. **Crear perfiles, conectar y negociar requiere también configurar el acceso del propietario. La negociación NO funciona sin una clave válida de Gemini**; así evitamos aparentar artificialmente que existe una IA.

## Personalización

- **Datos profesionales:** edita `data/isaac.json`.
- **Tu fotografía real:** coloca una foto propia como `static/assets/profile.jpg` (deberás agregarla tú). Antes de eso verás un avatar diseñado con tus iniciales. Para que cumpla por completo el requisito de fotografía, añade la imagen antes de entregar.
- **Colores, tamaños y estética:** `static/styles.css`.
- **Contenido e interacciones:** `templates/index.html` y `static/app.js`.
- **Restricciones del agente:** `data/isaac.json` → `constraints`. Los valores actuales (por ejemplo, 5 h/semana) son **valores iniciales propuestos**, no extraídos del CV; ajústalos a tus preferencias reales antes de demostrar una negociación.
- **CV:** no se publica el PDF directamente porque incluye datos de contacto personales. Tú decides qué información hacer pública.

## Demostración local

Primero configura el acceso del propietario según la guía de etapa 1. Inicia sesión desde el módulo del agente, crea o conecta un perfil invitado autorizado y pulsa **Autorizar demostración**. Seis mensajes y una síntesis se generan en un único backend mediante Gemini. El portafolio, QR y vCard son públicos; crear perfiles, conectar y negociar requieren autenticación y CSRF. El segundo perfil es un invitado local y no tiene acceso de propietario.

Esta etapa permite ejecutar dos instancias independientes, pero no conectarlas entre sí. El descubrimiento y transporte federados quedan pendientes.

## QR desde un teléfono / publicación

El QR se genera con la URL desde donde se está visitando. Si la aplicación corre en `localhost`, el código apunta a `localhost`, que solo funciona en tu propia computadora. Opciones:

- Para una demo en la misma Wi-Fi, usa `http://IP-DE-TU-PC:5000` desde el teléfono; el firewall debe permitir el puerto 5000.
- Publica **todo el servicio Flask**, no solo los archivos HTML. En Render, configura un servicio web Python con build `pip install -r requirements.txt` y start `gunicorn --worker-class gthread --workers 1 --threads 8 --timeout 180 app:app`. Añade la variable `GEMINI_API_KEY` en el panel de secretos y `PUBLIC_BASE_URL=https://tu-dominio.com` si necesitas un QR canónico. Render gratuito puede hibernar y **perder archivos SQLite en reinicios**; para un proyecto persistente usa un hosting con volumen persistente o Postgres.

⚠️ **Privacidad y seguridad:** este es un proyecto académico, no una plataforma comercial autenticada. El formulario de invitados requiere ahora sesión del propietario y CSRF. No ingreses secretos, teléfonos privados ni datos sensibles de compañeros; valida su consentimiento. Antes de uso público amplio, añade los presupuestos de Gemini previstos y garantiza HTTPS y persistencia segura. Mantén la clave API solo en el servidor.

## Estructura

```
isaac_digital_identity/
├── app.py                 # Servidor, QR, registro y orquestación Gemini
├── templates/index.html   # UI del portafolio y networking
├── static/styles.css      # Identidad visual y responsive
├── static/app.js          # Interacción, vistas y streaming de agentes
├── static/assets/        # Favicon y fotografía que tú agregas
├── data/isaac.json        # CV transformado a perfil estructurado
├── data/profiles.db       # Se crea automáticamente, no se sube a Git
├── tests/                 # Pruebas básicas
├── requirements.txt
├── .env.example
└── Procfile
```

## Validar la instalación

```bash
python -m unittest discover -s tests -v
```

## Fuentes de información del portafolio

El contenido base procede del CV 2026 de Isaac Infante Méndez. Los proyectos son Monitoreo Industrial (en desarrollo), Monitoreo Climático y Máquina Expendedora Biométrica. Las visualizaciones son ilustrativas, no telemetría en vivo.

## Configuración y límites de Gemini

Se conserva gemini-3.5-flash-lite y el endpoint generateContent existente. GEMINI_MODEL permite seleccionar un modelo compatible con salida JSON. Consulta https://ai.google.dev/gemini-api/docs/pricing para confirmar el nivel gratuito, la disponibilidad y la cuota de tu proyecto. Cada negociación completa consume siete peticiones reales; no hay reintentos automáticos ni cambio automático a un modelo de pago. El estado configurado confirma la presencia de una clave, no su validez. La clave se lee exclusivamente del entorno del servidor; nunca se transmite al cliente.
