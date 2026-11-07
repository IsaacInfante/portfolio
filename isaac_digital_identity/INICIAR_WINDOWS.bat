@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo PORTFOLIO / AGENT NETWORK
echo ===============================================
if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Preparando entorno virtual...
  py -m venv .venv
  if errorlevel 1 goto error
)
echo [2/4] Instalando dependencias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
if not defined PORTFOLIO_ENV_FILE if not exist ".env" copy ".env.example" ".env" >nul
echo [3/4] Comprobando configuracion y puerto local...
".venv\Scripts\python.exe" -c "import app, socket, sys; print('GEMINI_API_KEY_LOADED=' + str(bool(app.GEMINI_API_KEY))); port=app.app.config['PORT']; s=socket.socket(); s.settimeout(2); occupied=s.connect_ex(('127.0.0.1', port)) == 0; s.close(); print('El puerto ' + str(port) + ' ya esta ocupado. Cierra el servidor anterior antes de reiniciar.' if occupied else 'Puerto disponible.'); sys.exit(1 if occupied else 0)"
if errorlevel 1 goto error
echo [4/4] Iniciando Flask. Abre la direccion indicada por el servidor.
echo Para el acceso privado y la demostracion local, consulta docs/stage-1-windows.md.
".venv\Scripts\python.exe" app.py
if errorlevel 1 goto error
pause
exit /b 0
:error
echo No se inicio un servidor nuevo. Revisa el mensaje anterior.
echo Si faltan dependencias, comprueba Python 3.11+ y la conexion a Internet.
pause
exit /b 1
