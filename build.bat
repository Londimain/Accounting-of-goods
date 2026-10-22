@echo off
chcp 65001 >nul
setlocal

set APP_NAME=Товарный расчёт
set APP_ICON=ico\app.ico
set ENTRY=inventory_tk.py

echo ========================================
echo  Очистка предыдущей сборки
echo ========================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%APP_NAME%.spec" del /q "%APP_NAME%.spec"
if exist "*.spec" del /q "*.spec"

echo.
echo ========================================
echo  Генерация встроенных иконок
echo ========================================
python generate_icons.py
if errorlevel 1 goto :error

echo.
echo ========================================
echo  Сборка EXE
echo ========================================
pyinstaller ^
    --onefile ^
    --windowed ^
    --clean ^
    --noconfirm ^
    --name "%APP_NAME%" ^
    --icon "%APP_ICON%" ^
    --hidden-import=PIL ^
    --hidden-import=Pillow ^
    --collect-all=PIL ^
    "%ENTRY%"
if errorlevel 1 goto :error

echo.
echo ========================================
echo  Готово!
echo  Файл: dist\%APP_NAME%.exe
echo ========================================
pause
exit /b 0

:error
echo.
echo [ОШИБКА] Сборка прервана.
pause
exit /b 1