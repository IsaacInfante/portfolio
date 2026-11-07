# Portfolio Federation v1 — etapa 1

Estado: identidad, autenticación y privacidad locales. No hay descubrimiento,
firmas de agentes, transporte federado ni autorización entre propietarios todavía.
La negociación existente se conserva como **Demostración local**: un servidor
realiza seis turnos y una síntesis con su propia configuración Gemini.

## Configuración y aislamiento

`PORTFOLIO_ENV_FILE` selecciona un archivo privado independiente. Si no se define,
se lee `.env` junto a `app.py`. El archivo se lee con UTF-8/BOM y nunca se reescribe.
Las variables del proceso tienen prioridad; no se hace interpolación de `$`.
Un archivo seleccionado inexistente provoca un error, sin caer silenciosamente
en la configuración de otro propietario.

| Variable | Uso |
|---|---|
| `OWNER_PROFILE_PATH` | JSON propietario; predeterminado `data/isaac.json`. Requiere `id`, `name` y `role`. |
| `DATABASE_PATH` | SQLite exclusiva de esta instancia. Predeterminado `data/profiles.db`. |
| `INSTANCE_ID` | UUID técnico independiente del ID público. Vacío: se genera y persiste en SQLite. |
| `SECRET_KEY` | Secreto aleatorio de al menos 32 caracteres; autentica los identificadores de sesión. |
| `OWNER_PASSWORD_HASH` | Hash scrypt generado con la herramienta, nunca contraseña en texto plano. |
| `SESSION_COOKIE_SECURE` | `true` por defecto. `false` permite acceso privado por HTTP únicamente en localhost/127.0.0.1. |
| `PORT` | Puerto de esta instancia. |
| `PUBLIC_BASE_URL` | Origen canónico para QR y comprobación de Origin, sin ruta ni barra final. |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Configuración local de Gemini, sin cambios de proveedor ni llamadas entre servidores. |

Las rutas relativas de perfiles y SQLite se resuelven respecto a la carpeta de
`app.py`, independientemente del directorio de inicio. El archivo indicado por
`PORTFOLIO_ENV_FILE` también sigue esta regla si su ruta es relativa.

SQLite registra `INSTANCE_ID`, ID del propietario y ruta del perfil. Rechaza
una configuración que intente reutilizar esa base con otro perfil o UUID.
Conserva la base para mantener la identidad; no copies una base entre estudiantes.
Mover el perfil a otra ruta requiere una migración deliberada de sus metadatos;
no se reasigna silenciosamente la propiedad.

## Dos instancias en Windows

Desde PowerShell, dentro de `isaac_digital_identity`, con el entorno virtual
instalado según el README:

```powershell
python -m pip install -r requirements.txt
```

Prepara el JSON real y autorizado del segundo estudiante, fuera de los archivos
públicos `static/`. No copies la identidad ni los datos profesionales de Isaac
para presentarlos como propios. Usa su nombre, su ID y sus proyectos reales.
Los campos de presentación admiten el mismo esquema que `data/isaac.json`.

Crea dos configuraciones NUEVAS. Ajusta la ruta del perfil B a un archivo real:

```powershell
python configure_owner.py --output .env.owner-a --profile data/isaac.json --database instances/a/profiles.db --port 5001 --local-http
python configure_owner.py --output .env.owner-b --profile C:/ruta/privada/perfil-b.json --database instances/b/profiles.db --port 5002 --local-http
```

La herramienta pide y confirma cada contraseña sin mostrarla; exige al menos
14 caracteres. Genera secretos e IDs separados, no ofrece credenciales por
defecto y rechaza sobrescribir archivos o usar `.env` como salida. No lee ni copia
tu clave Gemini. Los archivos nuevos dejan Gemini sin configurar: si quieres la
demostración, añade privadamente la clave de cada propietario a su archivo.

No subas esos archivos ni las bases a Git. `.env`, `.env.*` e `instances/` están
ignorados; `.env.example` sigue siendo versionable. Los permisos del sistema de
archivos deben restringir estos archivos a la cuenta que ejecuta Portfolio.

Abre dos terminales separadas, ambas en `isaac_digital_identity`:

**Terminal A**

```powershell
$env:PORTFOLIO_ENV_FILE = (Resolve-Path .env.owner-a).Path
python app.py
```

**Terminal B**

```powershell
$env:PORTFOLIO_ENV_FILE = (Resolve-Path .env.owner-b).Path
python app.py
```

También puedes ejecutar `INICIAR_WINDOWS.bat` en cada terminal después de definir
la variable: respeta el archivo seleccionado y detecta un puerto ocupado.
Si existen variables heredadas como `DATABASE_PATH`, `OWNER_PROFILE_PATH`,
`INSTANCE_ID` o `PORT`, prevalecerán sobre los archivos: elimínalas de esas
terminales o configúralas conscientemente. No compartas una misma configuración.

Visita `http://127.0.0.1:5001` y `http://127.0.0.1:5002`. Cada uno debe mostrar su
propietario; `/api/status` contiene IDs de instancia diferentes y
`federation_enabled=false`. Las cookies tienen nombres diferentes por instancia,
aunque ambas usen el mismo host. Los QR locales abren su puerto correspondiente;
un teléfono no puede acceder al localhost de tu computadora.

En el módulo del agente usa **Acceso propietario** e introduce la contraseña que
elegiste. El portafolio, sus proyectos, QR y vCard siguen siendo públicos.
Crear invitados, conectar y ejecutar Gemini requieren sesión y CSRF.
No hay usuarios ni contraseñas predeterminados. Si falta el hash o el secreto,
las operaciones privadas permanecen deshabilitadas y el portafolio sigue visible.

## Datos públicos, candidatos y reglas privadas

`profile_privacy.py` usa listas explícitas, incluso en proyectos y habilidades:

- **Públicos:** identidad profesional y campos de presentación existentes;
  formación, experiencia, certificaciones, proyectos, habilidades, ubicación,
  fotografía y correo profesional. El correo conserva la compatibilidad del
  portafolio anterior: inclúyelo solo si deseas publicarlo.
- **Candidatos para colaboración:** ID, nombre, rol, objetivo, intereses,
  habilidades y proyectos. No constituyen una autorización. Solo el propietario
  puede inspeccionarlos en `GET /api/owner/profile`.
- **Privados:** restricciones del agente. No se incluyen en respuestas públicas,
  QR o vCard. Contraseñas, claves Gemini y secretos no forman parte del perfil
  exportable ni de la respuesta privada del propietario.

Los invitados de la demostración publican por defecto únicamente identidad,
especialidad y habilidades. Esto también se aplica a invitados antiguos: sus
objetivos se duplicaban en descripciones de proyecto y no deben publicarse por
esa vía. Sus registros completos siguen disponibles internamente para la demo
autorizada, sin convertir esos objetivos en proyectos profesionales reales.

`phone`, `constraints`, `privacy`, configuraciones y campos desconocidos quedan
excluidos de las respuestas públicas. Los campos anidados desconocidos también.
El HTML inicial usa el perfil filtrado: no introduce la identidad de Isaac ni
su correo como datos estáticos en el portfolio de otra persona.

Para reducir la publicación puedes añadir al JSON propietario:

```json
"privacy": {
  "public_fields": [
    "short_name", "initials", "subtitle", "about", "manifesto", "location",
    "education", "experience", "certifications", "projects", "skills", "languages"
  ]
}
```

ID, nombre y rol siempre son públicos. Este ejemplo oculta correo y fotografía;
la vCard respeta la misma selección. Eliminar un dato ahora no retira copias que
ya se hayan compartido. Reinicia el proceso para aplicar cambios en el JSON.

## Autenticación y CSRF

- `GET /api/owner/session` crea una sesión anónima breve y entrega su CSRF.
- `POST /api/owner/login` recibe JSON y `X-CSRF-Token`; rota sesión y token al autenticar.
- Sesión autenticada: 30 minutos, sin renovación automática. Sesión anónima: 10 minutos.
- `POST /api/owner/logout` revoca la sesión en SQLite; una cookie copiada ya no sirve.
- Las mutaciones requieren sesión autenticada y `X-CSRF-Token` correspondiente.
- Se comprueban `Origin` y `Sec-Fetch-Site`. No se habilita CORS de credenciales.
- Cookies opacas, host-only, `HttpOnly`, `SameSite=Strict` y `Secure` por defecto.
- Límite persistente de cinco intentos de login por dirección cada cinco minutos,
  más límite global. No se confía en `X-Forwarded-For` enviado por el cliente.
- Los secretos y contraseñas nunca se registran ni se devuelven. Cambiar el hash
  o secreto invalida las sesiones anteriores al reiniciar.

Producción requiere HTTPS y almacenamiento persistente. Si TLS termina en un
proxy, configura el servidor WSGI para reconocer únicamente el esquema HTTPS de
ese proxy confiable (`request.is_secure` debe ser verdadero). No confíes en
cabeceras reenviadas de cualquier cliente. Configura `PUBLIC_BASE_URL` con el
origen externo exacto. El modo HTTP privado no se permite por IP de LAN.

## Demostración local y alcance pendiente

El botón **Autorizar demostración** envía `demo_consent=true`, además de sesión
y CSRF. Autoriza el uso de los datos profesionales y condiciones de esos perfiles
en Gemini, exclusivamente para esta demostración. El invitado debe consentir
previamente el registro de sus datos; esta etapa todavía no verifica su identidad.
Se exige que uno de los participantes sea el propietario local.
Cerrar sesión impide las siguientes llamadas del intercambio; una petición ya
enviada a Gemini puede finalizar y no se puede retirar del proveedor.

No existen aún sesiones federadas, firmas, QR con autorización, presupuestos
diarios de Gemini ni negociación entre servidores. El historial de la demo sigue
siendo transitorio. No habilites exposición pública masiva de la demostración
sin los presupuestos y controles de consumo previstos para las próximas etapas.

## Validación

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app.py settings.py owner_auth.py profile_privacy.py configure_owner.py tests
```

Las pruebas emplean perfiles y contraseñas de prueba, bases temporales y mocks de
Gemini. Incluyen aislamiento, identidad persistente, acceso, CSRF, expiración,
revocación, privacidad de vCard/HTML/JSON y cierre de SQLite en éxito y rollback.
No demuestran una llamada real a Gemini ni comunicación federada.
