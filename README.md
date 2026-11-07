# Portfolio — Isaac Infante Méndez

Portafolio universitario y profesional desarrollado con Flask, HTML, CSS y
JavaScript. Presenta proyectos de software y sistemas embebidos y conserva una
demostración local de negociación entre agentes mediante Gemini.

La aplicación existente se encuentra en [`isaac_digital_identity/`](isaac_digital_identity/).
Se conserva esa estructura para mantener su compatibilidad.

## Funcionalidades actuales

- Perfil profesional, experiencia, formación, habilidades y proyectos.
- Interfaz responsive con visualizaciones técnicas y microinteracciones.
- QR del portafolio y descarga de contacto vCard.
- Configuración independiente de propietario, base SQLite e identidad de instancia.
- Acceso privado del propietario con scrypt, sesiones revocables y protección CSRF.
- Separación entre datos públicos, candidatos para colaboración y reglas del agente.
- Perfiles invitados para una **Demostración local**: seis mensajes y una síntesis
  generados por Gemini en un único backend, con autorización del propietario.

Proyectos: **Monitoreo Industrial**, **Monitoreo Climático** y
**Máquina Expendedora Biométrica**. Monitoreo Industrial continúa en desarrollo;
las visualizaciones son ilustrativas y no acreditan resultados experimentales.

## Ejecución en Windows

Desde la carpeta del repositorio:

```powershell
cd isaac_digital_identity
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe app.py
```

Abre `http://127.0.0.1:5000`. El portafolio público funciona sin clave Gemini ni
credenciales del propietario. Las operaciones privadas permanecen bloqueadas
hasta configurarlas; no hay contraseñas predeterminadas.

Para el acceso privado, configura una contraseña propia usando
`configure_owner.py`. La [guía de etapa 1](isaac_digital_identity/docs/stage-1-windows.md)
incluye los comandos para crear archivos privados nuevos y ejecutar **dos
instancias independientes** con perfiles, SQLite, secretos y puertos separados.

En Linux/macOS utiliza `python3 -m venv .venv` y `.venv/bin/python` en lugar del
intérprete de Windows.

## Gemini y privacidad

La clave se configura exclusivamente en el entorno del servidor o en un archivo
privado seleccionado mediante `PORTFOLIO_ENV_FILE`. El modelo se configura con
`GEMINI_MODEL`. No pongas credenciales en HTML, JavaScript, commits o capturas.

El botón de la demostración autoriza enviar los datos profesionales necesarios
a Gemini. El propietario debe tener autorización del invitado para registrar sus
datos. Las pruebas usan identidades sintéticas y no contienen datos de compañeros.

El perfil de ejemplo conserva los datos profesionales del autor. No se incluyen
bases de perfiles invitados, documentos internos de empresas ni configuraciones
privadas de cuentas. Antes de adaptar el proyecto, publica únicamente datos que
estés autorizado a compartir.

## Alcance y limitaciones

- Está implementada la **etapa 1 de Portfolio Federation v1**: identidad,
  autenticación y privacidad. **No hay transporte entre servidores todavía.**
- La demostración local usa un backend para representar ambos perfiles. No
  constituye evidencia de negociación federada entre dos aplicaciones.
- Las propuestas son preliminares y requieren aprobación humana; no crean
  compromisos legales, económicos ni profesionales.
- No hay presupuesto diario de Gemini ni historial persistente de negociaciones.
- Tener una clave configurada no demuestra que sea válida ni que exista cuota.
  La disponibilidad y el nivel gratuito dependen del proveedor y de la cuenta.
- Producción requiere HTTPS, SQLite en almacenamiento persistente y una
  configuración correcta del proxy. GitHub aloja el código; GitHub Pages no
  ejecuta este backend Flask.
- Un QR con localhost solo funciona en el equipo que ejecuta el servidor. Para
  compartir el portafolio configura una URL accesible mediante `PUBLIC_BASE_URL`.

## Pruebas

Desde `isaac_digital_identity/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q app.py settings.py owner_auth.py profile_privacy.py configure_owner.py tests
```

Las pruebas cubren autenticación, CSRF, privacidad, cierre de SQLite, aislamiento
y dos procesos Flask independientes. Las respuestas de Gemini se sustituyen
exclusivamente dentro de las pruebas, sin solicitudes reales al proveedor.

Consulta el [README de la aplicación](isaac_digital_identity/README.md) para más
detalles de arquitectura y configuración.

## Archivos excluidos

`.gitignore` excluye `.env`, configuraciones de instancia, claves privadas,
credenciales, entornos virtuales, SQLite, cachés, registros, herramientas locales
y archivos temporales. `.env.example` contiene únicamente nombres de variables
y valores de ejemplo seguros. Nunca agregues secretos usando `git add -f`.
