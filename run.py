#!/usr/bin/env python3
"""
Скрипт для запуска приложения мониторинга 3D принтера
"""

import sys
import os

# Добавляем текущую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, update_printer_data, scheduler
import logging

def main():
    """Главная функция запуска"""
    print("=" * 50)
    print("3D Принтер - Мониторинг статуса")
    print("=" * 50)
    print("Запуск приложения...")
    print("Веб-интерфейс будет доступен по адресу: http://localhost:5000")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    try:
        # Первоначальное обновление данных
        print("Первоначальная загрузка данных...")
        update_printer_data()
        
        # Запуск планировщика
        scheduler.start()
        print("Планировщик задач запущен (обновление каждые 30 секунд)")
        
        # Запуск Flask приложения
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\nОстановка приложения...")
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
    finally:
        scheduler.shutdown()
        print("Приложение остановлено")

if __name__ == "__main__":
    main()
