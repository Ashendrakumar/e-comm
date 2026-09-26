@echo off
rem  One-click: create Category\SKU - Name\ photo folders for every product.
rem  Double-click, or run:  scripts\create_product_folders.bat ["G:\My Drive\Product Images"]
rem  With no argument it uses PRODUCT_IMAGES_DIR from .env. Existing folders are kept.
setlocal
cd /d "%~dp0\.."
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

python manage.py create_product_folders %*
echo.
pause
