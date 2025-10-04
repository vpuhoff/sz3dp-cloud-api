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
    'connection_status': 'Отключено',
    'camera_snapshot': None,
    'camera_enabled': False,
    'snapshot_last_update': 'Не обновлено'
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

def update_camera_snapshot():
    """Функция обновления снепшота камеры"""
    global printer_data
    
    try:
        logger.info("=== ОБНОВЛЕНИЕ СНЕПШОТА КАМЕРЫ ===")
        logger.info(f"Текущий статус камеры: {printer_data.get('camera_enabled', False)}")
        
        # Если камера еще не включена, пробуем включить
        if not printer_data.get('camera_enabled', False):
            logger.info("Камера не включена, пробуем включить...")
            camera_result = client.open_camera("ULJMGV")
            logger.info(f"Результат включения камеры: {camera_result}")
            
            if camera_result:
                printer_data['camera_enabled'] = True
                logger.info("✅ Камера успешно включена")
                # Небольшая задержка после включения камеры
                time.sleep(2)
            else:
                logger.warning("❌ Не удалось включить камеру")
                printer_data['camera_enabled'] = False
                printer_data['snapshot_last_update'] = time.strftime('%H:%M:%S')
                return
        else:
            logger.info("Камера уже включена, получаем снепшот...")
        
        # Получаем снепшот
        logger.info("Запрашиваем снепшот с камеры...")
        snapshot_data = client.get_printer_snapshot("ULJMGV")
        
        if snapshot_data:
            # Проверяем размер данных
            data_size = len(snapshot_data)
            logger.info(f"✅ Получен снепшот размером {data_size} символов")
            logger.info(f"Первые 100 символов: {snapshot_data[:100]}...")
            
            printer_data['camera_snapshot'] = snapshot_data
            printer_data['snapshot_last_update'] = time.strftime('%H:%M:%S')
            logger.info("✅ Снепшот камеры успешно сохранен")
        else:
            logger.warning("❌ Не удалось получить снепшот камеры (пустые данные)")
            printer_data['snapshot_last_update'] = time.strftime('%H:%M:%S')
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении снепшота камеры: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        printer_data['snapshot_last_update'] = time.strftime('%H:%M:%S')

# Настройка планировщика задач
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=update_printer_data,
    trigger=IntervalTrigger(seconds=30),
    id='update_printer_data',
    name='Обновление данных принтера каждые 30 секунд',
    replace_existing=True
)

# Планировщик для обновления снепшота камеры (реже, чем основные данные)
scheduler.add_job(
    func=update_camera_snapshot,
    trigger=IntervalTrigger(seconds=60),  # Каждую минуту
    id='update_camera_snapshot',
    name='Обновление снепшота камеры каждые 60 секунд',
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

@app.route('/api/camera/refresh')
def api_camera_refresh():
    """API endpoint для принудительного обновления снепшота камеры"""
    update_camera_snapshot()
    return jsonify({'status': 'success', 'message': 'Снепшот камеры обновлен'})

@app.route('/api/camera/enable')
def api_camera_enable():
    """API endpoint для принудительного включения камеры"""
    global printer_data
    try:
        logger.info("=== ПРИНУДИТЕЛЬНОЕ ВКЛЮЧЕНИЕ КАМЕРЫ ===")
        result = client.open_camera("ULJMGV")
        if result:
            printer_data['camera_enabled'] = True
            logger.info("✅ Камера включена через API")
            return jsonify({'status': 'success', 'message': 'Камера включена'})
        else:
            logger.warning("❌ Не удалось включить камеру через API")
            return jsonify({'status': 'error', 'message': 'Не удалось включить камеру'})
    except Exception as e:
        logger.error(f"❌ Ошибка при включении камеры через API: {e}")
        return jsonify({'status': 'error', 'message': f'Ошибка: {str(e)}'})

@app.route('/api/camera/debug')
def api_camera_debug():
    """API endpoint для отладочной информации о камере"""
    global printer_data
    try:
        debug_info = {
            'camera_enabled': printer_data.get('camera_enabled', False),
            'camera_snapshot_exists': bool(printer_data.get('camera_snapshot')),
            'camera_snapshot_size': len(printer_data.get('camera_snapshot', '')) if printer_data.get('camera_snapshot') else 0,
            'snapshot_last_update': printer_data.get('snapshot_last_update', 'Не обновлено'),
            'last_update': printer_data.get('last_update', 'Не обновлено'),
            'connection_status': printer_data.get('connection_status', 'Неизвестно'),
            'client_authenticated': client.is_authenticated,
            'client_base_url': client.base_url
        }
        
        logger.info("=== ОТЛАДОЧНАЯ ИНФОРМАЦИЯ КАМЕРЫ ===")
        logger.info(f"Debug info: {debug_info}")
        
        return jsonify(debug_info)
    except Exception as e:
        logger.error(f"❌ Ошибка при получении отладочной информации: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    try:
        # Первоначальное обновление данных
        update_printer_data()
        
        # Первоначальная попытка включить камеру
        logger.info("Попытка включить камеру при запуске...")
        update_camera_snapshot()
        
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
