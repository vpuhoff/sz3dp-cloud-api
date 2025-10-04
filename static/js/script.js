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
        
        // Добавляем визуальный индикатор обновления
        showUpdateIndicator();
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
    
    // Инициализируем полноэкранный режим
    initFullscreen();
    
    // Автоматическое обновление каждые 10 секунд
    setInterval(refreshData, 10000);
    
    // Первоначальная загрузка данных
    refreshData();
});
