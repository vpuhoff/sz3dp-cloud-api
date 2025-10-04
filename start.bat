@echo off
echo ===============================================
echo 3D Принтер - Мониторинг статуса
echo ===============================================
echo Запуск приложения...
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден. Установите Python 3.8+ и добавьте его в PATH
    pause
    exit /b 1
)

REM Устанавливаем зависимости если нужно
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активируем виртуальное окружение
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements.txt

REM Запускаем приложение
echo.
echo Запуск веб-приложения...
echo Веб-интерфейс будет доступен по адресу: http://localhost:5000
echo.
python run.py

pause
