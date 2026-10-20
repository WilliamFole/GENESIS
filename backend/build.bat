@echo off
echo =======================================================
echo A COMPILAR O SISTEMA GENESIS (AGUARDE...)
echo =======================================================

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo A limpar ficheiros antigos...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo A compilar o executavel...
python -m PyInstaller --onefile --noconsole --name "Genesis" ^
  --icon "icone.ico" ^
  --collect-all fastapi ^
  --collect-all uvicorn ^
  --collect-all pydantic ^
  --collect-all pydantic_settings ^
  --collect-all sqlalchemy ^
  --collect-all passlib ^
  --collect-all bcrypt ^
  --collect-all reportlab ^
  --collect-all qrcode ^
  --collect-all jose ^
  --collect-all multipart ^
  --collect-all cryptography ^
  --collect-all openpyxl ^
  --collect-all email_validator ^
  --hidden-import "pydantic.deprecated.decorator" ^
  --add-data "app;app" ^
  --add-data "frontend_dist;frontend_dist" ^
  --add-data "alembic;alembic" ^
  --add-data "alembic.ini;." ^
  run_server.py

echo A copiar ficheiro .env...
copy .env dist\.env

echo.
echo =======================================================
echo COMPILACAO CONCLUIDA! O executavel esta na pasta 'dist'.
echo =======================================================
pause