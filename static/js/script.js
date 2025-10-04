// JavaScript для дополнительной интерактивности
document.addEventListener('DOMContentLoaded', function() {
    console.log('3D Printer Status Monitor загружен');
    
    // Определяем мобильное устройство
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    // Добавляем класс для мобильных устройств
    if (isMobile || isTouchDevice) {
        document.body.classList.add('mobile-device');
    }
    
    // Предотвращаем зум при двойном тапе на мобильных
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // Функция для обновления данных через AJAX
    function refreshData() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                updateDisplay(data);
            })
            .catch(error => {
                console.error('Ошибка при обновлении данных:', error);
            });
    }
    
    // Функция для обновления отображения
    function updateDisplay(data) {
        // Обновляем статус подключения
        const statusElement = document.querySelector('.connection-status');
        if (statusElement) {
            statusElement.textContent = data.connection_status;
            statusElement.className = `connection-status ${data.connection_status === 'Подключено' ? 'connected' : 'disconnected'}`;
        }
        
        // Обновляем название модели
        const modelName = document.querySelector('.model-info h2');
        if (modelName) {
            modelName.textContent = `Модель: ${data.model_name}`;
        }
        
        // Обновляем прогресс-бар
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            const circumference = 2 * Math.PI * 45; // радиус 45
            const progress = (data.progress_percent / 100) * circumference;
            progressBar.style.strokeDasharray = `${progress} ${circumference}`;
        }
        
        // Обновляем процент прогресса
        const progressPercent = document.querySelector('.progress-percent');
        if (progressPercent) {
            progressPercent.textContent = `${data.progress_percent}%`;
        }
        
        // Обновляем время оставшееся
        const timeValue = document.querySelector('.time-value');
        if (timeValue) {
            timeValue.textContent = data.time_remaining;
        }
        
        // Обновляем параметры принтера по порядку
        const paramItems = document.querySelectorAll('.param-item');
        if (paramItems.length >= 4) {
            // Экструдер
            const extruderValue = paramItems[0].querySelector('.param-value');
            if (extruderValue) {
                extruderValue.textContent = `${data.extruder_temp.current}°C / ${data.extruder_temp.target}°C`;
            }
            
            // Стол
            const bedValue = paramItems[1].querySelector('.param-value');
            if (bedValue) {
                bedValue.textContent = `${data.bed_temp.current}°C / ${data.bed_temp.target}°C`;
            }
            
            // Корпус
            const enclosureValue = paramItems[2].querySelector('.param-value');
            if (enclosureValue) {
                enclosureValue.textContent = data.enclosure_status;
            }
            
            // Филамент
            const filamentValue = paramItems[3].querySelector('.param-value');
            if (filamentValue) {
                filamentValue.textContent = data.filament_status;
            }
        }
        
        // Обновляем время последнего обновления
        const lastUpdate = document.querySelector('.update-info p:first-child');
        if (lastUpdate) {
            lastUpdate.textContent = `Последнее обновление: ${data.last_update}`;
        }
        
        // Обновляем данные камеры
        updateCameraDisplay(data);
        
        // Добавляем визуальный индикатор обновления
        showUpdateIndicator();
    }
    
    // Функция для обновления отображения камеры
    function updateCameraDisplay(data) {
        console.log('=== ОБНОВЛЕНИЕ ОТОБРАЖЕНИЯ КАМЕРЫ ===');
        console.log('Данные камеры:', data);
        console.log('Статус камеры:', data.camera_enabled);
        console.log('Наличие снепшота:', !!data.camera_snapshot);
        console.log('Размер снепшота:', data.camera_snapshot ? data.camera_snapshot.length : 0);
        
        // Обновляем статус камеры
        const cameraStatus = document.querySelector('.camera-status');
        if (cameraStatus) {
            cameraStatus.textContent = data.camera_enabled ? 'Камера включена' : 'Камера отключена';
            cameraStatus.className = `camera-status ${data.camera_enabled ? 'enabled' : 'disabled'}`;
            console.log('Статус камеры обновлен в UI');
        } else {
            console.error('Элемент .camera-status не найден!');
        }
        
        // Обновляем изображение камеры
        const cameraImage = document.getElementById('camera-image');
        const cameraSnapshot = document.querySelector('.camera-snapshot');
        const cameraPlaceholder = document.querySelector('.camera-placeholder');
        const placeholderText = document.querySelector('.placeholder-text');
        
        console.log('Элементы DOM:');
        console.log('- cameraImage:', cameraImage);
        console.log('- cameraSnapshot:', cameraSnapshot);
        console.log('- cameraPlaceholder:', cameraPlaceholder);
        console.log('- placeholderText:', placeholderText);
        
        if (data.camera_snapshot && cameraImage) {
            // Обновляем существующее изображение
            console.log('Обновляем существующее изображение');
            const imageSrc = `data:image/jpeg;base64,${data.camera_snapshot}`;
            cameraImage.src = imageSrc;
            console.log('Новый src изображения установлен');
            
            if (cameraSnapshot) {
                cameraSnapshot.style.display = 'flex';
                console.log('cameraSnapshot показан');
            }
            if (cameraPlaceholder) {
                cameraPlaceholder.style.display = 'none';
                console.log('cameraPlaceholder скрыт');
            }
        } else if (data.camera_snapshot && cameraSnapshot && cameraPlaceholder) {
            // Создаем новое изображение если его нет
            console.log('Создаем новое изображение');
            const imageSrc = `data:image/jpeg;base64,${data.camera_snapshot}`;
            cameraSnapshot.innerHTML = `
                <img src="${imageSrc}" 
                     alt="Снепшот с камеры принтера" 
                     class="snapshot-image"
                     id="camera-image">
            `;
            cameraSnapshot.style.display = 'flex';
            cameraPlaceholder.style.display = 'none';
            console.log('Новое изображение создано и показано');
        } else if (cameraPlaceholder && placeholderText) {
            // Показываем placeholder
            console.log('Показываем placeholder');
            cameraPlaceholder.style.display = 'flex';
            if (cameraSnapshot) cameraSnapshot.style.display = 'none';
            
            if (data.camera_enabled) {
                placeholderText.textContent = 'Загрузка изображения...';
                console.log('Placeholder: Загрузка изображения...');
            } else {
                placeholderText.textContent = 'Камера не включена';
                console.log('Placeholder: Камера не включена');
            }
        } else {
            console.warn('Не удалось найти нужные DOM элементы для отображения камеры');
        }
        
        // Обновляем время последнего обновления камеры
        const cameraInfo = document.querySelector('.camera-info p:first-child');
        if (cameraInfo) {
            cameraInfo.textContent = `Последнее обновление камеры: ${data.snapshot_last_update}`;
        }
        
        // Обновляем состояние кнопок
        updateCameraButtons(data.camera_enabled);
    }
    
    // Функция для обновления состояния кнопок камеры
    function updateCameraButtons(cameraEnabled) {
        const enableBtn = document.getElementById('enable-camera-btn');
        const refreshBtn = document.getElementById('refresh-camera-btn');
        
        if (enableBtn) {
            if (cameraEnabled) {
                enableBtn.style.display = 'none';
            } else {
                enableBtn.style.display = 'flex';
            }
        }
        
        if (refreshBtn) {
            if (cameraEnabled) {
                refreshBtn.style.display = 'flex';
            } else {
                refreshBtn.style.display = 'none';
            }
        }
    }
    
    // Функция для показа индикатора обновления
    function showUpdateIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'update-indicator';
        indicator.textContent = '✓ Обновлено';
        
        // Добавляем стили для индикатора
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        
        document.body.appendChild(indicator);
        
        // Анимация появления и исчезновения
        setTimeout(() => {
            indicator.style.opacity = '1';
        }, 10);
        
        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        }, 2000);
    }
    
    // Добавляем кнопку принудительного обновления
    const updateButton = document.createElement('button');
    updateButton.textContent = 'Обновить сейчас';
    updateButton.className = 'refresh-button';
    updateButton.onclick = function() {
        fetch('/api/refresh')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Данные обновлены');
                    // Небольшая задержка для обновления данных
                    setTimeout(refreshData, 1000);
                }
            })
            .catch(error => {
                console.error('Ошибка при принудительном обновлении:', error);
            });
    };
    
    // Добавляем кнопку в update-buttons секцию
    const updateButtons = document.querySelector('.update-buttons');
    if (updateButtons) {
        updateButtons.appendChild(updateButton);
    }
    
    // Стили для кнопки обновления
    const style = document.createElement('style');
    style.textContent = `
        .refresh-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background-color 0.3s ease;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            min-height: 40px;
            min-width: 40px;
            touch-action: manipulation;
            white-space: nowrap;
        }
        
        .refresh-button:hover {
            background: #45a049;
        }
        
        .refresh-button:active {
            transform: translateY(1px);
            background: #3d8b40;
        }
        
        @media (max-width: 768px) {
            .refresh-button {
                padding: 8px 12px;
                font-size: 0.8rem;
                min-height: 36px;
            }
            
            .fullscreen-button {
                min-width: 36px;
                min-height: 36px;
                padding: 8px;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Функциональность полноэкранного режима
    function initFullscreen() {
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        const fullscreenIcon = fullscreenBtn.querySelector('.fullscreen-icon');
        
        if (!fullscreenBtn) return;
        
        // Проверяем поддержку полноэкранного режима
        const isFullscreenSupported = !!(document.fullscreenEnabled || 
                                        document.webkitFullscreenEnabled || 
                                        document.mozFullScreenEnabled || 
                                        document.msFullscreenEnabled);
        
        if (!isFullscreenSupported) {
            fullscreenBtn.style.display = 'none';
            return;
        }
        
        // Функция для входа в полноэкранный режим
        function enterFullscreen() {
            const element = document.documentElement;
            
            if (element.requestFullscreen) {
                element.requestFullscreen();
            } else if (element.webkitRequestFullscreen) {
                element.webkitRequestFullscreen();
            } else if (element.mozRequestFullScreen) {
                element.mozRequestFullScreen();
            } else if (element.msRequestFullscreen) {
                element.msRequestFullscreen();
            }
        }
        
        // Функция для выхода из полноэкранного режима
        function exitFullscreen() {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
        
        // Проверяем, находимся ли мы в полноэкранном режиме
        function isFullscreen() {
            return !!(document.fullscreenElement || 
                     document.webkitFullscreenElement || 
                     document.mozFullScreenElement || 
                     document.msFullscreenElement);
        }
        
        // Обработчик клика на кнопку
        fullscreenBtn.addEventListener('click', function() {
            if (isFullscreen()) {
                exitFullscreen();
            } else {
                enterFullscreen();
            }
        });
        
        // Обработчики событий изменения полноэкранного режима
        document.addEventListener('fullscreenchange', updateFullscreenButton);
        document.addEventListener('webkitfullscreenchange', updateFullscreenButton);
        document.addEventListener('mozfullscreenchange', updateFullscreenButton);
        document.addEventListener('MSFullscreenChange', updateFullscreenButton);
        
        // Функция обновления иконки кнопки
        function updateFullscreenButton() {
            if (isFullscreen()) {
                fullscreenIcon.textContent = '⛶';
                fullscreenBtn.title = 'Выйти из полноэкранного режима';
            } else {
                fullscreenIcon.textContent = '⛶';
                fullscreenBtn.title = 'Полноэкранный режим';
            }
        }
        
        // Обработчик клавиши Escape для выхода из полноэкранного режима
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && isFullscreen()) {
                exitFullscreen();
            }
        });
    }
    
    // Функция для включения камеры
    function enableCamera() {
        fetch('/api/camera/enable')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Камера включена');
                    showCameraIndicator('✓ Камера включена');
                    // Обновляем данные через небольшую задержку
                    setTimeout(refreshData, 2000);
                } else {
                    console.error('Ошибка включения камеры:', data.message);
                    showCameraIndicator('✗ ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка при включении камеры:', error);
                showCameraIndicator('✗ Ошибка подключения', 'error');
            });
    }
    
    // Функция для обновления снепшота камеры
    function refreshCameraSnapshot() {
        fetch('/api/camera/refresh')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Снепшот камеры обновлен');
                    showCameraIndicator('✓ Снепшот обновлен');
                    // Обновляем данные через небольшую задержку
                    setTimeout(refreshData, 1000);
                } else {
                    console.error('Ошибка обновления снепшота:', data.message);
                    showCameraIndicator('✗ ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка при обновлении снепшота:', error);
                showCameraIndicator('✗ Ошибка подключения', 'error');
            });
    }
    
    // Функция для показа индикатора камеры
    function showCameraIndicator(message, type = 'success') {
        const indicator = document.createElement('div');
        indicator.className = 'camera-indicator';
        indicator.textContent = message;
        
        // Добавляем стили для индикатора
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#f44336' : '#4CAF50'};
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 1001;
            opacity: 0;
            transition: opacity 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            max-width: 300px;
        `;
        
        document.body.appendChild(indicator);
        
        // Анимация появления и исчезновения
        setTimeout(() => {
            indicator.style.opacity = '1';
        }, 10);
        
        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        }, 3000);
    }
    
    // Функция для тестирования камеры
    function testCamera() {
        console.log('=== ТЕСТИРОВАНИЕ КАМЕРЫ ===');
        
        // Получаем отладочную информацию
        fetch('/api/camera/debug')
            .then(response => response.json())
            .then(debugInfo => {
                console.log('=== ОТЛАДОЧНАЯ ИНФОРМАЦИЯ ===');
                console.log('Debug info:', debugInfo);
                
                // Получаем текущий статус
                return fetch('/api/status');
            })
            .then(response => response.json())
            .then(data => {
                console.log('=== ТЕКУЩИЙ СТАТУС ===');
                console.log('Текущий статус:', data);
                console.log('Статус камеры:', data.camera_enabled);
                console.log('Наличие снепшота:', !!data.camera_snapshot);
                console.log('Размер снепшота:', data.camera_snapshot ? data.camera_snapshot.length : 0);
                
                if (!data.camera_enabled) {
                    console.log('Камера отключена, пробуем включить...');
                    enableCamera();
                } else {
                    console.log('Камера включена, пробуем получить снепшот...');
                    refreshCameraSnapshot();
                }
            })
            .catch(error => {
                console.error('Ошибка при тестировании камеры:', error);
            });
    }
    
    // Добавляем обработчики событий для кнопок камеры
    const enableCameraBtn = document.getElementById('enable-camera-btn');
    const refreshCameraBtn = document.getElementById('refresh-camera-btn');
    const testCameraBtn = document.getElementById('test-camera-btn');
    
    if (enableCameraBtn) {
        enableCameraBtn.addEventListener('click', enableCamera);
    }
    
    if (refreshCameraBtn) {
        refreshCameraBtn.addEventListener('click', refreshCameraSnapshot);
    }
    
    if (testCameraBtn) {
        testCameraBtn.addEventListener('click', testCamera);
    }
    
    // Инициализируем полноэкранный режим
    initFullscreen();
    
    // Автоматическое обновление каждые 10 секунд
    setInterval(refreshData, 10000);
    
    // Автоматическое обновление снепшота камеры каждые 60 секунд
    setInterval(() => {
        // Обновляем снепшот только если камера включена
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                if (data.camera_enabled) {
                    refreshCameraSnapshot();
                }
            })
            .catch(error => {
                console.error('Ошибка при проверке статуса камеры:', error);
            });
    }, 60000);
    
    // Первоначальная загрузка данных
    refreshData();
});
