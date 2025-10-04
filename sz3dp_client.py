import requests
import json
import time
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SZ3DPCloudClient:
    """Клиент для работы с API cloud.sz3dp.com"""
    
    def __init__(self, email: str, password: str, base_url: str = "https://cloud.sz3dp.com"):
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.is_authenticated = False
        
    def login(self) -> bool:
        """Авторизация на сайте"""
        try:
            # Устанавливаем cookies из curl запроса для имитации авторизованной сессии
            # Эти cookies получены из реального запроса
            cookies = {
                'langcookie': 'ru-RU',
                'login_code': self.email,
                'goSessionid': 'QNzsJwfiyiae8r5o_zl_4DTn_0j32Gap1tfe-S6je8o=',  # Временная сессия
                'autoLogin': 'false',
                'pwd': '',
                'menuclass': ".sidemenu1[name='menuMyPrinter']",
                'iframcookie': 'printerDetail.html?regcode=ULJMGV&name=Flashforge%205m&measure=220x220x220'
            }
            
            # Устанавливаем cookies в сессию
            for name, value in cookies.items():
                self.session.cookies.set(name, value, domain='.sz3dp.com')
            
            # Пробуем получить главную страницу для проверки авторизации
            response = self.session.get(f"{self.base_url}/")
            response.raise_for_status()
            
            # Проверяем, авторизованы ли мы
            if self._check_login_success(response):
                self.is_authenticated = True
                logger.info("Успешная авторизация с cookies")
                return True
            
            # Если cookies не работают, пробуем стандартную авторизацию
            logger.info("Cookies не работают, пробуем стандартную авторизацию")
            return self._try_standard_login()
            
        except Exception as e:
            logger.error(f"Ошибка при авторизации: {e}")
            return False
    
    def _try_standard_login(self) -> bool:
        """Стандартная попытка авторизации"""
        try:
            # Используем правильный endpoint для авторизации
            endpoint = "/user/login"
            
            # Подготавливаем данные в правильном формате
            data = {
                "UserID": self.email,
                "Password": self.password
            }
            
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'no-cache',
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'dnt': '1',
                'origin': self.base_url,
                'pragma': 'no-cache',
                'referer': f'{self.base_url}/login.html',
                'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-requested-with': 'XMLHttpRequest'
            }
            
            # Отправляем данные в формате JSON как raw data
            json_data = f'{{"UserID":"{self.email}","Password":"{self.password}"}}'
            
            logger.info(f"Попытка авторизации через {endpoint}")
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                data=json_data,
                headers=headers
            )
            
            logger.info(f"Ответ авторизации: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"Ответ сервера: {response_data}")
                    
                    # Проверяем успешность авторизации
                    if response_data.get('ErrorCode') == 200 or response_data.get('success'):
                        self.is_authenticated = True
                        logger.info("Успешная авторизация")
                        return True
                    else:
                        logger.error(f"Ошибка авторизации: {response_data.get('Message', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"Ошибка парсинга ответа авторизации: {e}")
                    # Если не JSON, проверяем HTML
                    if self._check_login_success(response):
                        self.is_authenticated = True
                        logger.info("Успешная авторизация (HTML ответ)")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка при стандартной авторизации: {e}")
            return False
    
    def _try_ajax_login(self) -> bool:
        """Попытка авторизации через AJAX endpoints"""
        ajax_endpoints = [
            '/api/login',
            '/api/auth/login',
            '/login',
            '/auth/login',
            '/user/login',
            '/api/user/login',
            '/api/account/login'
        ]
        
        for endpoint in ajax_endpoints:
            try:
                # Пробуем разные варианты данных
                data_variants = [
                    {'email': self.email, 'password': self.password},
                    {'username': self.email, 'password': self.password},
                    {'login': self.email, 'password': self.password},
                    {'user': self.email, 'pass': self.password},
                    {'email': self.email, 'pwd': self.password}
                ]
                
                for data in data_variants:
                    headers = {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        headers=headers
                    )
                    
                    if response.status_code in [200, 201, 302]:
                        if self._check_login_success(response):
                            self.is_authenticated = True
                            logger.info(f"Успешная авторизация через {endpoint}")
                            return True
                            
            except Exception as e:
                logger.debug(f"Ошибка при попытке входа через {endpoint}: {e}")
                continue
                
        return False
    
    def _check_login_success(self, response) -> bool:
        """Проверка успешности авторизации по ответу"""
        # Проверяем редирект на главную страницу
        if response.status_code == 302:
            location = response.headers.get('Location', '')
            if '/dashboard' in location or '/main' in location or '/' == location:
                return True
        
        # Проверяем содержимое ответа
        try:
            if response.headers.get('Content-Type', '').startswith('application/json'):
                data = response.json()
                return data.get('success', False) or data.get('status') == 'success'
        except:
            pass
        
        # Проверяем HTML ответ на наличие признаков успешной авторизации
        if response.headers.get('Content-Type', '').startswith('text/html'):
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем признаки успешной авторизации
            success_indicators = [
                'dashboard', 'main', 'home', 'welcome', 'logout'
            ]
            
            page_text = soup.get_text().lower()
            for indicator in success_indicators:
                if indicator in page_text:
                    return True
            
            # Проверяем отсутствие формы логина
            login_form = soup.find('form')
            if not login_form:
                return True
        
        return False
    
    def get_printer_status(self, registration_code: str = "ULJMGV") -> Optional[Dict[str, Any]]:
        """Получение статуса принтера"""
        if not self.is_authenticated:
            if not self.login():
                return None
                
        try:
            # Используем правильный API endpoint для получения статуса принтера
            endpoint = "/user/printer"
            
            # Подготавливаем данные запроса в правильном формате
            data = {
                "Cmd": "GetPrinterStatus",
                "Parameters": {
                    "RegistrationCode": registration_code
                }
            }
            
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'x-requested-with': 'XMLHttpRequest',
                'origin': self.base_url,
                'referer': f'{self.base_url}/printerDetail.html?regcode={registration_code}'
            }
            
            logger.info(f"Запрос статуса принтера {registration_code}")
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                data=f'{{"Cmd":"GetPrinterStatus","Parameters":{{"RegistrationCode":"{registration_code}"}}}}',
                headers=headers
            )
            
            if response.status_code == 200:
                try:
                    api_data = response.json()
                    if api_data.get('ErrorCode') == 200:
                        return self._parse_printer_status(api_data)
                    else:
                        logger.error(f"API вернул ошибку: {api_data.get('Message', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Ошибка парсинга JSON ответа: {e}")
            else:
                logger.error(f"HTTP ошибка: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ошибка при получении статуса принтера: {e}")
            
        return None
    
    def _parse_printer_status(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Парсинг данных статуса принтера из API ответа"""
        detail = api_data.get('Detail', {})
        
        # Извлекаем температуры экструдера
        cur_temps = detail.get('CurTemps', [0, 0])
        target_temps = detail.get('TargetTemps', [0, 0])
        
        extruder_temp = {
            'current': cur_temps[0] if len(cur_temps) > 0 else 0,
            'target': target_temps[0] if len(target_temps) > 0 else 0
        }
        
        # Температура стола
        bed_temp = {
            'current': detail.get('PlatformCurTemp', 0),
            'target': detail.get('PlatformTargetTemp', 0)
        }
        
        # Прогресс печати (умножаем на 100 для отображения в процентах и округляем)
        progress_percent = round(detail.get('PrintProgress', 0) * 100, 2)
        
        # Время оставшееся (в минутах)
        estimate_time = detail.get('EstimateTime', 0)
        time_remaining = self._format_time(estimate_time)
        
        # Статус корпуса (Door: 0 = закрыт, 1 = открыт)
        door_status = detail.get('Door', 0)
        enclosure_status = "закрыт" if door_status == 0 else "открыт"
        
        # Статус филамента
        filament_status = "нормальный" if detail.get('Filament', 0) == 0 else "проблема"
        
        return {
            'model_name': detail.get('GcodeName', '').replace('.gcode', ''),
            'progress_percent': progress_percent,
            'time_remaining': time_remaining,
            'extruder_temp': extruder_temp,
            'bed_temp': bed_temp,
            'enclosure_status': enclosure_status,
            'filament_status': filament_status,
            'printer_name': detail.get('PrinterName', ''),
            'registration_code': detail.get('RegistrationCode', ''),
            'firmware_version': detail.get('FirmwareVersion', ''),
            'printer_type': detail.get('PrinterType', ''),
            'measure': detail.get('Measure', ''),
            'job_status': detail.get('JobStatus', ''),
            'duration': detail.get('Duration', 0),
            'raw_data': api_data
        }
    
    def _format_time(self, minutes: float) -> str:
        """Форматирование времени из минут в читаемый вид"""
        if minutes <= 0:
            return "0 мин"
        
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        
        if hours > 0:
            return f"{hours} ч {mins} мин"
        else:
            return f"{mins} мин"
    
    def _parse_status_html(self, html: str) -> Dict[str, Any]:
        """Парсинг HTML для извлечения статуса принтера"""
        soup = BeautifulSoup(html, 'html.parser')
        
        status_data = {
            'model_name': '',
            'progress_percent': 0,
            'time_remaining': '',
            'extruder_temp': {'current': 0, 'target': 0},
            'bed_temp': {'current': 0, 'target': 0},
            'enclosure_status': '',
            'filament_status': '',
            'raw_html': html
        }
        
        # Ищем данные о модели
        model_elements = soup.find_all(string=lambda text: text and 'voron_design_cube' in text.lower())
        if model_elements:
            status_data['model_name'] = str(model_elements[0]).strip()
            
        # Ищем процент прогресса
        progress_elements = soup.find_all(string=lambda text: text and '%' in text)
        for element in progress_elements:
            try:
                percent = float(str(element).replace('%', '').strip())
                if 0 <= percent <= 100:
                    status_data['progress_percent'] = percent
                    break
            except:
                continue
                
        # Ищем время оставшееся
        time_elements = soup.find_all(string=lambda text: text and ('h' in text.lower() or 'min' in text.lower()) and ('remaining' in text.lower() or 'left' in text.lower()))
        if time_elements:
            status_data['time_remaining'] = str(time_elements[0]).strip()
            
        # Ищем температуры
        temp_elements = soup.find_all(string=lambda text: text and '°C' in text)
        for element in temp_elements:
            try:
                temp_text = str(element).strip()
                if '/' in temp_text:
                    parts = temp_text.split('/')
                    if len(parts) == 2:
                        current = float(parts[0].replace('°C', '').strip())
                        target = float(parts[1].replace('°C', '').strip())
                        
                        # Определяем тип температуры по контексту
                        parent = element.parent
                        if parent:
                            parent_text = parent.get_text().lower()
                            if 'extruder' in parent_text or 'hotend' in parent_text:
                                status_data['extruder_temp'] = {'current': current, 'target': target}
                            elif 'bed' in parent_text:
                                status_data['bed_temp'] = {'current': current, 'target': target}
            except:
                continue
                
        # Ищем статус корпуса
        enclosure_elements = soup.find_all(string=lambda text: text and ('closed' in text.lower() or 'open' in text.lower()))
        for element in enclosure_elements:
            parent = element.parent
            if parent and ('enclosure' in parent.get_text().lower() or 'door' in parent.get_text().lower()):
                status_data['enclosure_status'] = str(element).strip()
                break
                
        # Ищем статус филамента
        filament_elements = soup.find_all(string=lambda text: text and 'normal' in text.lower())
        for element in filament_elements:
            parent = element.parent
            if parent and 'filament' in parent.get_text().lower():
                status_data['filament_status'] = str(element).strip()
                break
                
        return status_data
    
    def get_printers_list(self) -> Optional[list]:
        """Получение списка принтеров"""
        if not self.is_authenticated:
            if not self.login():
                return None
                
        try:
            endpoints = [
                '/api/printers',
                '/api/printer/list',
                '/api/devices',
                '/printers',
                '/devices'
            ]
            
            for endpoint in endpoints:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    if response.status_code == 200:
                        try:
                            return response.json()
                        except:
                            # Если не JSON, парсим HTML
                            soup = BeautifulSoup(response.text, 'html.parser')
                            printers = []
                            # Логика парсинга списка принтеров из HTML
                            return printers
                except Exception as e:
                    logger.debug(f"Ошибка при запросе {endpoint}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка при получении списка принтеров: {e}")
            
        return []
    
    def open_camera(self, registration_code: str = "ULJMGV") -> bool:
        """Включение камеры принтера"""
        if not self.is_authenticated:
            logger.info("Не авторизован, пробуем авторизоваться...")
            if not self.login():
                logger.error("Не удалось авторизоваться для включения камеры")
                return False
                
        try:
            endpoint = "/user/printer"
            
            data = {
                "Cmd": "OpenCamera",
                "Parameters": {
                    "RegistrationCode": registration_code
                }
            }
            
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'x-requested-with': 'XMLHttpRequest',
                'origin': self.base_url,
                'referer': f'{self.base_url}/printerDetail.html?regcode={registration_code}'
            }
            
            request_data = f'{{"Cmd":"OpenCamera","Parameters":{{"RegistrationCode":"{registration_code}"}}}}'
            logger.info(f"=== ВКЛЮЧЕНИЕ КАМЕРЫ ===")
            logger.info(f"Принтер: {registration_code}")
            logger.info(f"URL: {self.base_url}{endpoint}")
            logger.info(f"Данные запроса: {request_data}")
            
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                data=request_data,
                headers=headers
            )
            
            logger.info(f"Статус ответа: {response.status_code}")
            logger.info(f"Заголовки ответа: {dict(response.headers)}")
            logger.info(f"Текст ответа: {response.text[:500]}...")
            
            if response.status_code == 200:
                try:
                    api_data = response.json()
                    logger.info(f"JSON ответ: {api_data}")
                    
                    if api_data.get('ErrorCode') == 200:
                        logger.info("✅ Камера успешно включена")
                        return True
                    else:
                        logger.error(f"❌ Ошибка включения камеры: {api_data.get('Message', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"❌ Ошибка парсинга JSON ответа включения камеры: {e}")
                    logger.error(f"Ответ сервера: {response.text}")
            else:
                logger.error(f"❌ HTTP ошибка при включении камеры: {response.status_code}")
                logger.error(f"Ответ сервера: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при включении камеры: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            
        return False
    
    def get_printer_snapshot(self, registration_code: str = "ULJMGV") -> Optional[str]:
        """Получение снепшота с камеры принтера"""
        if not self.is_authenticated:
            logger.info("Не авторизован, пробуем авторизоваться...")
            if not self.login():
                logger.error("Не удалось авторизоваться для получения снепшота")
                return None
                
        try:
            endpoint = "/user/printer"
            
            data = {
                "Cmd": "GetPrinterSnapshot",
                "Parameters": {
                    "RegistrationCode": registration_code
                }
            }
            
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'x-requested-with': 'XMLHttpRequest',
                'origin': self.base_url,
                'referer': f'{self.base_url}/printerDetail.html?regcode={registration_code}'
            }
            
            request_data = f'{{"Cmd":"GetPrinterSnapshot","Parameters":{{"RegistrationCode":"{registration_code}"}}}}'
            logger.info(f"=== ПОЛУЧЕНИЕ СНЕПШОТА ===")
            logger.info(f"Принтер: {registration_code}")
            logger.info(f"URL: {self.base_url}{endpoint}")
            logger.info(f"Данные запроса: {request_data}")
            
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                data=request_data,
                headers=headers
            )
            
            logger.info(f"Статус ответа: {response.status_code}")
            logger.info(f"Размер ответа: {len(response.text)} символов")
            
            if response.status_code == 200:
                try:
                    api_data = response.json()
                    logger.info(f"JSON структура ответа: {list(api_data.keys()) if isinstance(api_data, dict) else 'Не словарь'}")
                    
                    if api_data.get('ErrorCode') == 200:
                        snapshot_data = api_data.get('Snapshot', '')
                        if snapshot_data:
                            data_size = len(snapshot_data)
                            logger.info(f"✅ Снепшот успешно получен, размер: {data_size} символов")
                            logger.info(f"Начало данных: {snapshot_data[:50]}...")
                            return snapshot_data
                        else:
                            logger.warning("❌ Пустой снепшот от сервера")
                            logger.info(f"Полный ответ: {api_data}")
                    else:
                        logger.error(f"❌ API вернул ошибку: {api_data.get('Message', 'Unknown error')}")
                        logger.info(f"Полный ответ: {api_data}")
                except Exception as e:
                    logger.error(f"❌ Ошибка парсинга JSON ответа снепшота: {e}")
                    logger.error(f"Ответ сервера (первые 1000 символов): {response.text[:1000]}")
            else:
                logger.error(f"❌ HTTP ошибка при получении снепшота: {response.status_code}")
                logger.error(f"Ответ сервера: {response.text[:500]}")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при получении снепшота: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            
        return None

    def logout(self):
        """Выход из системы"""
        try:
            self.session.post(f"{self.base_url}/logout")
        except:
            pass
        self.is_authenticated = False
