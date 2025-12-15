"""AI-агент для тестирования AI-психолога через браузер"""
import asyncio
import time
import json
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import sys
import os

# Добавляем путь для импорта настроек
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import get_our_settings

our_settings = get_our_settings()
AI_API_KEY = our_settings.AI_API_KEY
AI_MODEL = our_settings.AI_MODEL


class PsychologistTestAgent:
    """Агент для тестирования AI-психолога через веб-интерфейс"""
    
    def __init__(self, base_url: str = "http://localhost:5003", headless: bool = False, continuous_mode: bool = False):
        self.base_url = base_url
        self.headless = headless
        self._continuous_mode = continuous_mode
        self.driver = None
        self.conversation_log = []
        self.errors_found = []
        self.test_username = "test_user"
        self.test_password = "test_pass_123"
        self.ai_api_key = AI_API_KEY
        self.ai_model = AI_MODEL
        
    def _log(self, message: str, level: str = "INFO"):
        """Логировать сообщение и отправлять в чат"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.conversation_log.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        
        # Отправляем в web_chat_viewer если доступен
        try:
            # Пробуем импортировать web_chat_viewer из корневой директории
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            from web_server import web_chat_viewer
            web_chat_viewer.add_agent_notification(
                title=f"🤖 Тест-агент психолога",
                message=message,
                notification_type="testing" if level == "INFO" else "error",
                details=log_entry
            )
        except Exception as e:
            # web_chat_viewer может быть недоступен - это нормально
            pass
    
    def _setup_driver(self):
        """Настроить Selenium WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(5)
            self._log("✅ WebDriver успешно инициализирован")
            return True
        except Exception as e:
            self._log(f"❌ Ошибка инициализации WebDriver: {e}", "ERROR")
            return False
    
    def _wait_for_element(self, by: By, value: str, timeout: int = 10):
        """Ожидать появления элемента"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self._log(f"⏱️ Таймаут ожидания элемента: {value}", "WARNING")
            return None
    
    def _find_element_by_multiple_selectors(self, selectors: List[tuple]) -> Optional:
        """Найти элемент по нескольким селекторам"""
        for by, value in selectors:
            try:
                element = self.driver.find_element(by, value)
                if element and element.is_displayed():
                    return element
            except:
                continue
        return None
    
    def _wait_for_clickable(self, by: By, value: str, timeout: int = 10):
        """Ожидать кликабельности элемента"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            self._log(f"⏱️ Таймаут ожидания кликабельности: {value}", "WARNING")
            return None
    
    def login(self) -> bool:
        """Войти в систему"""
        try:
            # Если мы не на странице входа, переходим туда
            current_url = self.driver.current_url if self.driver else ""
            if "login" not in current_url:
                self._log("🔐 Перехожу на страницу входа...")
                self.driver.get(f"{self.base_url}/login")
                time.sleep(2)
            else:
                self._log("🔐 Начинаю процесс входа...")
            
            # Находим поля ввода
            username_field = self._wait_for_element(By.ID, "username")
            password_field = self._wait_for_element(By.ID, "password")
            
            if not username_field or not password_field:
                self._log("❌ Не найдены поля ввода на странице входа", "ERROR")
                return False
            
            # Вводим данные
            username_field.clear()
            username_field.send_keys(self.test_username)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(self.test_password)
            time.sleep(0.5)
            
            # Нажимаем кнопку входа
            login_button = self._wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']")
            if login_button:
                login_button.click()
                time.sleep(3)
                
                # Проверяем, что мы на главной странице
                if "index" in self.driver.current_url or "chat" in self.driver.current_url:
                    self._log("✅ Успешный вход в систему")
                    return True
                else:
                    # Проверяем, есть ли ошибка на странице
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error-message, #errorMessage")
                        for error_elem in error_elements:
                            if error_elem.is_displayed() and error_elem.text:
                                error_text = error_elem.text
                                if "неверный" in error_text.lower() or "неправильный" in error_text.lower():
                                    self._log("⚠️ Неверный логин или пароль. Пробую зарегистрироваться...", "WARNING")
                                    return self._register()
                    except:
                        pass
                    
                    self._log("⚠️ Возможно, требуется регистрация. Пробую зарегистрироваться...", "WARNING")
                    return self._register()
            else:
                self._log("❌ Не найдена кнопка входа", "ERROR")
                return False
                
        except Exception as e:
            self._log(f"❌ Ошибка при входе: {e}", "ERROR")
            return False
    
    def _register(self) -> bool:
        """Зарегистрировать нового пользователя"""
        try:
            self._log("📝 Начинаю регистрацию...")
            self.driver.get(f"{self.base_url}/register")
            time.sleep(3)
            
            # Находим поля регистрации по разным селекторам
            username_field = self._find_element_by_multiple_selectors([
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.CSS_SELECTOR, "input[name='username']"),
            ])
            
            password_field = self._find_element_by_multiple_selectors([
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[name='password']"),
            ])
            
            confirm_password_field = self._find_element_by_multiple_selectors([
                (By.ID, "passwordConfirm"),
                (By.NAME, "passwordConfirm"),
                (By.CSS_SELECTOR, "input[name='passwordConfirm']"),
                (By.ID, "confirm_password"),
                (By.NAME, "confirm_password"),
                (By.CSS_SELECTOR, "input[type='password']:nth-of-type(2)"),
            ])
            
            if not username_field or not password_field:
                self._log("❌ Не найдены основные поля регистрации", "ERROR")
                return False
            
            # confirm_password может быть необязательным в некоторых версиях
            if not confirm_password_field:
                self._log("⚠️ Поле подтверждения пароля не найдено, продолжаю без него", "WARNING")
            
            # Вводим данные
            username_field.clear()
            username_field.send_keys(self.test_username)
            time.sleep(0.5)
            
            password_field.clear()
            password_field.send_keys(self.test_password)
            time.sleep(0.5)
            
            if confirm_password_field:
                confirm_password_field.clear()
                confirm_password_field.send_keys(self.test_password)
                time.sleep(0.5)
            
            # Нажимаем кнопку регистрации
            register_button = self._wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']")
            if register_button:
                # Прокручиваем к кнопке, если нужно
                self.driver.execute_script("arguments[0].scrollIntoView(true);", register_button)
                time.sleep(0.5)
                register_button.click()
                
                # Ждем обработки формы через JavaScript (fetch запрос)
                # Ожидаем либо редиректа, либо появления ошибки
                max_wait = 10
                waited = 0
                while waited < max_wait:
                    time.sleep(1)
                    waited += 1
                    current_url = self.driver.current_url
                    
                    # Проверяем, произошел ли редирект
                    if "index" in current_url or "chat" in current_url or current_url == f"{self.base_url}/" or current_url.endswith("/"):
                        self._log("✅ Успешная регистрация и вход")
                        return True
                    
                    # Проверяем, есть ли ошибка
                    try:
                        error_element = self.driver.find_element(By.ID, "errorMessage")
                        if error_element and error_element.is_displayed():
                            error_text = error_element.text
                            if error_text:
                                self._log(f"❌ Ошибка регистрации: {error_text}", "ERROR")
                                # Если пользователь уже существует, пробуем войти
                                if "уже существует" in error_text.lower() or "already exists" in error_text.lower():
                                    self._log("🔄 Пользователь уже существует, пробую войти...")
                                    # Переходим на страницу входа
                                    self.driver.get(f"{self.base_url}/login")
                                    time.sleep(2)
                                    # Пробуем войти с теми же данными
                                    username_field = self._wait_for_element(By.ID, "username")
                                    password_field = self._wait_for_element(By.ID, "password")
                                    if username_field and password_field:
                                        username_field.clear()
                                        username_field.send_keys(self.test_username)
                                        password_field.clear()
                                        password_field.send_keys(self.test_password)
                                        login_button = self._wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']")
                                        if login_button:
                                            login_button.click()
                                            time.sleep(5)
                                            if "index" in self.driver.current_url or "chat" in self.driver.current_url or self.driver.current_url.endswith("/"):
                                                self._log("✅ Успешный вход после регистрации")
                                                return True
                                return False
                    except:
                        pass
                
                # Если не произошел редирект и нет ошибки, возможно пользователь уже существует
                final_url = self.driver.current_url
                self._log(f"⚠️ Регистрация не завершилась. URL: {final_url}. Возможно, пользователь уже существует.", "WARNING")
                # Пробуем войти с этими данными
                self._log("🔄 Пробую войти с существующими данными...")
                return self.login()
            else:
                self._log("❌ Не найдена кнопка регистрации", "ERROR")
                return False
                
        except Exception as e:
            self._log(f"❌ Ошибка при регистрации: {e}", "ERROR")
            return False
    
    def create_new_session(self) -> bool:
        """Создать новую сессию чата"""
        try:
            self._log("➕ Ищу кнопку создания новой сессии...")
            
            # Пробуем разные способы найти кнопку
            new_session_button = None
            
            # Способ 1: По тексту в кнопках
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                btn_text = btn.text.strip()
                if "Новая сессия" in btn_text or "новая сессия" in btn_text.lower() or "новая" in btn_text.lower():
                    if btn.is_displayed() and btn.is_enabled():
                        new_session_button = btn
                        self._log(f"✅ Найдена кнопка по тексту: '{btn_text}'")
                        break
            
            # Способ 2: По селекторам
            if not new_session_button:
                selectors = [
                    "button:contains('Новая сессия')",
                    "#newSession",
                    ".new-session",
                    "button[id*='new']",
                    "button[class*='new']",
                ]
                for selector in selectors:
                    try:
                        btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if btn and btn.is_displayed() and btn.is_enabled():
                            new_session_button = btn
                            self._log(f"✅ Найдена кнопка по селектору: {selector}")
                            break
                    except:
                        continue
            
            if new_session_button:
                # Прокручиваем к кнопке
                self.driver.execute_script("arguments[0].scrollIntoView(true);", new_session_button)
                time.sleep(0.5)
                new_session_button.click()
                time.sleep(3)
                self._log("✅ Новая сессия создана")
                return True
            else:
                self._log("⚠️ Кнопка создания сессии не найдена, возможно сессия уже создана или не требуется", "WARNING")
                return True  # Возможно, сессия уже есть или не нужна
                
        except Exception as e:
            self._log(f"❌ Ошибка при создании сессии: {e}", "ERROR")
            import traceback
            self._log(traceback.format_exc(), "ERROR")
            return False
    
    def send_message(self, message: str) -> Optional[str]:
        """Отправить сообщение в чат и получить ответ"""
        try:
            self._log(f"💬 Отправляю сообщение: {message}")
            
            # Находим поле ввода по разным селекторам
            message_input = self._find_element_by_multiple_selectors([
                (By.ID, "messageInput"),
                (By.CSS_SELECTOR, "textarea"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[placeholder*='сообщение']"),
                (By.CSS_SELECTOR, "input[placeholder*='Напишите']"),
                (By.CSS_SELECTOR, "#message"),
            ])
            
            if not message_input:
                self._log("❌ Не найдено поле ввода сообщения", "ERROR")
                return None
            
            # Вводим сообщение
            message_input.clear()
            message_input.send_keys(message)
            time.sleep(0.5)
            
            # Нажимаем Enter или кнопку отправки
            try:
                # Пробуем найти кнопку отправки по разным селекторам
                send_button = None
                selectors = [
                    "#sendButton",
                    "button[type='button']",
                    ".send-button",
                    "button:has(svg)",
                ]
                for selector in selectors:
                    try:
                        send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if send_button and send_button.is_displayed():
                            break
                    except:
                        continue
                
                if send_button:
                    send_button.click()
                else:
                    message_input.send_keys(Keys.RETURN)
            except:
                # Если не нашли кнопку, просто нажимаем Enter
                message_input.send_keys(Keys.RETURN)
            
            time.sleep(3)  # Ждем ответа
            
            # Получаем последний ответ AI
            # Ждем появления нового сообщения
            time.sleep(2)
            
            try:
                # Пробуем разные селекторы для сообщений AI
                selectors = [
                    ".message.assistant",
                    ".ai-message",
                    ".message[data-role='assistant']",
                    ".message:has(.ai-label)",
                    ".chat-message.assistant",
                ]
                
                ai_messages = []
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            ai_messages = elements
                            break
                    except:
                        continue
                
                if ai_messages:
                    last_message = ai_messages[-1]
                    response_text = last_message.text.strip()
                    if response_text:
                        self._log(f"🤖 Ответ AI: {response_text[:100]}...")
                        return response_text
                
                # Если не нашли по селекторам, пробуем найти по тексту
                all_messages = self.driver.find_elements(By.CSS_SELECTOR, ".message, .chat-message")
                for msg in reversed(all_messages):
                    text = msg.text.strip()
                    if text and text != message:  # Не наше сообщение
                        self._log(f"🤖 Ответ AI (найден альтернативным способом): {text[:100]}...")
                        return text
                
                self._log("⚠️ Ответ AI не найден", "WARNING")
                return None
            except Exception as e:
                self._log(f"⚠️ Ошибка при получении ответа: {e}", "WARNING")
                return None
                
        except Exception as e:
            self._log(f"❌ Ошибка при отправке сообщения: {e}", "ERROR")
            return None
    
    def check_for_errors(self, user_message: str, ai_response: str) -> List[Dict]:
        """Проверить ответ на ошибки и вернуть детальную информацию"""
        errors = []
        
        if not ai_response or len(ai_response.strip()) == 0:
            errors.append({
                "type": "empty_response",
                "message": "Пустой ответ от AI",
                "severity": "high",
                "recommendation": "Проверить подключение к GPT API и логи обработки сообщений"
            })
        
        if "ошибка" in ai_response.lower() or "error" in ai_response.lower():
            errors.append({
                "type": "error_message",
                "message": "AI сообщил об ошибке",
                "severity": "high",
                "recommendation": "Проверить логи сервера и обработку ошибок в psychologist_ai.py"
            })
        
        # Проверка на дублирование вопросов
        if user_message and ai_response:
            user_words = set(user_message.lower().split())
            ai_words = set(ai_response.lower().split())
            # Если AI повторяет вопрос пользователя
            if len(user_words.intersection(ai_words)) > 3 and "?" in ai_response:
                errors.append({
                    "type": "duplicate_question",
                    "message": "AI дублирует вопрос пользователя",
                    "severity": "medium",
                    "recommendation": "Улучшить логику в handle_emotions_stage и handle_situations_stage, чтобы не задавать уже заданные вопросы"
                })
        
        # Проверка на некорректные вопросы (два вопроса одновременно)
        if "как вы себя чувствуете" in ai_response.lower() and "расскажите" in ai_response.lower() and "что происходит" in ai_response.lower():
            errors.append({
                "type": "double_question",
                "message": "AI задает два вопроса одновременно (дублирование)",
                "severity": "medium",
                "recommendation": "Исправить базовые ответы в handle_emotions_stage - убрать второй вопрос 'Что происходит в вашей жизни?'"
            })
        
        # Проверка на непонимание контекста
        if user_message and ai_response:
            # Если пользователь говорит о позитивных чувствах, а AI спрашивает о негативных
            positive_words = ["хорошо", "отлично", "нормально", "радость", "счастье", "хорошее", "хорошая"]
            negative_words_in_response = ["плохо", "тревога", "грусть", "беспокоит", "дискомфорт", "негативные", "проблемы"]
            
            if any(word in user_message.lower() for word in positive_words):
                if any(word in ai_response.lower() for word in negative_words_in_response):
                    errors.append({
                        "type": "context_misunderstanding",
                        "message": "AI не понимает контекст: пользователь говорит о позитивных чувствах, а AI спрашивает о негативных",
                        "severity": "high",
                        "recommendation": "Улучшить логику в handle_emotions_stage для обработки позитивных ответов. GPT должен получать четкие инструкции не предполагать негатив. Проверить системный промпт GPT."
                    })
            
            # Проверка: если пользователь уже описал ситуацию, а AI все еще спрашивает о ситуациях
            situation_keywords = ["работа", "начальник", "коллеги", "друзья", "семья", "отношения", "ситуация", "происходит", "случилось", "было"]
            if any(keyword in user_message.lower() for keyword in situation_keywords):
                if "ситуациях" in ai_response.lower() or "ситуации" in ai_response.lower() or "что происходит" in ai_response.lower():
                    # Но только если это не начало работы с идеей
                    if "разберем идею" not in ai_response.lower() and "система убеждений" not in ai_response.lower():
                        errors.append({
                            "type": "repeated_situation_question",
                            "message": "AI спрашивает о ситуациях повторно, хотя пользователь уже описал ситуацию",
                            "severity": "medium",
                            "recommendation": "Улучшить логику в handle_situations_stage. После получения ситуации нужно сразу переходить к работе с идеей, а не спрашивать еще раз."
                        })
            
            # Если пользователь уже ответил на вопрос, а AI задает его снова
            if "как вы себя чувствуете" in ai_response.lower() and len(user_message) > 3:
                # Проверяем, не ответил ли пользователь уже на этот вопрос
                emotion_indicators = ["плохо", "хорошо", "нормально", "тревога", "грусть", "радость", "чувствую"]
                if any(indicator in user_message.lower() for indicator in emotion_indicators):
                    errors.append({
                        "type": "repeated_question",
                        "message": "AI задает вопрос повторно, хотя пользователь уже ответил",
                        "severity": "high",
                        "recommendation": "Улучшить отслеживание состояния диалога. GPT должен видеть историю и не повторять вопросы."
                    })
        
        # Проверка на несоответствие этапу работы
        # Если пользователь описывает ситуацию, а AI все еще спрашивает об эмоциях
        situation_indicators = ["работа", "начальник", "ситуация", "происходит", "случилось"]
        if any(indicator in user_message.lower() for indicator in situation_indicators):
            if "как вы себя чувствуете" in ai_response.lower() or "эмоции" in ai_response.lower():
                errors.append({
                    "type": "wrong_stage",
                    "message": "AI не переходит к следующему этапу: пользователь описывает ситуацию, а AI все еще спрашивает об эмоциях",
                    "severity": "high",
                    "recommendation": "Исправить логику перехода между этапами в handle_emotions_stage и handle_situations_stage. GPT должен получать информацию о текущем этапе."
                })
        
        return errors
    
    async def run_test_scenario(self, scenario: List[str]) -> Dict:
        """Запустить тестовый сценарий"""
        self._log(f"🧪 Начинаю тестовый сценарий из {len(scenario)} сообщений")
        
        test_results = {
            "scenario": scenario,
            "responses": [],
            "errors": [],
            "timestamp": time.time()
        }
        
        comments_count = 0  # Счетчик комментариев
        max_comments = 3  # Максимальное количество комментариев перед "готово"
        
        for i, message in enumerate(scenario):
            self._log(f"📝 Шаг {i+1}/{len(scenario)}: {message[:50]}...")
            response = self.send_message(message)
            
            if response:
                # Проверяем, спрашивает ли AI о комментариях
                response_lower = response.lower()
                is_asking_for_comments = (
                    "комментари" in response_lower or 
                    "готово" in response_lower and "напишите" in response_lower or
                    "есть еще" in response_lower and "комментари" in response_lower
                )
                
                if is_asking_for_comments:
                    comments_count += 1
                    self._log(f"💬 AI спрашивает о комментариях (раз {comments_count})")
                    
                    # Если уже несколько раз спрашивает о комментариях, пишем "готово" вместо следующего сообщения
                    if comments_count >= max_comments:
                        self._log(f"✅ Автоматически пишу 'готово' после {comments_count} вопросов о комментариях")
                        time.sleep(1)
                        finish_response = self.send_message("готово")
                        if finish_response:
                            test_results["responses"].append({
                                "user_message": "готово",
                                "ai_response": finish_response,
                                "errors": []
                            })
                            # Проверяем ошибки в ответе на "готово"
                            errors = self.check_for_errors("готово", finish_response)
                            if errors:
                                test_results["errors"].extend(errors)
                                self.errors_found.extend(errors)
                                for error in errors:
                                    error_msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                                    self._log(f"⚠️ Найдена ошибка: {error_msg}", "WARNING")
                                    self._send_error_notification(error, "готово", finish_response)
                        # Сбрасываем счетчик
                        comments_count = 0
                        time.sleep(1.5)
                        # Пропускаем текущее сообщение из сценария, так как мы уже написали "готово"
                        continue
                
                errors = self.check_for_errors(message, response)
                test_results["responses"].append({
                    "user_message": message,
                    "ai_response": response,
                    "errors": errors
                })
                
                if errors:
                    test_results["errors"].extend(errors)
                    self.errors_found.extend(errors)
                    for error in errors:
                        error_msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
                        self._log(f"⚠️ Найдена ошибка: {error_msg}", "WARNING")
                        # Отправляем детальную информацию об ошибке
                        self._send_error_notification(error, message, response)
            else:
                self._log(f"⚠️ Не получен ответ на шаге {i+1}", "WARNING")
            
            # Пауза между сообщениями (уменьшена для длинного диалога)
            time.sleep(1.5)
        
        self._log(f"✅ Тестовый сценарий завершен. Найдено ошибок: {len(test_results['errors'])}")
        return test_results
    
    def _send_error_notification(self, error: Dict, user_message: str, ai_response: str):
        """Отправить детальное уведомление об ошибке"""
        error_type = error.get("type", "unknown")
        error_msg = error.get("message", "Неизвестная ошибка")
        severity = error.get("severity", "medium")
        recommendation = error.get("recommendation", "")
        
        # Всегда выводим в консоль
        self._log("=" * 60, "ERROR")
        self._log(f"🔴 НАЙДЕНА ОШИБКА: {error_msg}", "ERROR")
        self._log(f"   Тип: {error_type} | Серьезность: {severity}", "ERROR")
        self._log(f"   Сообщение пользователя: {user_message[:100]}", "ERROR")
        self._log(f"   Ответ AI: {ai_response[:200]}", "ERROR")
        self._log(f"   📝 РЕКОМЕНДАЦИЯ ПО ИСПРАВЛЕНИЮ:", "ERROR")
        self._log(f"   {recommendation}", "ERROR")
        self._log("=" * 60, "ERROR")
        
        # Сохраняем в файл для чтения ассистентом
        self._save_error_to_file(error, user_message, ai_response)
        
        # Пробуем отправить в web_chat_viewer
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            from web_server import web_chat_viewer
            
            details = f"""
Тип ошибки: {error_type}
Серьезность: {severity}
Сообщение пользователя: {user_message[:100]}
Ответ AI: {ai_response[:200]}

Рекомендация по исправлению:
{recommendation}
"""
            
            web_chat_viewer.add_agent_notification(
                title=f"⚠️ Ошибка в работе AI-психолога: {error_msg}",
                message=f"Тип: {error_type} | Серьезность: {severity}",
                notification_type="error",
                details=details.strip()
            )
            self._log("✅ Уведомление отправлено в web_chat_viewer", "INFO")
        except Exception as e:
            self._log(f"⚠️ web_chat_viewer недоступен: {e}", "WARNING")
    
    def generate_report(self) -> Dict:
        """Сгенерировать отчет о тестировании"""
        # Уникальные ошибки с деталями
        unique_errors = []
        seen_types = set()
        for error in self.errors_found:
            if isinstance(error, dict):
                error_type = error.get("type", "unknown")
                if error_type not in seen_types:
                    unique_errors.append(error)
                    seen_types.add(error_type)
            else:
                if str(error) not in seen_types:
                    unique_errors.append({"message": str(error), "type": "unknown"})
                    seen_types.add(str(error))
        
        report = {
            "total_tests": len(self.conversation_log),
            "total_errors": len(self.errors_found),
            "unique_errors": len(unique_errors),
            "errors": unique_errors,
            "conversation_log": self.conversation_log[-50:],  # Последние 50 записей
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self._log(f"📊 Отчет сгенерирован: {report['total_errors']} ошибок ({report['unique_errors']} уникальных) из {report['total_tests']} тестов")
        
        # Отправляем итоговый отчет
        self._send_final_report(report)
        
        return report
    
    def _save_error_to_file(self, error: Dict, user_message: str, ai_response: str):
        """Сохранить ошибку в файл для чтения ассистентом"""
        try:
            errors_file = "/tmp/psychologist_agent_errors.txt"
            error_type = error.get("type", "unknown")
            error_msg = error.get("message", "Неизвестная ошибка")
            severity = error.get("severity", "medium")
            recommendation = error.get("recommendation", "")
            
            with open(errors_file, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"🔴 ОШИБКА: {error_msg}\n")
                f.write(f"Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Тип: {error_type} | Серьезность: {severity}\n")
                f.write(f"Сообщение пользователя: {user_message}\n")
                f.write(f"Ответ AI: {ai_response[:300]}\n")
                f.write(f"\n📝 РЕКОМЕНДАЦИЯ ПО ИСПРАВЛЕНИЮ:\n{recommendation}\n")
                f.write("=" * 80 + "\n")
        except Exception as e:
            pass  # Не критично, если не удалось сохранить
    
    def _send_final_report(self, report: Dict):
        """Отправить итоговый отчет"""
        errors_summary = "\n".join([
            f"  • {err.get('message', str(err))} ({err.get('severity', 'unknown')})"
            for err in report.get("errors", [])[:10]
        ])
        
        # Всегда выводим в консоль
        self._log("", "INFO")
        self._log("=" * 60, "INFO")
        self._log("📊 ИТОГОВЫЙ ОТЧЕТ С РЕКОМЕНДАЦИЯМИ", "INFO")
        self._log("=" * 60, "INFO")
        self._log(f"Всего тестов: {report['total_tests']}", "INFO")
        self._log(f"Найдено ошибок: {report['total_errors']}", "INFO")
        self._log(f"Уникальных ошибок: {report['unique_errors']}", "INFO")
        self._log("", "INFO")
        
        if report.get("errors"):
            self._log("🔴 НАЙДЕННЫЕ ОШИБКИ И РЕКОМЕНДАЦИИ:", "ERROR")
            for i, err in enumerate(report.get("errors", [])[:10], 1):
                if isinstance(err, dict):
                    self._log(f"", "ERROR")
                    self._log(f"{i}. {err.get('message', 'Неизвестная ошибка')}", "ERROR")
                    self._log(f"   Тип: {err.get('type', 'unknown')} | Серьезность: {err.get('severity', 'unknown')}", "ERROR")
                    recommendation = err.get('recommendation', '')
                    if recommendation:
                        self._log(f"   📝 РЕКОМЕНДАЦИЯ: {recommendation}", "ERROR")
                else:
                    self._log(f"{i}. {err}", "ERROR")
        
        self._log("", "INFO")
        self._log("=" * 60, "INFO")
        
        # Сохраняем итоговый отчет в файл
        self._save_final_report_to_file(report)
        
        # Пробуем отправить в web_chat_viewer
        try:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            from web_server import web_chat_viewer
            
            details = f"""
Итоги тестирования:
- Всего тестов: {report['total_tests']}
- Найдено ошибок: {report['total_errors']}
- Уникальных ошибок: {report['unique_errors']}

Найденные ошибки:
{errors_summary}

Рекомендации:
1. Проверить логику обработки сообщений в psychologist_ai.py
2. Убедиться, что GPT получает правильный контекст и инструкции
3. Проверить переходы между этапами диалога
"""
            
            web_chat_viewer.add_agent_notification(
                title=f"📊 Итоговый отчет тестирования: {report['total_errors']} ошибок",
                message=f"Найдено {report['unique_errors']} уникальных типов ошибок",
                notification_type="report",
                details=details.strip()
            )
            self._log("✅ Итоговый отчет отправлен в web_chat_viewer", "INFO")
        except Exception as e:
            self._log(f"⚠️ web_chat_viewer недоступен для итогового отчета: {e}", "WARNING")
    
    def _save_final_report_to_file(self, report: Dict):
        """Сохранить итоговый отчет в файл для чтения ассистентом"""
        try:
            report_file = "/tmp/psychologist_agent_report.txt"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ AI-ПСИХОЛОГА\n")
                f.write("=" * 80 + "\n")
                f.write(f"Время: {report.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))}\n")
                f.write(f"Всего тестов: {report['total_tests']}\n")
                f.write(f"Найдено ошибок: {report['total_errors']}\n")
                f.write(f"Уникальных ошибок: {report['unique_errors']}\n\n")
                
                if report.get("errors"):
                    f.write("🔴 НАЙДЕННЫЕ ОШИБКИ И РЕКОМЕНДАЦИИ:\n")
                    f.write("-" * 80 + "\n")
                    for i, err in enumerate(report.get("errors", []), 1):
                        if isinstance(err, dict):
                            f.write(f"\n{i}. {err.get('message', 'Неизвестная ошибка')}\n")
                            f.write(f"   Тип: {err.get('type', 'unknown')}\n")
                            f.write(f"   Серьезность: {err.get('severity', 'unknown')}\n")
                            recommendation = err.get('recommendation', '')
                            if recommendation:
                                f.write(f"   📝 РЕКОМЕНДАЦИЯ: {recommendation}\n")
                            f.write("-" * 80 + "\n")
                        else:
                            f.write(f"{i}. {err}\n")
                
                f.write("\n" + "=" * 80 + "\n")
        except Exception as e:
            pass  # Не критично
    
    def cleanup(self):
        """Закрыть браузер и очистить ресурсы"""
        if self.driver:
            try:
                if hasattr(self, '_cleaned_up') and self._cleaned_up:
                    return  # Уже закрыт
                self._cleaned_up = True
                self.driver.quit()
                self._log("✅ Браузер закрыт")
            except:
                pass


async def run_psychologist_tests(continuous_mode: bool = False):
    """Запустить тесты AI-психолога"""
    agent = PsychologistTestAgent(headless=False, continuous_mode=continuous_mode)  # Показываем браузер для отладки
    
    try:
        # Инициализация
        if not agent._setup_driver():
            return None
        
        # Вход/регистрация
        if not agent.login():
            agent._log("❌ Не удалось войти в систему", "ERROR")
            agent.cleanup()
            return None
        
        agent._log("✅ Вход успешен, перехожу к тестам...")
        time.sleep(2)  # Даем время странице загрузиться
        
        # Проверяем, что мы на главной странице
        current_url = agent.driver.current_url
        agent._log(f"🔍 Текущий URL: {current_url}")
        
        # Если мы не на главной странице, переходим
        if "index" not in current_url and "chat" not in current_url and not current_url.endswith("/"):
            agent._log("🔄 Перехожу на главную страницу...")
            agent.driver.get(f"{agent.base_url}/")
            time.sleep(3)
        
        # Создание новой сессии
        agent._log("➕ Создаю новую сессию...")
        session_created = agent.create_new_session()
        if session_created:
            agent._log("✅ Сессия готова")
        else:
            agent._log("⚠️ Проблема с созданием сессии, но продолжаю...", "WARNING")
        time.sleep(3)  # Даем время сессии создаться
        
        # Проверяем, что поле ввода доступно
        message_input = agent._find_element_by_multiple_selectors([
            (By.ID, "messageInput"),
            (By.CSS_SELECTOR, "textarea"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.CSS_SELECTOR, "input[placeholder*='сообщение']"),
        ])
        
        if not message_input:
            agent._log("⚠️ Поле ввода не найдено, но продолжаю тесты...", "WARNING")
        else:
            agent._log("✅ Поле ввода найдено, готов к тестам")
        
        # Тестовые сценарии для проверки различных аспектов работы
        # Расширенный диалог на 40+ шагов
        test_scenarios = [
            # Полный развернутый диалог для глубокого тестирования
            [
                "привет",
                "плохо",
                "Я чувствую тревогу и грусть",
                "На работе начальник постоянно критикует меня",
                "Он говорит, что я ничего не умею",
                "Потому что я делаю ошибки в работе",
                "Я боюсь потерять работу",
                "Мне кажется, что я неудачник",
                "Потому что я не справляюсь с задачами",
                "Начальник говорит, что я ленивый",
                "Я думаю, что я действительно ленивый",
                "Потому что я не могу заставить себя работать лучше",
                "Я чувствую вину за это",
                "Мне кажется, что я подвел свою семью",
                "Потому что я не могу обеспечить их",
                "Я думаю, что я не достоин любви",
                "Потому что я не справляюсь с работой",
                "Мне кажется, что все меня осуждают",
                "Потому что я вижу, как на меня смотрят",
                "Я чувствую стыд",
                "Потому что я не могу быть лучше",
                "Я думаю, что я обречен на неудачу",
                "Потому что у меня никогда ничего не получалось",
                "В детстве родители тоже меня критиковали",
                "Они говорили, что я ничего не добьюсь",
                "Я поверил в это",
                "Потому что они были авторитетом для меня",
                "Теперь я сам себя критикую",
                "Потому что я усвоил их слова",
                "Я не могу остановить этот голос в голове",
                "Он говорит мне, что я плохой",
                "Я чувствую усталость от этого",
                "Мне кажется, что я никогда не буду счастлив",
                "Потому что я не могу измениться",
                "Я думаю, что проблема во мне",
                "Потому что другие справляются, а я нет",
                "Мне кажется, что я не такой как все",
                "Потому что у меня не получается то, что у других получается легко",
                "Я чувствую себя одиноким",
                "Потому что никто не понимает, что я чувствую",
            ]
        ]
        
        agent._log(f"🧪 Начинаю выполнение {len(test_scenarios)} тестовых сценариев...")
        
        # Запускаем тесты
        for i, scenario in enumerate(test_scenarios, 1):
            agent._log(f"📋 Сценарий {i}/{len(test_scenarios)}")
            await agent.run_test_scenario(scenario)
            time.sleep(3)  # Пауза между сценариями
        
        # Генерируем отчет
        report = agent.generate_report()
        
        # Выводим отчет
        agent._log("=" * 50)
        agent._log("📊 ИТОГОВЫЙ ОТЧЕТ")
        agent._log("=" * 50)
        agent._log(f"Всего тестов: {report['total_tests']}")
        agent._log(f"Найдено ошибок: {report['total_errors']}")
        if report['errors']:
            agent._log("Список ошибок:")
            for error in report['errors']:
                if isinstance(error, dict):
                    error_msg = error.get('message', 'Неизвестная ошибка')
                    error_severity = error.get('severity', 'unknown')
                    error_recommendation = error.get('recommendation', '')
                    agent._log(f"  - [{error_severity}] {error_msg}")
                    if error_recommendation:
                        agent._log(f"    Рекомендация: {error_recommendation}")
                else:
                    agent._log(f"  - {error}")
        agent._log("=" * 50)
        
        return agent
        
    except Exception as e:
        agent._log(f"❌ Критическая ошибка: {e}", "ERROR")
        import traceback
        agent._log(traceback.format_exc(), "ERROR")
        return None
        
    finally:
        # Не закрываем браузер сразу, чтобы можно было посмотреть результат
        # Только если запущено интерактивно
        try:
            import sys
            if sys.stdin.isatty():
                input("\nНажмите Enter для закрытия браузера...")
        except:
            pass  # Если не интерактивный режим, просто продолжаем
        
        # Даем время посмотреть результат
        time.sleep(5)
        agent.cleanup()


if __name__ == "__main__":
    asyncio.run(run_psychologist_tests())

