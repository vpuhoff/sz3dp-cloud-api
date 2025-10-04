from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading
import time
import logging
from sz3dp_client import SZ3DPCloudClient
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Глобальные переменные для хранения данных
printer_data = {
    'model_name': 'Загрузка...',
    'progress_percent': 0,
    'time_remaining': 'Загрузка...',
    'extruder_temp': {'current': 0, 'target': 0},
    'bed_temp': {'current': 0, 'target': 0},
    'enclosure_status': 'Загрузка...',
    'filament_status': 'Загрузка...',
    'last_update': 'Не обновлено',
    'connection_status': 'Отключено'
}

# Инициализация клиента
client = SZ3DPCloudClient(
    email=app.config['EMAIL'],
    password=app.config['PASSWORD'],
    base_url=app.config['API_BASE_URL']
)

def update_printer_data():
    """Функция обновления данных принтера"""
    global printer_data
    
    try:
        logger.info("Обновление данных принтера...")
        status = client.get_printer_status("ULJMGV")  # Используем код принтера из curl
        
        if status:
            printer_data.update({
                'model_name': status.get('model_name', 'Неизвестная модель'),
                'progress_percent': status.get('progress_percent', 0),
                'time_remaining': status.get('time_remaining', 'Неизвестно'),
                'extruder_temp': status.get('extruder_temp', {'current': 0, 'target': 0}),
                'bed_temp': status.get('bed_temp', {'current': 0, 'target': 0}),
                'enclosure_status': status.get('enclosure_status', 'Неизвестно'),
                'filament_status': status.get('filament_status', 'Неизвестно'),
                'printer_name': status.get('printer_name', ''),
                'registration_code': status.get('registration_code', ''),
                'firmware_version': status.get('firmware_version', ''),
                'printer_type': status.get('printer_type', ''),
                'measure': status.get('measure', ''),
                'job_status': status.get('job_status', ''),
                'duration': status.get('duration', 0),
                'last_update': time.strftime('%H:%M:%S'),
                'connection_status': 'Подключено'
            })
            logger.info("Данные успешно обновлены")
            logger.info(f"Принтер: {status.get('printer_name', 'Unknown')} - {status.get('job_status', 'Unknown')}")
        else:
            printer_data['connection_status'] = 'Ошибка подключения'
            printer_data['last_update'] = time.strftime('%H:%M:%S')
            logger.warning("Не удалось получить данные принтера")
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных: {e}")
        printer_data['connection_status'] = f'Ошибка: {str(e)}'
        printer_data['last_update'] = time.strftime('%H:%M:%S')

# Настройка планировщика задач
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=update_printer_data,
    trigger=IntervalTrigger(seconds=30),
    id='update_printer_data',
    name='Обновление данных принтера каждые 30 секунд',
    replace_existing=True
)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html', data=printer_data)

@app.route('/api/status')
def api_status():
    """API endpoint для получения статуса принтера"""
    return jsonify(printer_data)

@app.route('/api/refresh')
def api_refresh():
    """API endpoint для принудительного обновления данных"""
    update_printer_data()
    return jsonify({'status': 'success', 'message': 'Данные обновлены'})

if __name__ == '__main__':
    try:
        # Первоначальное обновление данных
        update_printer_data()
        
        # Запуск планировщика
        scheduler.start()
        logger.info("Планировщик задач запущен")
        
        # Запуск Flask приложения
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=app.config['DEBUG'],
            use_reloader=False  # Отключаем reloader чтобы избежать конфликтов с scheduler
        )
        
    except KeyboardInterrupt:
        logger.info("Остановка приложения...")
    finally:
        scheduler.shutdown()
        logger.info("Планировщик остановлен")
