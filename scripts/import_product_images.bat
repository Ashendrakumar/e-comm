@echo off
rem  One-click product photo import from Google Drive for desktop.
rem  Double-click, or run:  scripts\import_product_images.bat ["G:\My Drive\Product Images"]
rem  With no argument it uses PRODUCT_IMAGES_DIR from .env. See docs\PRODUCT_IMAGES.md.
setlocal
cd /d "%~dp0\.."
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

echo.
echo === Preview (nothing is saved yet) ===
python manage.py import_product_images %*
if errorlevel 1 goto end

echo.
set /p OK=Import these photos now? (y/N):
if /i "%OK%"=="y" (
  python manage.py import_product_images --apply %*
) else (
  echo Cancelled - nothing was imported.
)
:end
echo.
pause
