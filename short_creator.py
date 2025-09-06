import sys
import os
import json
import time
import subprocess
import threading
import logging
import re
from functools import partial
from datetime import datetime
from urllib.parse import quote as url_quote

# #############################################################################
# # ЗАЛЕЖНОСТІ / DEPENDENCIES
# #############################################################################
# Перед запуском встановіть необхідні бібліотеки:
# pip install PySide6
# pip install requests
# pip install openai-whisper
# pip install openai
#
# Також переконайтесь, що у вашій системі встановлено FFmpeg і FFprobe,
# і вони доступні через системний PATH.
# #############################################################################

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
        QPushButton, QLineEdit, QLabel, QFileDialog, QListWidget, QListWidgetItem,
        QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QScrollArea,
        QTreeWidget, QTreeWidgetItem, QProgressBar,
        QFormLayout, QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox,
        QSplitter, QCheckBox, QDialog, QDialogButtonBox, QInputDialog, QStackedWidget
    )
    from PySide6.QtCore import (
        Qt, QObject, QRunnable, QThreadPool, Signal, Slot, QThread, QTimer, QUrl
    )
    from PySide6.QtGui import QColor, QPalette, QFont, QDesktopServices
    import requests
    import whisper
    from openai import OpenAI
    import pysubs2
except ImportError as e:
    print(f"Помилка імпорту. Будь ласка, встановіть необхідні бібліотеки: pip install PySide6 requests openai-whisper openai. Деталі: {e}")
    sys.exit(1)

# #############################################################################
# # СТАТИЧНІ ДАНІ
# #############################################################################

VOICEMAKER_VOICES = {
    'de-DE': [{'VoiceId': 'ai4-de-DE-Paul', 'Engine': 'neural'}, {'VoiceId': 'ai4-de-DE-Anja', 'Engine': 'neural'}, {'VoiceId': 'ai4-de-DE-Gabriele', 'Engine': 'neural'}, {'VoiceId': 'ai2-de-DE-Patrick', 'Engine': 'neural'}, {'VoiceId': 'ai2-de-DE-Pia', 'Engine': 'neural'}, {'VoiceId': 'ai2-de-DE-Mona', 'Engine': 'neural'}, {'VoiceId': 'ai2-de-DE-Dustin', 'Engine': 'neural'}, {'VoiceId': 'ai2-de-DE-Fabienne', 'Engine': 'neural'}, {'VoiceId': 'ai2-de-DE-Thomas', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Katja', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Conrad', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Johanna', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Kasper', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Schmidt', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Galliena', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Marlene', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Ermanno', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Rodriguez', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Rheinbeck', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Kerryl', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Marie', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Brunon', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Yettie', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-Maja', 'Engine': 'neural'}, {'VoiceId': 'ai3-de-DE-AmaliaV2', 'Engine': 'neural'}, {'VoiceId': 'ai1-de-DE-Fiona', 'Engine': 'neural'}, {'VoiceId': 'ai1-de-DE-Stefan', 'Engine': 'neural'}, {'VoiceId': 'ai5-de-DE-Mathilda', 'Engine': 'neural'}],
    'es-ES': [{'VoiceId': 'ai3-es-ES-Alvaro', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Elvira', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Lia', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Oscar', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Maura', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Juana', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Cruz', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Lorenzo', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Cristina', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Xiomara', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Domingo', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Silvio', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Carlos', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Viviana', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Ramiro', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-Blanca', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-ES-MarianaV2', 'Engine': 'neural'}, {'VoiceId': 'ai4-es-ES-Savannah', 'Engine': 'neural'}, {'VoiceId': 'ai4-es-ES-Matlab', 'Engine': 'neural'}, {'VoiceId': 'ai1-es-ES-Patricia', 'Engine': 'neural'}, {'VoiceId': 'ai1-es-ES-Casper', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-ES-Vega', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-ES-Luciana', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-ES-Ricardo', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-ES-Ruben2', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-ES-Azura2', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-ES-Reyna2', 'Engine': 'neural'}],
    'es-US': [{'VoiceId': 'ai4-es-US-Luz2', 'Engine': 'neural'}, {'VoiceId': 'ai1-es-US-Lupe', 'Engine': 'neural'}, {'VoiceId': 'ai1-es-US-Diego', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-US-Alberto', 'Engine': 'neural'}, {'VoiceId': 'ai3-es-US-Paz', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-US-Manolito', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-US-Savanna', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-US-Orlando', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-US-Savanna2', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-US-Orlando2', 'Engine': 'neural'}, {'VoiceId': 'ai2-es-US-Manolito2', 'Engine': 'neural'}],
    'fr-FR': [{'VoiceId': 'ai4-fr-FR-Blaise', 'Engine': 'neural'}, {'VoiceId': 'ai4-fr-FR-Charles', 'Engine': 'neural'}, {'VoiceId': 'ai2-fr-FR-Cassandra', 'Engine': 'neural'}, {'VoiceId': 'ai2-fr-FR-Amandine', 'Engine': 'neural'}, {'VoiceId': 'ai2-fr-FR-Erwan', 'Engine': 'neural'}, {'VoiceId': 'ai2-fr-FR-Valentine', 'Engine': 'neural'}, {'VoiceId': 'ai2-fr-FR-Dylan', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Henri', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Denise', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Nevil', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Claire', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Roel', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Tyssen', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Liana', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Austine', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Cannan', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Camille', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Tayler', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Manie', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Emmy', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-Victoire', 'Engine': 'neural'}, {'VoiceId': 'ai3-fr-FR-OdetteV2', 'Engine': 'neural'}, {'VoiceId': 'ai1-fr-FR-Jeanne', 'Engine': 'neural'}, {'VoiceId': 'ai1-fr-FR-Bernado', 'Engine': 'neural'}],
    'it-IT': [{'VoiceId': 'ai2-it-IT-Siliva', 'Engine': 'neural'}, {'VoiceId': 'ai2-it-IT-Dario', 'Engine': 'neural'}, {'VoiceId': 'ai2-it-IT-Federica', 'Engine': 'neural'}, {'VoiceId': 'ai2-it-IT-Alessandro', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Diego', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Isabella', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Elsa', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Fabiola', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Valeria', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Regina', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Ludovica', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Aitana', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Matteo', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Natalia', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Tito', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Gerardo', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Ennio', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Massimo', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-Francesco', 'Engine': 'neural'}, {'VoiceId': 'ai3-it-IT-CaterinaV2', 'Engine': 'neural'}, {'VoiceId': 'ai4-it-IT-Sara', 'Engine': 'neural'}, {'VoiceId': 'ai1-it-IT-Viola', 'Engine': 'neural'}, {'VoiceId': 'ai1-it-IT-Tommaso', 'Engine': 'neural'}],
    'pl-PL': [{'VoiceId': 'ai2-pl-PL-Hanna', 'Engine': 'neural'}, {'VoiceId': 'ai2-pl-PL-Julia', 'Engine': 'neural'}, {'VoiceId': 'ai2-pl-PL-Wojciech', 'Engine': 'neural'}, {'VoiceId': 'ai2-pl-PL-Franciszek', 'Engine': 'neural'}, {'VoiceId': 'ai2-pl-PL-Alicja', 'Engine': 'neural'}, {'VoiceId': 'ai3-pl-PL-Lena', 'Engine': 'neural'}, {'VoiceId': 'ai3-pl-PL-Zofia', 'Engine': 'neural'}, {'VoiceId': 'ai3-pl-PL-Kacper', 'Engine': 'neural'}, {'VoiceId': 'ai1-pl-PL-Kalina', 'Engine': 'neural'}],
    'ro-RO': [{'VoiceId': 'ai3-ro-RO-Alina', 'Engine': 'neural'}, {'VoiceId': 'ai3-ro-RO-Alexandru', 'Engine': 'neural'}, {'VoiceId': 'ai2-ro-RO-Corina', 'Engine': 'neural'}],
    'ru-RU': [{'VoiceId': 'ai2-ru-RU-Samara', 'Engine': 'neural'}, {'VoiceId': 'ai2-ru-RU-Tianna', 'Engine': 'neural'}, {'VoiceId': 'ai2-ru-RU-Czar', 'Engine': 'neural'}, {'VoiceId': 'ai2-ru-RU-Igor', 'Engine': 'neural'}, {'VoiceId': 'ai2-ru-RU-Tassa', 'Engine': 'neural'}, {'VoiceId': 'ai3-ru-RU-Yelena', 'Engine': 'neural'}, {'VoiceId': 'ai3-ru-RU-Dariya', 'Engine': 'neural'}, {'VoiceId': 'ai3-ru-RU-Dmitry', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Yuri', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Vladimir', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Alisa', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Sofia', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Konstantin', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Dmitri', 'Engine': 'neural'}, {'VoiceId': 'ai5-ru-RU-Ekaterina', 'Engine': 'neural'}],
    'uk-UA': [{'VoiceId': 'ai3-uk-UA-Olena', 'Engine': 'neural'}, {'VoiceId': 'ai3-uk-UA-Pavlo', 'Engine': 'neural'}, {'VoiceId': 'ai2-uk-UA-Aleksandra', 'Engine': 'neural'}],
}

# #############################################################################
# # ДОПОМІЖНІ ФУНКЦІЇ
# #############################################################################

def parse_ass_styles(file_path):
    """
    Парсить файл .ass і повертає словник зі стилями.
    """
    styles = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_styles_section = False
        format_order = []
        for line in lines:
            line = line.strip()
            if line == '[V4+ Styles]':
                in_styles_section = True
                continue
            if line.startswith('[') and in_styles_section:
                break # Кінець секції стилів
            
            if in_styles_section and line.startswith('Format:'):
                format_order = [h.strip() for h in line.split(':')[1].split(',')]
                continue
            
            if in_styles_section and line.startswith('Style:') and format_order:
                parts = line.split(':')[1].split(',')
                style_data = {}
                for i, key in enumerate(format_order):
                    if i < len(parts):
                        style_data[key] = parts[i].strip()
                
                style_name = style_data.get("Name")
                if style_name:
                    styles[style_name] = style_data
    except Exception as e:
        logging.error(f"Failed to parse ASS file {file_path}: {e}")
        return {}
    return styles

# #############################################################################
# # НАЛАШТУВАННЯ ЛОГЕРА
# #############################################################################

class QtLogHandler(logging.Handler):
    def __init__(self, log_signal):
        super().__init__()
        self.log_signal = log_signal
        # Створюємо спеціальний, більш читабельний форматер для GUI
        gui_formatter = logging.Formatter('%(asctime)s: %(message)s', datefmt='%H:%M:%S')
        self.setFormatter(gui_formatter)

    def emit(self, record):
        # Ігноруємо повідомлення рівня DEBUG в GUI для чистоти
        if record.levelno == logging.DEBUG:
            return
        msg = self.format(record)
        self.log_signal.emit(msg)

def setup_file_logging(level=logging.INFO):
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = datetime.now().strftime("log_%Y-%m-%d_%H-%M-%S.txt")
    log_filepath = os.path.join(log_dir, log_filename)

    logger = logging.getLogger()
    # Завжди встановлюємо найнижчий рівень для root логера,
    # щоб хендлери могли самі фільтрувати потрібний рівень.
    logger.setLevel(logging.DEBUG)

    # Видаляємо всі попередні хендлери, щоб уникнути дублювання
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Створюємо ДЕТАЛЬНИЙ форматер для файлу
    file_formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - (%(threadName)s) - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Створюємо файловий хендлер
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    # Файловий хендлер буде записувати все, починаючи з рівня DEBUG
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized. Log file: {log_filepath}")

# #############################################################################
# # КЛАСИ ДЛЯ РОБОТИ З API
# #############################################################################

class ApiClient:
    """Базовий клас для клієнтів API."""
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {}

    def test_connection(self):
        return False, "Not Implemented"

    def get_balance(self):
        return "N/A"

class OpenRouterClient(ApiClient):
    def __init__(self, api_key, detailed_logging=False):
        super().__init__(api_key)
        self.base_url = "https://openrouter.ai/api/v1"
        self.detailed_logging = detailed_logging
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/v-a-s/shorts-creator",
            "X-Title": "Shorts Creator App"
        }
        
    def _log_api_call(self, request_payload, response_data, error=None):
        # Ця функція тепер буде логувати тільки якщо увімкнено детальний лог у налаштуваннях
        if not self.detailed_logging:
            return
        
        # Використовуємо стандартний логер рівня DEBUG
        log_message = "API Call to OpenRouter"
        
        try:
            req_str = json.dumps(request_payload, indent=2, ensure_ascii=False)
            log_message += f"\n--- REQUEST ---\n{req_str}"
        except Exception:
            log_message += "\n--- REQUEST ---\n<Could not serialize request>"

        if error:
            log_message += f"\n--- ERROR ---\n{error}"
        
        try:
            # Намагаємось розпарсити відповідь як JSON для красивого виводу
            res_str = json.dumps(response_data, indent=2, ensure_ascii=False)
            log_message += f"\n--- RESPONSE ---\n{res_str}"
        except (TypeError, ValueError):
            # Якщо не вийшло, виводимо як є
            log_message += f"\n--- RESPONSE (RAW) ---\n{response_data}"
            
        logging.debug(log_message)


    def generate_text(self, model, messages, temperature, max_tokens):
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        while True: # Безкінечний цикл для перепідключення
            try:
                response = requests.post(f"{self.base_url}/chat/completions", headers=self.headers, json=payload, timeout=180)
                response.raise_for_status()
                response_json = response.json()
                self._log_api_call(payload, response_json)
                return response_json['choices'][0]['message']['content'], None
            except requests.exceptions.RequestException as e:
                error_message = f"OpenRouter Error: {e}. Retrying in 15 seconds..."
                logging.error(error_message) # Логуємо помилку
                response_json_for_log = {}
                try:
                    if e.response:
                        response_json_for_log = e.response.json()
                        error_details = response_json_for_log
                        error_message += f" | Details: {error_details.get('error', {}).get('message', 'N/A')}"
                except (ValueError, AttributeError): pass
                self._log_api_call(payload, response_json_for_log, error=error_message)
                
                # Замість того, щоб повертати помилку, чекаємо і пробуємо знову
                time.sleep(15)

    def test_connection(self):
        if not self.api_key: return False, "API Key is missing."
        try:
            response = requests.get(f"{self.base_url}/key", headers={"Authorization": f"Bearer {self.api_key}"})
            if response.status_code == 200:
                return True, "Success"
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, str(e)

    def get_balance(self):
        if not self.api_key: return "N/A"
        try:
            response = requests.get(f"{self.base_url}/key", headers={"Authorization": f"Bearer {self.api_key}"})
            if response.status_code == 200:
                data = response.json().get('data', {})
                limit = data.get('limit')
                usage = data.get('usage')
                if limit is None:
                    return f"Usage: ${usage:,.4f}"
                else:
                    remaining = limit - usage
                    return f"${remaining:,.4f} left"
            return "Error"
        except requests.exceptions.RequestException:
            return "Error"

class RecraftClient(ApiClient):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(base_url='https://external.api.recraft.ai/v1', api_key=self.api_key)
            except Exception as e:
                logging.error(f"Failed to initialize Recraft client: {e}")

    def generate_images(self, prompts, style, model, size="1024x1024", negative_prompt=None):
        if not self.client: return [], ["Recraft client not initialized."]
        urls, errors = [], []
        for prompt in prompts:
            while True: # Безкінечний цикл для поточного промпту
                try:
                    extra_params = {}
                    if negative_prompt:
                        extra_params['negative_prompt'] = negative_prompt
                    
                    response = self.client.images.generate(
                        prompt=prompt, 
                        style=style, 
                        model=model, 
                        n=1, 
                        size=size,
                        extra_body=extra_params if extra_params else None
                    )
                    urls.append(response.data[0].url)
                    break # Виходимо з циклу while, якщо запит успішний
                except Exception as e:
                    # Логуємо помилку і чекаємо перед повторною спробою
                    error_message = f"Recraft Error for prompt '{prompt}': {e}. Retrying in 15 seconds..."
                    logging.error(error_message)
                    time.sleep(15)
        return urls, errors
        
    def test_connection(self):
        if not self.api_key: return False, "API Key is missing."
        try:
            response = requests.get(
                'https://external.api.recraft.ai/v1/users/me',
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if response.status_code == 200:
                 user_data = response.json()
                 return True, f"Success! User: {user_data.get('name')}, Credits: {user_data.get('credits')}"
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if e.response else str(e)
            return False, f"Error: {error_text}"
        except Exception as e:
            return False, str(e)

    def get_balance(self):
        if not self.api_key: return "N/A"
        try:
            response = requests.get(
                'https://external.api.recraft.ai/v1/users/me',
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            if response.status_code == 200:
                return str(response.json().get('credits', 'Error'))
            return "Error"
        except Exception:
            return "Error"

class PollinationsClient(ApiClient):
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.base_url = "https://image.pollinations.ai/prompt/"

    def generate_image(self, prompt, width=1024, height=1024, model='flux', seed=None, nologo=False):
        encoded_prompt = url_quote(prompt)
        url = f"{self.base_url}{encoded_prompt}"
        params = {"width": width, "height": height, "model": model}
        if seed: params["seed"] = seed
        if nologo: params["nologo"] = "true"
        if self.api_key: params["token"] = self.api_key

        while True: # Безкінечний цикл для перепідключення
            try:
                response = requests.get(url, params=params, timeout=300)
                response.raise_for_status()
                return response.content, None
            except requests.exceptions.RequestException as e:
                error_text = e.response.text if e.response else str(e)
                error_message = f"Pollinations Error: {error_text}. Retrying in 15 seconds..."
                logging.error(error_message) # Логуємо помилку
                time.sleep(15)

    def test_connection(self):
        try:
            response = requests.get("https://image.pollinations.ai/models", timeout=10)
            return response.status_code == 200, "Service is reachable"
        except requests.exceptions.RequestException as e:
            return False, str(e)

class ElevenLabsBotClient(ApiClient):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.base_url = "https://voiceapi.csv666.ru"
        self.post_headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        self.get_headers = {"X-API-Key": self.api_key}

    def create_task(self, text, template_uuid=None):
        payload = {"text": text}
        if template_uuid: payload["template_uuid"] = template_uuid
        while True:
            try:
                response = requests.post(f"{self.base_url}/tasks", headers=self.post_headers, json=payload)
                response.raise_for_status()
                return response.json(), None
            except requests.exceptions.RequestException as e:
                error_message = f"ElevenLabsBot Error (create_task): {e.response.text if e.response else e}. Retrying in 15 seconds..."
                logging.error(error_message)
                time.sleep(15)

    def get_task_status(self, task_id):
        while True:
            try:
                response = requests.get(f"{self.base_url}/tasks/{task_id}/status", headers=self.get_headers)
                response.raise_for_status()
                return response.json(), None
            except requests.exceptions.RequestException as e:
                error_message = f"ElevenLabsBot Error (get_task_status): {e.response.text if e.response else e}. Retrying in 15 seconds..."
                logging.error(error_message)
                time.sleep(15)

    def get_result(self, task_id):
        while True:
            try:
                response = requests.get(f"{self.base_url}/tasks/{task_id}/result", headers=self.get_headers, timeout=120)
                if response.status_code == 200: return response.content, None
                elif response.status_code == 202: return "pending", None
                else: response.raise_for_status()
            except requests.exceptions.RequestException as e:
                error_message = f"ElevenLabsBot Error (get_result): {e.response.text if e.response else e}. Retrying in 15 seconds..."
                logging.error(error_message)
                time.sleep(15)

    def test_connection(self):
        if not self.api_key: return False, "API Key is missing."
        try:
            response = requests.get(f"{self.base_url}/balance", headers=self.get_headers)
            if response.status_code == 200:
                return True, f"Success! Balance: {response.json().get('balance_text', 'N/A')}"
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, str(e)
            
    def get_balance(self):
        if not self.api_key: return "N/A"
        try:
            response = requests.get(f"{self.base_url}/balance", headers=self.get_headers)
            if response.status_code == 200:
                return response.json().get('balance_text', 'Error')
            return "Error"
        except requests.exceptions.RequestException:
            return "Error"
            
    def get_templates(self):
        if not self.api_key: return [], "API Key is missing."
        try:
            response = requests.get(f"{self.base_url}/templates", headers=self.get_headers)
            if response.status_code == 200:
                return response.json(), None
            return [], f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return [], str(e)

class VoicemakerClient(ApiClient):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.base_url = "https://developer.voicemaker.in/voice/api"
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def generate_audio(self, text, voice_id, lang_code='en-US', engine='neural'):
        payload = {"Engine": engine, "VoiceId": voice_id, "LanguageCode": lang_code, "Text": text, "OutputFormat": "mp3", "SampleRate": "48000"}
        while True:
            try:
                response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    audio_url = data.get("path")
                    # Вкладений цикл для завантаження аудіофайлу
                    while True:
                        try:
                            audio_response = requests.get(audio_url, timeout=120)
                            audio_response.raise_for_status()
                            return audio_response.content, None
                        except requests.exceptions.RequestException as e:
                            error_message = f"Voicemaker Error (downloading audio): {e.response.text if e.response else e}. Retrying in 15 seconds..."
                            logging.error(error_message)
                            time.sleep(15)
                else:
                    # Це помилка API, а не з'єднання. Але для надійності додамо повторну спробу.
                    error_message = f"Voicemaker API Error: {data.get('message', 'Unknown error')}. Retrying in 15 seconds..."
                    logging.error(error_message)
                    time.sleep(15)

            except requests.exceptions.RequestException as e:
                error_message = f"Voicemaker Error (API call): {e.response.text if e.response else e}. Retrying in 15 seconds..."
                logging.error(error_message)
                time.sleep(15)

    def test_connection(self):
        if not self.api_key: return False, "API Key is missing."
        try:
            list_url = "https://developer.voicemaker.in/voice/list"
            response = requests.post(list_url, headers=self.headers, json={"language": "en-US"})
            if response.status_code == 200 and response.json().get("success"):
                return True, "Success"
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, str(e)
            
    def get_balance(self):
        if not self.api_key: return "N/A"
        
        payload = {
            "Engine": "neural", "VoiceId": "ai3-Jony", "LanguageCode": "en-US",
            "Text": ".", "OutputFormat": "mp3"
        }
        response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            remaining_chars = data.get("remainChars")
            return f"{remaining_chars:,}" if remaining_chars is not None else "Error parsing"
        else:
            raise RuntimeError(f"API returned success=false: {data.get('message', 'Unknown API error')}")

# #############################################################################
# # РОБОЧІ ПОТОКИ / WORKER THREADS
# #############################################################################

class WorkerSignals(QObject):
    """Визначає сигнали, доступні для всіх воркерів."""
    finished = Signal(bool, object)
    templates_updated = Signal(list, str)
    balances_updated = Signal(dict)
    status_update = Signal(int, int, str)

class BaseWorker(QRunnable):
    """Базовий клас для всіх потоків, що виконують тривалі операції."""
    def __init__(self, settings=None, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.is_killed = threading.Event()
        self.settings = settings if settings is not None else {}

    @Slot()
    def run(self):
        """Цей метод має бути перевизначений у дочірніх класах."""
        raise NotImplementedError("Метод 'run' має бути реалізований у дочірньому класі.")

    def kill(self): self.is_killed.set()
    def check_killed(self):
        if self.is_killed.is_set(): raise InterruptedError("Worker was cancelled.")
        
    def log_api(self, service, request_details, response_details):
        if self.settings.get('detailed_logging', False):
            req_str = json.dumps(request_details, indent=2, ensure_ascii=False, default=str)
            
            if isinstance(response_details, bytes):
                res_str = f"Received {len(response_details)} bytes of binary data."
            else:
                try: res_str = json.dumps(response_details, indent=2, ensure_ascii=False, default=str)
                except (TypeError, RecursionError): res_str = str(response_details)
            
            logging.debug(f"[API Call - {service}]\n>>> REQUEST:\n{req_str}\n\n<<< RESPONSE:\n{res_str}\n" + "="*40)

class AudioAndTranscriptionMasterWorker(BaseWorker):
    """Керує послідовним виконанням генерації аудіо та транскрипції."""
    def __init__(self, parent_worker):
        super().__init__(settings=parent_worker.settings)
        self.parent = parent_worker

    @Slot()
    def run(self):
        success = False
        try:
            self.parent.generate_all_audio()
            self.check_killed()
            self.parent._run_sequential_transcription()
            success = True
        except InterruptedError:
            logging.warning("AudioAndTranscriptionMasterWorker was cancelled.")
        except Exception as e:
            logging.error(f"AudioAndTranscriptionMasterWorker failed: {e}", exc_info=True)
        finally:
            self.signals.finished.emit(success, None)
            
class ImageGenerationWorker(BaseWorker):
    """Генерує всі картинки для всіх сценаріїв."""
    def __init__(self, parent_worker):
        super().__init__(settings=parent_worker.settings)
        self.parent = parent_worker

    @Slot()
    def run(self):
        logging.info("--- Sub-step: Image Generation (running in parallel) ---")
        try:
            for task_row, lang_idx, lang_config, settings, path in self.parent.scenario_paths:
                self.check_killed()
                scenario_name = os.path.basename(path)
                
                prompts = []
                with open(os.path.join(path, 'image_prompts.txt'), 'r', encoding='utf-8') as f:
                    for line in f:
                        cleaned_line = re.sub(r'^\d+[\.\)]?\s*', '', line.strip()).strip()
                        if cleaned_line:
                            prompts.append(cleaned_line)
                
                image_dir = os.path.join(path, 'images'); os.makedirs(image_dir, exist_ok=True)

                # --- ОНОВЛЕНА ЛОГІКА ПЕРЕМИКАННЯ З ЛІЧИЛЬНИКОМ СПРОБ ---
                
                for i, prompt in enumerate(prompts):
                    self.check_killed()
                    is_prompt_generated = False
                    error_attempts = 0 # Лічильник спроб для поточного промпту
                    
                    while not is_prompt_generated:
                        service = self.parent.current_image_service
                        
                        try:
                            status_prompt = (prompt[:75] + '...') if len(prompt) > 75 else prompt
                            self.parent.status_update.emit(task_row, lang_idx, f"🖼️ {service} [{i+1}/{len(prompts)}]: {status_prompt} (Спроба {error_attempts + 1})")
                            logging.info(f"[{service}] Generating image {i+1}/{len(prompts)} (Attempt {error_attempts + 1}) for {scenario_name} with prompt: {prompt}")

                            if service == 'Recraft':
                                cfg = self.settings['api']['recraft']
                                client = RecraftClient(cfg['api_key'])
                                urls, errors = client.generate_images([prompt], style=cfg['style'], model=cfg['model'], size=cfg['size'], negative_prompt=cfg.get('negative_prompt'))
                                if errors: raise RuntimeError("\n".join(errors))
                                
                                self.parent.status_update.emit(task_row, lang_idx, f"🖼️ Recraft: завантажую картинку {i+1}/{len(prompts)}")
                                img_data = requests.get(urls[0]).content
                                with open(os.path.join(image_dir, f'img_{i+1}.png'), 'wb') as f: f.write(img_data)

                            elif service == 'Pollinations':
                                cfg = self.settings['api']['pollinations']
                                client = PollinationsClient(api_key=cfg.get('token'))
                                img_data, error = client.generate_image(prompt, width=cfg.get('width', 1024), height=cfg.get('height', 1024), model=cfg.get('model', 'flux'), nologo=cfg.get('nologo', False))
                                if error: raise RuntimeError(error)
                                
                                with open(os.path.join(image_dir, f'img_{i+1}.jpg'), 'wb') as f: f.write(img_data)
                            
                            is_prompt_generated = True
                            time.sleep(1)

                        except Exception as e:
                            logging.error(f"Image generation failed for prompt {i+1} using {service} (Attempt {error_attempts + 1}): {e}")
                            error_attempts += 1

                            if error_attempts < 10:
                                # Якщо спроби ще не вичерпано, просто чекаємо і пробуємо знову ЦЕЙ Ж СЕРВІС
                                self.parent.status_update.emit(task_row, lang_idx, f"🖼️ Помилка {service}, повторна спроба через 15с...")
                                time.sleep(15)
                            else:
                                # Якщо всі 3 спроби були невдалими, перемикаємо сервіс
                                if self.settings.get('auto_fallback_image_service', True):
                                    new_service = 'Pollinations' if service == 'Recraft' else 'Recraft'
                                    logging.warning(f"Failed after 3 attempts. Fallback enabled. Switching from {service} to {new_service}.")
                                    self.parent.status_update.emit(task_row, lang_idx, f"🖼️ Помилка! Перемикаюсь на {new_service}...")
                                    self.parent.current_image_service = new_service
                                    error_attempts = 0 # Скидаємо лічильник для нового сервісу
                                else:
                                    # Якщо перемикання вимкнено, продовжуємо нескінченні спроби
                                    self.parent.status_update.emit(task_row, lang_idx, f"🖼️ Помилка, повторна спроба через 15с...")
                                    time.sleep(15)

            self.signals.finished.emit(True, "images")
            
        except InterruptedError:
            logging.warning("ImageGenerationWorker was cancelled.")
            self.signals.finished.emit(False, "images")
        except Exception as e:
            logging.error(f"Critical error in ImageGenerationWorker: {e}", exc_info=True)
            self.signals.finished.emit(False, "images")

class TitleGenerationWorker(BaseWorker):
    """Генерує назву для кожного сценарію."""
    def __init__(self, parent_worker):
        super().__init__(settings=parent_worker.settings)
        self.parent = parent_worker

    @Slot()
    def run(self):
        logging.info("--- Sub-step: Title Generation (running in parallel) ---")
        try:
            client = OpenRouterClient(
                self.settings['api']['openrouter']['api_key'],
                detailed_logging=self.settings.get('detailed_logging', False)
            )
            model = self.settings['api']['openrouter']['models'][0]

            for task_row, lang_idx, lang_config, settings, path in self.parent.scenario_paths:
                self.check_killed()
                scenario_name = os.path.basename(path)
                
                with open(os.path.join(path, 'scenario.txt'), 'r', encoding='utf-8') as f:
                    scenario_text = f.read()

                title_prompt = lang_config.get('title_prompt')
                if not title_prompt:
                    logging.warning(f"Title prompt is not defined for language {lang_config['id']}. Skipping title generation for {scenario_name}.")
                    continue
                
                self.parent.status_update.emit(task_row, lang_idx, f"✍️ Генерую назву для {scenario_name}...")
                logging.info(f"Generating title for {scenario_name}...")
                
                messages = [{"role": "system", "content": title_prompt}, {"role": "user", "content": scenario_text}]
                title_text, error = client.generate_text(model['id'], messages, model['temperature'], model['max_tokens'])

                if error:
                    logging.error(f"Title generation failed for {scenario_name}: {error}")
                    self.parent.status_update.emit(task_row, lang_idx, f"✍️ Помилка генерації назви!")
                else:
                    with open(os.path.join(path, 'title.txt'), 'w', encoding='utf-8') as f:
                        f.write(title_text.strip())
                    logging.info(f"Title for {scenario_name} generated successfully.")
            
            self.signals.finished.emit(True, "titles")
        except InterruptedError:
            logging.warning("TitleGenerationWorker was cancelled.")
            self.signals.finished.emit(False, "titles")
        except Exception as e:
            logging.error(f"Title generation failed: {e}", exc_info=True)
            self.signals.finished.emit(False, "titles")

class MainTaskWorker(QObject):
    """Керує повним життєвим циклом одного великого завдання (від сценарію до фінального відео)."""
    finished = Signal(bool, object)
    status_update = Signal(int, int, str)

    def __init__(self, task_id, task_row, work_dir, lang_configs, settings):
        super().__init__()
        self.task_id = task_id
        self.task_row = task_row
        self.work_dir = work_dir
        self.lang_configs = lang_configs
        self.settings = settings
        self.is_killed = threading.Event()
        self.threadpool = QThreadPool.globalInstance()
        self.scenario_paths = []
        self.lock = threading.Lock()
        self.asset_phase_tasks_remaining = 0
        self.asset_phase_has_errors = False
        # --- НОВИЙ АТРИБУТ ДЛЯ ЗБЕРІГАННЯ ПОТОЧНОГО СЕРВІСУ ---
        self.current_image_service = self.settings['tasks'][self.task_row]['image_service']

    def kill(self):
        self.is_killed.set()
        self.threadpool.clear()

    def check_killed(self):
        if self.is_killed.is_set():
            raise InterruptedError("Task was cancelled.")

    @Slot()
    def run(self):
        try:
            logging.info(f"Starting Task #{self.task_id} in '{self.work_dir}'")
            # Етап 1: Генерація текстових сценаріїв і промптів
            self.generate_scenarios_and_prompts()
            self.check_killed()
            # Етап 2: Паралельна генерація картинок та аудіо з транскрипцією
            self.run_asset_generation_phase()
        except Exception as e:
            logging.error(f"Fatal error in task #{self.task_id}: {e}", exc_info=True)
            self.finished.emit(False, self.task_id)

    def generate_scenarios_and_prompts(self):
        logging.info("--- Step: Scenario & Prompt Generation ---")
        for lang_idx, lang_config in enumerate(self.lang_configs):
            self.check_killed()
            lang_id = lang_config['id']
            lang_name = lang_config['name']
            self.status_update.emit(self.task_row, lang_idx, f"📝 Сценарії для '{lang_name}'")
            logging.info(f"Generating scenarios for language: {lang_name} ({lang_id})")

            lang_dir = os.path.join(self.work_dir, lang_id)
            source_file = next((os.path.join(lang_dir, f) for f in ["rewritten_text.txt", "translation.txt"] if os.path.exists(os.path.join(lang_dir, f))), None)
            if not source_file: raise FileNotFoundError(f"Source text file not found for {lang_id}")
            
            with open(source_file, 'r', encoding='utf-8') as f: text = f.read()
            
            messages_scenario = [{"role": "system", "content": lang_config['scenario_prompt']}, {"role": "user", "content": text}]
            client = OpenRouterClient(
                self.settings['api']['openrouter']['api_key'],
                detailed_logging=self.settings.get('detailed_logging', False)
            )
            model = self.settings['api']['openrouter']['models'][0]
            scenarios_text, error = client.generate_text(model['id'], messages_scenario, model['temperature'], model['max_tokens'])
            if error: raise ConnectionError(f"Scenario generation failed: {error}")
            
            # Оновлена логіка для розрізання сценаріїв по нумерації
            scenarios_raw = re.split(r'\n(?=\d+[\.\)]\s*)', scenarios_text.strip())
            parsed_scenarios = []
            for s in scenarios_raw:
                if s.strip():
                    cleaned_scenario = re.sub(r'^\d+[\.\)]?\s*', '', s.strip()).strip()
                    if cleaned_scenario:
                        parsed_scenarios.append(cleaned_scenario)
            
            if not parsed_scenarios:
                raise ValueError(f"Could not parse any scenarios from LLM response for {lang_id}")
            logging.info(f"Generated {len(parsed_scenarios)} scenarios for {lang_name}.")

            shorts_dir = os.path.join(lang_dir, 'shorts')
            
            for i, scenario_text in enumerate(parsed_scenarios):
                self.check_killed()
                scenario_dir = os.path.join(shorts_dir, f'scenario_{i+1}')
                os.makedirs(scenario_dir, exist_ok=True)
                with open(os.path.join(scenario_dir, 'scenario.txt'), 'w', encoding='utf-8') as f: f.write(scenario_text)

                self.status_update.emit(self.task_row, lang_idx, f"🖼️ Промти для сценарію {i+1}")
                logging.info(f"Generating image prompts for scenario {i+1} ({lang_name})...")
                messages_prompt = [{"role": "system", "content": lang_config['image_prompt_prompt']}, {"role": "user", "content": scenario_text}]
                prompts_text, error = client.generate_text(model['id'], messages_prompt, model['temperature'], model['max_tokens'])
                if error: raise ConnectionError(f"Prompt generation failed: {error}")
                
                # Промпти зберігаються в файл в оригінальному вигляді з нумерацією
                with open(os.path.join(scenario_dir, 'image_prompts.txt'), 'w', encoding='utf-8') as f: f.write(prompts_text)

        self.scenario_paths = self.get_all_scenario_paths()

    def run_asset_generation_phase(self):
        """Запускає генерацію картинок, назв і (аудіо + транскрипція) паралельно."""
        logging.info("--- Step: Parallel Asset Generation ---")
        self.asset_phase_tasks_remaining = 3 # Змінено на 3
        self.asset_phase_has_errors = False
        
        image_worker = ImageGenerationWorker(self)
        image_worker.signals.finished.connect(self.on_asset_phase_finished)
        self.threadpool.start(image_worker)
        
        title_worker = TitleGenerationWorker(self) # Новий воркер
        title_worker.signals.finished.connect(self.on_asset_phase_finished)
        self.threadpool.start(title_worker)
        
        audio_transcribe_worker = AudioAndTranscriptionMasterWorker(self)
        audio_transcribe_worker.signals.finished.connect(self.on_asset_phase_finished)
        self.threadpool.start(audio_transcribe_worker)

    @Slot(bool, object)
    def on_asset_phase_finished(self, success, result):
        """Чекає, доки і картинки, і субтитри будуть готові."""
        with self.lock:
            if not success:
                self.asset_phase_has_errors = True
            self.asset_phase_tasks_remaining -= 1

            if self.asset_phase_tasks_remaining == 0:
                if self.asset_phase_has_errors:
                    logging.error("Asset generation (images or audio/subs) failed.")
                    self.finished.emit(False, self.task_id)
                else:
                    logging.info("--- Step Finished: All Assets (Images, Audio, Subtitles) are Ready ---")
                    QTimer.singleShot(0, self.run_video_assembly_pipeline)

    def generate_all_audio(self):
        """Генерує всі аудіофайли (метод з AudioMasterWorker)."""
        from collections import defaultdict
        scenarios_by_lang = defaultdict(list)
        for path_tuple in self.scenario_paths:
            lang_id = path_tuple[2]['id'] 
            scenarios_by_lang[lang_id].append(path_tuple)

        for lang_id, scenarios_for_this_lang in scenarios_by_lang.items():
            logging.info(f"--- Starting audio generation for language: {lang_id} ---")
            pool = self.threadpool
            completion_event = threading.Event()
            active_workers = len(scenarios_for_this_lang)
            lock = threading.Lock()
            has_errors = threading.Event()

            if active_workers == 0: continue

            def on_finished(success, result):
                nonlocal active_workers
                if not success: has_errors.set()
                with lock:
                    active_workers -= 1
                    if active_workers == 0: completion_event.set()

            for args in scenarios_for_this_lang:
                worker = AudioGenerationWorker(*args)
                worker.signals.status_update.connect(self.status_update)
                worker.signals.finished.connect(on_finished, Qt.DirectConnection)
                pool.start(worker)
            
            while not completion_event.wait(0.2): self.check_killed()
            
            if has_errors.is_set():
                raise RuntimeError(f"One or more audio generation tasks failed for language {lang_id}.")
            logging.info(f"--- Finished audio generation for language: {lang_id} ---")

    def _run_sequential_transcription(self):
        """Послідовно транскрибує всі готові аудіофайли."""
        logging.info("--- Sub-step: Sequential Transcription from AUDIO files ---")
        
        model = whisper.load_model("base")
        sub_settings = self.settings.get('ffmpeg', {}).get('subtitle', {})
        max_words = sub_settings.get('max_words_per_segment', 8)

        # Словник для перетворення вирівнювання з налаштувань у формат pysubs2
        alignment_map_pysubs2 = {
            '1': 1, '2': 2, '3': 3,       # Bottom
            '4': 5, '5': 6, '6': 7,       # Middle (pysubs2 uses different numbers)
            '7': 9, '8': 10, '9': 11      # Top
        }

        for task_row, lang_idx, lang_config, settings, path in self.scenario_paths:
            self.check_killed()
            scenario_name = os.path.basename(path)
            
            audio_path = os.path.join(path, 'audio.mp3')
            ass_path = os.path.join(path, 'subtitles.ass')

            if not os.path.exists(audio_path): 
                logging.warning(f"Audio file not found for {scenario_name}, skipping transcription.")
                continue

            # --- НОВИЙ РЯДОК ЛОГУВАННЯ ---
            self.status_update.emit(task_row, lang_idx, f"✒️ Транскрипція для {scenario_name}...")
            logging.info(f"Starting transcription for {scenario_name}...")
            
            try:
                result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
                
                subs = pysubs2.SSAFile()
                
                def _ass_to_pysubs2_color(ass_color):
                    try:
                        if not ass_color.startswith('&H'): return pysubs2.Color(255, 255, 255)
                        hex_color = ass_color.lstrip('&H').rstrip('&')
                        if len(hex_color) == 8:
                            aa, bb, gg, rr = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16)
                            return pysubs2.Color(r=rr, g=gg, b=bb, a=aa)
                        else:
                            bb, gg, rr = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                            return pysubs2.Color(r=rr, g=gg, b=bb)
                    except Exception: return pysubs2.Color(255, 255, 255)

                style = subs.styles["Default"].copy()
                style.fontname = sub_settings.get('fontname', 'Arial')
                style.fontsize = float(sub_settings.get('fontsize', 60))
                style.primarycolor = _ass_to_pysubs2_color(sub_settings.get('primary_color', '&H00FFFFFF'))
                style.secondarycolor = _ass_to_pysubs2_color(sub_settings.get('secondary_color', '&H000000FF'))
                style.outlinecolor = _ass_to_pysubs2_color(sub_settings.get('outline_color', '&H00000000'))
                style.backcolor = _ass_to_pysubs2_color(sub_settings.get('shadow_color', '&H96000000'))
                style.bold = sub_settings.get('bold', True)
                style.italic = sub_settings.get('italic', False)
                style.outline = float(sub_settings.get('outline', 3.0))
                style.shadow = float(sub_settings.get('shadow', 3.0))
                
                alignment_key = sub_settings.get('alignment', '2')
                style.alignment = alignment_map_pysubs2.get(alignment_key, 2)

                style.marginl = int(sub_settings.get('marginl', 20))
                style.marginr = int(sub_settings.get('marginr', 20))
                style.marginv = int(sub_settings.get('marginv', 60))
                
                subs.styles["Default"] = style

                all_words = [word for s in result['segments'] if 'words' in s for word in s['words']]

                animation = sub_settings.get('animation', 'None')
                anim_tag = ""
                if animation == "Fade": anim_tag = "{\\fad(250,250)}"
                elif animation == "Karaoke": anim_tag = "{\\fad(150,150)}"

                current_pos = 0
                while current_pos < len(all_words):
                    segment_words = all_words[current_pos : current_pos + max_words]
                    if not segment_words: break
                    start_time = segment_words[0]['start'] * 1000
                    end_time = segment_words[-1]['end'] * 1000
                    text = " ".join(word['word'] for word in segment_words).strip()
                    full_text = f"{anim_tag}{text}"
                    event = pysubs2.SSAEvent(start=start_time, end=end_time, text=full_text)
                    subs.events.append(event)
                    current_pos += max_words
                
                subs.save(ass_path)
            except Exception as e:
                logging.error(f"Failed to create subtitles for {scenario_name}: {e}", exc_info=True)
                raise e

    def run_video_assembly_pipeline(self):
        """Запускає монтаж тимчасових відео, а потім фіналізацію."""
        try:
            self.check_killed()
            self._run_parallel_stage(SilentMontageWorker, "--- Step: Creating silent videos ---")
            self.check_killed()
            self._run_parallel_stage(FinalizeVideoWorker, "--- Step: Finalizing videos ---")
            
            logging.info(f"Task #{self.task_id} finished successfully.")
            self.finished.emit(True, self.task_id)

        except Exception as e:
            logging.error(f"Video assembly pipeline failed for task #{self.task_id}: {e}", exc_info=True)
            self.finished.emit(False, self.task_id)

    def _run_parallel_stage(self, worker_class, log_message):
        """Допоміжний метод для запуску багатьох воркерів паралельно."""
        logging.info(log_message)
        max_threads = self.settings.get('ffmpeg', {}).get('max_concurrent', 3)
        pool = QThreadPool()
        pool.setMaxThreadCount(max_threads)
        completion_event = threading.Event()
        active_workers = len(self.scenario_paths)
        lock = threading.Lock()
        has_errors = threading.Event()

        if active_workers == 0:
            logging.warning(f"No scenarios to process for stage: {log_message}.")
            return

        def on_finished(success, result):
            nonlocal active_workers
            if not success: has_errors.set()
            with lock:
                active_workers -= 1
                if active_workers == 0: completion_event.set()

        for args in self.scenario_paths:
            worker = worker_class(*args)
            worker.signals.status_update.connect(self.status_update)
            worker.signals.finished.connect(on_finished, Qt.DirectConnection)
            pool.start(worker)
        
        while not completion_event.wait(0.1): self.check_killed()
        
        if has_errors.is_set():
            raise RuntimeError(f"One or more tasks failed during stage: {log_message}")

    def get_all_scenario_paths(self):
        paths = []
        for i, lc in enumerate(self.lang_configs):
            shorts_dir = os.path.join(self.work_dir, lc['id'], 'shorts')
            if os.path.exists(shorts_dir):
                for sc_folder in sorted(os.listdir(shorts_dir)):
                    if sc_folder.startswith('scenario_'):
                        paths.append((self.task_row, i, lc, self.settings, os.path.join(shorts_dir, sc_folder)))
        return paths

class AudioGenerationWorker(BaseWorker):
    """Відповідає за генерацію одного аудіофайлу для одного сценарію."""
    def __init__(self, task_row, lang_idx, lang_config, settings, scenario_path):
        super().__init__(settings=settings)
        self.task_row, self.lang_idx, self.lang_config, self.settings, self.scenario_path = task_row, lang_idx, lang_config, settings, scenario_path

    @Slot()
    def run(self):
        success = False
        scenario_name = os.path.basename(self.scenario_path)
        try:
            with open(os.path.join(self.scenario_path, 'scenario.txt'), 'r', encoding='utf-8') as f:
                text = f.read()
            audio_path = os.path.join(self.scenario_path, 'audio.mp3')
            service = self.lang_config['voice_service']
            audio_data = None
            
            logging.info(f"Starting audio generation for {scenario_name} using {service}")
            
            if service == 'ElevenLabsBot':
                client = ElevenLabsBotClient(self.settings['api']['elevenlabs']['api_key'])
                
                # --- Створення задачі ---
                self.check_killed()
                self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎤 ElevenLabs: створюю задачу для {scenario_name}")
                task_info, _ = client.create_task(text, self.lang_config['voice_template'])
                task_id = task_info['task_id']
                logging.info(f"ElevenLabs task created for {scenario_name}: ID {task_id}.")
                
                # --- Очікування обробки ---
                is_ready_for_download = False
                while not is_ready_for_download:
                    self.check_killed()
                    status_info, _ = client.get_task_status(task_id)
                    status = status_info.get('status', 'unknown')
                    status_label = status_info.get('status_label', status)
                    self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎤 ElevenLabs ({scenario_name}): {status_label}")
                    logging.info(f"ElevenLabs task {task_id} status: {status_label}")
                    
                    if status == 'error': raise ConnectionError(f"ElevenLabsBot task {task_id} failed: {status_info.get('detail', 'API error')}")
                    if status in ['ending', 'ending_processed']:
                        is_ready_for_download = True
                    else:
                        time.sleep(10) # Продовжуємо чекати, поки задача обробляється
                
                # --- Завантаження результату ---
                while audio_data is None:
                    self.check_killed()
                    self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎤 ElevenLabs: завантаження аудіо для {scenario_name}")
                    data, _ = client.get_result(task_id)
                    if data == "pending":
                        self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎤 ElevenLabs: результат ще не готовий...")
                        time.sleep(10)
                    else:
                        audio_data = data

            elif service == 'Voicemaker':
                client = VoicemakerClient(self.settings['api']['voicemaker']['api_key'])
                self.check_killed()
                self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎤 Voicemaker: генерую аудіо для {scenario_name}")
                audio_data, _ = client.generate_audio(text, self.lang_config['voice_template'])
            
            if audio_data:
                self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎤 Аудіо для {scenario_name} збережено!")
                with open(audio_path, 'wb') as f: f.write(audio_data)
                success = True
        except InterruptedError:
             logging.warning(f"AudioGenerationWorker for {scenario_name} was cancelled.")
        except Exception as e:
            logging.error(f"AudioGenerationWorker error for {scenario_name}: {e}", exc_info=True)
        finally:
            self.signals.finished.emit(success, None)

class SilentMontageWorker(BaseWorker):
    """Створює тимчасове 'німе' відео з картинок, переходів та аудіодоріжки."""
    def __init__(self, task_row, lang_idx, lang_config, settings, scenario_path):
        super().__init__(settings=settings)
        self.task_row, self.lang_idx, self.lang_config, self.settings, self.scenario_path = task_row, lang_idx, lang_config, settings, scenario_path

    @Slot()
    def run(self):
        success = False
        scenario_name = os.path.basename(self.scenario_path)
        try:
            self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎞️ Монтаж для {scenario_name}...")
            logging.info(f"Starting silent montage for {scenario_name}...")

            audio_path, img_dir = os.path.join(self.scenario_path, 'audio.mp3'), os.path.join(self.scenario_path, 'images')
            if not all(os.path.exists(p) for p in [audio_path, img_dir]): raise FileNotFoundError("Assets not ready.")
            images = sorted([os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            if not images: raise FileNotFoundError("No images found.")

            # --- Нова логіка для визначення назви файлу ---
            output_dir = os.path.dirname(self.scenario_path)
            title_path = os.path.join(self.scenario_path, 'title.txt')
            video_filename = f"video_{scenario_name.split('_')[-1]}.mp4" # Назва за замовчуванням
            if os.path.exists(title_path):
                try:
                    with open(title_path, 'r', encoding='utf-8') as f:
                        title = f.read().strip()
                    if title:
                        # Очищуємо назву від символів, неприпустимих у назвах файлів
                        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
                        video_filename = f"{sanitized_title}.mp4"
                except Exception as e:
                    logging.warning(f"Could not read title from {title_path}, using default name. Error: {e}")
            
            temp_video_path = os.path.join(output_dir, f"temp_{video_filename}")
            # --- Кінець нової логіки ---

            ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
            total_duration = float(subprocess.check_output(ffprobe_cmd).decode('utf-8').strip())
            
            cfg = self.settings['ffmpeg']
            transition_duration, num_transitions = cfg.get('transition_duration', 1.0), max(0, len(images) - 1)
            img_duration = (total_duration - num_transitions * transition_duration) / len(images) if len(images) > 0 else 0
            if img_duration <= 0: img_duration, transition_duration = total_duration / len(images) if len(images) > 0 else 0, 0

            cmd, f_complex = ['ffmpeg', '-y'], []
            for i, img in enumerate(images): cmd.extend(['-loop', '1', '-t', str(img_duration + (transition_duration if i < num_transitions else 0)), '-i', img])
            cmd.extend(['-i', audio_path])

            import random
            for i in range(len(images)):
                stream = f"[{i}:v]scale=2160:3840,setsar=1,format=yuv420p"
                if (cfg.get('zoom_effect', True) or cfg.get('pan_effect', True)) and img_duration > 0:
                    fr, total_frames = 30, int(img_duration * 30)
                    px, py = "0", "0"
                    if cfg.get('pan_effect', True):
                        m_type = cfg.get('pan_direction', 'random')
                        if m_type == "random": m_type = random.choice(["horizontal", "vertical", "infinity"])
                        amp = cfg.get('pan_amount', 0.05) * 100
                        m_period = 20.0 * fr
                        if m_type == "horizontal": px = f"sin(2*PI*on/{m_period})*{amp}"
                        elif m_type == "vertical": py = f"sin(2*PI*on/{m_period})*{amp}"
                        elif m_type == "infinity": px, py = f"sin(2*PI*on/{m_period})*{amp}", f"sin(4*PI*on/{m_period})*{amp/2}"
                    z_expr = "1.1"
                    if cfg.get('zoom_effect', True):
                        z_start, z_end = cfg.get('zoom_start', 1.0), cfg.get('zoom_end', 1.2)
                        if z_end < z_start: z_end = z_start
                        base_z, amp_z = (z_start + z_end) / 2.0, (z_end - z_start) / 2.0
                        z_expr = f"{base_z}+{amp_z}*cos(2*PI*on/{(10.0*fr)})"
                    x_final, y_final = f"(iw-iw/({z_expr}))/2+{px}", f"(ih-ih/({z_expr}))/2+{py}"
                    stream += f",zoompan=z='{z_expr}':d={total_frames}:s=1080x1920:x='{x_final}':y='{y_final}':fps={fr}"
                else: stream += f",scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
                f_complex.append(stream + f"[v{i}]")

            last_stream = "[v0]"
            if len(images) > 1:
                for i in range(num_transitions):
                    offset = (i + 1) * img_duration + i * transition_duration
                    f_complex.append(f"{last_stream}[v{i+1}]xfade=transition=fade:duration={transition_duration}:offset={offset}[vt{i}]")
                    last_stream = f"[vt{i}]"
            
            f_complex.append(f"{last_stream}format=yuv420p[outv]")
            cmd.extend(['-filter_complex', ";".join(f_complex), '-map', '[outv]', '-map', f'{len(images)}:a'])
            
            codec_key, codec_cfg = cfg.get('selected_codec', 'CPU (libx264)'), cfg.get('codecs', {})
            codec_config = codec_cfg.get(codec_key, {})
            cmd.extend(['-c:v', codec_config.get('codec', 'libx264')])
            if 'bitrate' in codec_config: cmd.extend(['-b:v', codec_config['bitrate']])
            elif 'preset' in codec_config and 'crf' in codec_config: cmd.extend(['-preset', codec_config['preset'], '-crf', str(codec_config['crf'])])
            cmd.extend(['-c:a', 'aac', '-b:a', '192k', '-shortest', temp_video_path])
            
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if proc.returncode != 0: raise RuntimeError(f"FFmpeg failed during montage:\n{proc.stderr}")
            success = True
        except Exception as e:
            logging.error(f"SilentMontageWorker error for {scenario_name}: {e}", exc_info=True)
        finally:
            self.signals.finished.emit(success, None)

class FinalizeVideoWorker(BaseWorker):
    """Впаює субтитри у тимчасове відео для отримання фінального результату."""
    def __init__(self, task_row, lang_idx, lang_config, settings, scenario_path):
        super().__init__(settings=settings)
        self.task_row, self.lang_idx, self.lang_config, self.settings, self.scenario_path = task_row, lang_idx, lang_config, settings, scenario_path

    @Slot()
    def run(self):
        success = False
        s_name = os.path.basename(self.scenario_path); out_dir = os.path.dirname(self.scenario_path)
        
        # --- Нова логіка для визначення назви файлу (ідентична до SilentMontageWorker) ---
        title_path = os.path.join(self.scenario_path, 'title.txt')
        v_filename = f"video_{s_name.split('_')[-1]}.mp4" # Назва за замовчуванням
        if os.path.exists(title_path):
            try:
                with open(title_path, 'r', encoding='utf-8') as f:
                    title = f.read().strip()
                if title:
                    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
                    v_filename = f"{sanitized_title}.mp4"
            except Exception as e:
                logging.warning(f"Could not read title from {title_path}, using default name. Error: {e}")

        final_path, temp_path, ass_path = os.path.join(out_dir, v_filename), os.path.join(out_dir, f"temp_{v_filename}"), os.path.join(self.scenario_path, 'subtitles.ass')
        # --- Кінець нової логіки ---
        
        try:
            self.signals.status_update.emit(self.task_row, self.lang_idx, f"🎬 Finalizing {s_name}")
            if not all(os.path.exists(p) for p in [temp_path, ass_path]): raise FileNotFoundError(f"Missing assets for {s_name}")

            safe_ass = ass_path.replace('\\', '/').replace(':', '\\:')
            font_dir = 'C:/Windows/Fonts'.replace(':', '\\:')
            vf_str = f"ass=filename='{safe_ass}':fontsdir='{font_dir}'"
            cmd = ['ffmpeg', '-y', '-i', temp_path, '-vf', vf_str]
            
            cfg = self.settings['ffmpeg']
            codec_key = cfg.get('selected_codec', 'CPU (libx264)'); codec_config = cfg.get('codecs', {}).get(codec_key, {})
            cmd.extend(['-c:v', codec_config.get('codec', 'libx264')])
            if 'bitrate' in codec_config: cmd.extend(['-b:v', codec_config['bitrate']])
            elif 'preset' in codec_config and 'crf' in codec_config: cmd.extend(['-preset', codec_config['preset'], '-crf', str(codec_config['crf'])])
            cmd.extend(['-c:a', 'copy', final_path])

            proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if proc.returncode != 0: raise RuntimeError(f"FFmpeg failed during finalization:\n{proc.stderr}")
            success = True
        except Exception as e:
            logging.error(f"FinalizeVideoWorker error for {s_name}: {e}", exc_info=True)
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except OSError as e: logging.error(f"Failed to remove temp file {temp_path}: {e}")
            self.signals.finished.emit(success, None)

class PreviewWorker(BaseWorker):
    """Створює відео для попереднього перегляду на основі налаштувань."""
    def __init__(self, command, output_path):
        super().__init__()
        self.command = command; self.output_path = output_path
    
    @Slot()
    def run(self):
        success = False
        try:
            logging.info(f"Executing FFmpeg preview command: {' '.join(self.command)}")
            proc = subprocess.run(self.command, capture_output=True, text=True, encoding='utf-8')
            if proc.returncode != 0: raise RuntimeError(f"FFmpeg preview failed:\n{proc.stderr}")
            success = True
        except Exception as e:
            logging.error(f"PreviewWorker error: {e}", exc_info=True)
        finally:
            self.signals.finished.emit(success, self.output_path)

class BalanceUpdateWorker(BaseWorker):
    """Оновлює баланси всіх підключених API."""
    def __init__(self, settings):
        super().__init__(settings=settings)
    
    @Slot()
    def run(self):
        balances = {}
        apis = self.settings.get('api', {})
        client_map = {'openrouter': OpenRouterClient, 'recraft': RecraftClient, 'elevenlabs': ElevenLabsBotClient, 'voicemaker': VoicemakerClient}
        for name, client_class in client_map.items():
            if apis.get(name, {}).get('api_key'):
                try: balances[name] = client_class(apis[name]['api_key']).get_balance()
                except Exception as e: logging.error(f"Failed to get {name} balance: {e}")
        self.signals.balances_updated.emit(balances)
        self.signals.finished.emit(True, None)

class TemplateUpdateWorker(BaseWorker):
    """Оновлює список шаблонів/голосів для сервісів озвучки."""
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key
        
    @Slot()
    def run(self):
        try:
            client = ElevenLabsBotClient(self.api_key)
            templates, error = client.get_templates()
            if error: raise RuntimeError(error)
            self.signals.templates_updated.emit(templates, "elevenlabs")
            self.signals.finished.emit(True, None)
        except Exception as e:
            logging.error(f"Failed to get templates: {e}", exc_info=True)
            self.signals.finished.emit(False, None)

# #############################################################################
# # ДІАЛОГИ ТА ІНШІ ВІДЖЕТИ
# #############################################################################

class NewLanguageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додати нову мову")
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.id_edit = QLineEdit()
        layout.addRow("Назва (напр. Українська):", self.name_edit)
        layout.addRow("Ідентифікатор (напр. UA):", self.id_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return self.name_edit.text(), self.id_edit.text()

# #############################################################################
# # ГОЛОВНЕ ВІКНО ТА ВКЛАДКИ
# #############################################################################

class MainWindow(QMainWindow):
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shorts Creator")
        self.setGeometry(100, 100, 1400, 900)
        self.settings_file = "settings.json"
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(20) # Збільшимо ліміт потоків для паралельної роботи
        self.worker_threads = {}
        self.is_queue_running = False
        self.current_queue_task_row = -1

        setup_file_logging()
        self.settings = self.load_settings() 
        self.init_ui()
        self.settings_tab.load_settings_to_ui()

        qt_handler = QtLogHandler(self.log_signal)
        qt_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S'))
        logging.getLogger().addHandler(qt_handler)

        self.toggle_detailed_logging(self.settings.get('detailed_logging', False))
        logging.info("Application started. UI is ready.")

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.task_tab = TaskCreationTab(self)
        self.settings_tab = SettingsTab(self)
        self.log_tab = LogTab()
        self.log_signal.connect(self.log_tab.log)
        
        self.tabs.addTab(self.task_tab, "Створення завдання")
        self.tabs.addTab(self.settings_tab, "Налаштування")
        self.tabs.addTab(self.log_tab, "Лог")

        self.task_tab.start_task_signal.connect(self.start_main_task)
        self.task_tab.stop_task_signal.connect(self.stop_main_task)
        self.task_tab.start_queue_signal.connect(self.start_queue)
        self.settings_tab.settings_saved.connect(self.save_settings)
        self.settings_tab.refresh_languages.connect(self.task_tab.populate_lang_list)
        
        self.log_tab.detailed_log_checkbox.stateChanged.connect(self.toggle_detailed_logging)
        self.log_tab.detailed_log_checkbox.setChecked(self.settings.get('detailed_logging', False))

    def start_queue(self):
        if self.is_queue_running:
            logging.warning("Queue is already running.")
            return
        
        if self.task_tab.task_tree.topLevelItemCount() == 0:
            logging.info("Queue is empty. Nothing to start.")
            return

        self.is_queue_running = True
        self.task_tab.start_queue_btn.setText("■ Зупинити чергу")
        self.task_tab.start_queue_btn.clicked.disconnect()
        self.task_tab.start_queue_btn.clicked.connect(self.stop_queue)
        
        logging.info("Starting task queue...")
        self.current_queue_task_row = 0
        self.start_main_task(self.current_queue_task_row)

    def stop_queue(self):
        if not self.is_queue_running:
            return
            
        self.is_queue_running = False
        # Зупиняємо завдання, тільки якщо його індекс є дійсним
        if self.current_queue_task_row != -1 and self.current_queue_task_row < self.task_tab.task_tree.topLevelItemCount():
            self.stop_main_task(self.current_queue_task_row)

        self.task_tab.start_queue_btn.setText("▶ Запустити всі завдання")
        self.task_tab.start_queue_btn.clicked.disconnect()
        self.task_tab.start_queue_btn.clicked.connect(self.start_queue)
        # Скидаємо лічильник, коли черга зупинена
        self.current_queue_task_row = -1
        logging.warning("Task queue stopped.")

    def toggle_detailed_logging(self, state):
        is_detailed = bool(state)
        self.settings['detailed_logging'] = is_detailed
        new_level = logging.DEBUG if is_detailed else logging.INFO
        logging.getLogger().setLevel(new_level)
        logging.info(f"Detailed logging {'enabled' if is_detailed else 'disabled'}.")
        
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f: 
                    return json.load(f)
            except json.JSONDecodeError:
                logging.error("settings.json is corrupted. Loading defaults.")
        
        return {
            "api": {
                "openrouter": {"api_key": "", "models": [{"id": "openai/gpt-3.5-turbo", "temperature": 0.7, "max_tokens": 1500}]},
                "recraft": {"api_key": "", "model": "recraftv3", "style": "digital_illustration", "size": "1024x1024", "negative_prompt": ""},
                "pollinations": {"token": "", "model": "flux", "width": 1024, "height": 1024, "nologo": False},
                "elevenlabs": {"api_key": ""}, "voicemaker": {"api_key": ""}
            },
            "languages": {},
            "ffmpeg": {
                "selected_codec": "NVIDIA (h264_nvenc)",
                "codecs": {
                    "NVIDIA (h264_nvenc)": { "codec": "h264_nvenc", "bitrate": "8000k" },
                    "AMD (h264_amf)": { "codec": "h264_amf", "bitrate": "8000k" },
                    "Apple (h264_videotoolbox)": { "codec": "h264_videotoolbox", "bitrate": "8000k" },
                    "CPU (libx264)": { "codec": "libx264", "preset": "medium", "crf": "23" }
                },
                "transition_duration": 1.0,
                "zoom_effect": True,
                "zoom_start": 1.0,
                "zoom_end": 1.2,
                "pan_effect": True,
                "pan_direction": "random",
                "pan_amount": 0.05,
                "subtitle": {
                    "fontname": "Arial",
                    "fontsize": 32,
                    "primary_color": "&H00FFFFFF",
                    "outline_color": "&H00000000",
                    "shadow_color": "&H80000000",
                    "outline": 2,
                    "shadow": 2,
                    "animation": "Fade",
                    "max_words_per_segment": 8,
                    "marginv": 40
                },
                "max_concurrent": 3
            },
            "tasks": [],
            "default_image_service": "Recraft",
            "clear_queue_on_exit": True,
            "detailed_logging": False,
            "auto_fallback_image_service": True
        }

    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
        logging.info("Settings saved.")

    def closeEvent(self, event):
        self.is_queue_running = False
        
        # Перевіряємо, чи треба очищувати чергу
        if self.settings.get('clear_queue_on_exit', False):
            self.settings['tasks'] = []
            logging.info("Queue cleared on exit as per settings.")

        self.settings_tab.save_all_settings()
        for thread, worker in self.worker_threads.values():
            if thread.isRunning():
                worker.kill()
                thread.quit()
                thread.wait(1000)
        self.threadpool.clear()
        self.threadpool.waitForDone()
        super().closeEvent(event)

    def cleanup_task_thread(self, task_id):
        if task_id in self.worker_threads:
            del self.worker_threads[task_id]
            logging.debug(f"Cleaned up thread and worker for task #{task_id}.")

    @Slot(int)
    def start_main_task(self, task_row):
        if task_row >= self.task_tab.task_tree.topLevelItemCount():
            logging.warning(f"Attempted to start task at invalid row {task_row}. Stopping queue.")
            self.stop_queue()
            return

        task_info = self.settings['tasks'][task_row]
        task_id = task_info['id']
        if task_id in self.worker_threads and self.worker_threads[task_id][0].isRunning():
            logging.warning(f"Task #{task_id} is already running.")
            return
            
        lang_ids = task_info['languages']
        lang_configs = [self.settings['languages'][lid] for lid in lang_ids if lid in self.settings['languages']]
        if not lang_configs:
            logging.error(f"No valid languages for task '{task_info['work_dir']}'. Aborted.")
            return
            
        thread = QThread()
        worker = MainTaskWorker(task_id, task_row, task_info['work_dir'], lang_configs, self.settings)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self.on_task_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.cleanup_task_thread(task_id))
        
        worker.status_update.connect(self.task_tab.update_task_status)
        
        self.worker_threads[task_id] = (thread, worker)
        thread.start()
        self.task_tab.set_task_running_state(task_row, True)

    @Slot(int)
    def stop_main_task(self, task_row):
        task_id = self.settings['tasks'][task_row]['id']
        if task_id in self.worker_threads:
            thread, worker = self.worker_threads[task_id]
            if thread.isRunning():
                logging.info(f"Stopping task #{task_id}...")
                worker.kill()
                thread.quit()
                thread.wait(2000)

    @Slot(bool, object)
    def on_task_finished(self, success, task_id):
        task_row = next((i for i, t in enumerate(self.settings['tasks']) if t['id'] == task_id), -1)
        if task_row != -1:
            logging.info(f"Task #{task_id} (row {task_row}) finished with success={success}!")
            self.task_tab.set_task_running_state(task_row, False)
            
            # Оновлюємо фінальний статус для всіх мов у завданні
            final_status = "Completed ✅" if success else "Failed ❌"
            num_langs = len(self.settings['tasks'][task_row]['languages'])
            for i in range(num_langs):
                self.task_tab.update_task_status(task_row, i, final_status)
        
        if self.is_queue_running and success:
            self.current_queue_task_row += 1
            if self.current_queue_task_row < self.task_tab.task_tree.topLevelItemCount():
                logging.info(f"Queue mode: Starting next task (row {self.current_queue_task_row}).")
                self.start_main_task(self.current_queue_task_row)
            else:
                logging.info("All tasks in the queue are completed.")
                self.stop_queue()
        elif self.is_queue_running and not success:
             logging.error(f"Task #{task_id} failed. Stopping queue.")
             self.stop_queue()


class TaskCreationTab(QWidget):
    start_task_signal = Signal(int)
    stop_task_signal = Signal(int)
    start_queue_signal = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = main_window.settings
        self.task_counter = max([t['id'] for t in self.settings.get('tasks', [])] or [0])
        self.init_ui()
        self.populate_tasks()
        self.refresh_balances()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        balance_group = QGroupBox("Баланси")
        balance_layout = QHBoxLayout(balance_group)
        self.openrouter_balance_label = QLabel("OpenRouter: N/A")
        self.recraft_balance_label = QLabel("Recraft: N/A")
        self.elevenlabs_balance_label = QLabel("ElevenLabsBot: N/A")
        self.voicemaker_balance_label = QLabel("Voicemaker: N/A")
        refresh_btn = QPushButton("Оновити баланси")
        refresh_btn.clicked.connect(self.refresh_balances)
        balance_layout.addWidget(self.openrouter_balance_label)
        balance_layout.addWidget(self.recraft_balance_label)
        balance_layout.addWidget(self.elevenlabs_balance_label)
        balance_layout.addWidget(self.voicemaker_balance_label)
        balance_layout.addStretch()
        balance_layout.addWidget(refresh_btn)
        layout.addWidget(balance_group)

        creation_group = QGroupBox("Створити нове завдання")
        creation_layout = QFormLayout(creation_group)
        self.work_dir_edit = QLineEdit()
        self.work_dir_btn = QPushButton("Вибрати папку...")
        self.work_dir_btn.clicked.connect(self.select_work_dir)
        dir_layout = QHBoxLayout(); dir_layout.addWidget(self.work_dir_edit); dir_layout.addWidget(self.work_dir_btn)
        creation_layout.addRow("Робоча папка:", dir_layout)
        self.lang_list_widget = QListWidget(); self.lang_list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.populate_lang_list()
        creation_layout.addRow("Мови для обробки:", self.lang_list_widget)
        self.image_service_combo = QComboBox(); self.image_service_combo.addItems(["Recraft", "Pollinations"])
        creation_layout.addRow("Сервіс генерації зображень:", self.image_service_combo)
        self.add_task_btn = QPushButton("Додати завдання в чергу")
        self.add_task_btn.clicked.connect(self.add_task)
        creation_layout.addWidget(self.add_task_btn)
        layout.addWidget(creation_group)

        queue_group = QGroupBox("Черга завдань")
        queue_layout = QVBoxLayout(queue_group)
        self.task_tree = QTreeWidget()
        self.task_tree.setColumnCount(3)
        self.task_tree.setHeaderLabels(["Завдання / Мова", "Статус", "Дії"])
        self.task_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.task_tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.task_tree.header().resizeSection(0, 400) 
        self.task_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.task_tree.setAlternatingRowColors(True)
        queue_layout.addWidget(self.task_tree)

        queue_controls_layout = QHBoxLayout()
        self.start_queue_btn = QPushButton("▶ Запустити всі завдання")
        self.start_queue_btn.clicked.connect(self.start_queue_signal.emit)
        clear_queue_btn = QPushButton("Очистити чергу")
        clear_queue_btn.clicked.connect(self.clear_queue)
        queue_controls_layout.addWidget(self.start_queue_btn)
        queue_controls_layout.addWidget(clear_queue_btn)
        queue_layout.addLayout(queue_controls_layout)
        
        layout.addWidget(queue_group)

    def clear_queue(self):
        if QMessageBox.question(self, "Очистити чергу", "Ви впевнені, що хочете видалити всі завдання з черги?") == QMessageBox.Yes:
            self.settings['tasks'] = []
            self.task_tree.clear()
            logging.info("Task queue cleared.")

    def refresh_balances(self):
        worker = BalanceUpdateWorker(self.settings)
        worker.signals.balances_updated.connect(self.update_balance_labels)
        self.main_window.threadpool.start(worker)

    @Slot(dict)
    def update_balance_labels(self, balances):
        self.openrouter_balance_label.setText(f"OpenRouter: {balances.get('openrouter', 'N/A')}")
        self.recraft_balance_label.setText(f"Recraft: {balances.get('recraft', 'N/A')}")
        self.elevenlabs_balance_label.setText(f"ElevenLabsBot: {balances.get('elevenlabs', 'N/A')}")
        self.voicemaker_balance_label.setText(f"Voicemaker: {balances.get('voicemaker', 'N/A')}")

    def select_work_dir(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Вибрати робочу папку")
        if dir_name: self.work_dir_edit.setText(dir_name)
    
    def populate_lang_list(self):
        self.lang_list_widget.clear()
        for lang_id, lang_data in self.settings.get('languages', {}).items():
            item = QListWidgetItem(f"{lang_data.get('name', lang_id)} ({lang_id})")
            item.setData(Qt.UserRole, lang_id)
            self.lang_list_widget.addItem(item)
            
    def add_task(self):
        work_dir, selected_items = self.work_dir_edit.text(), self.lang_list_widget.selectedItems()
        if not work_dir or not os.path.isdir(work_dir): QMessageBox.warning(self, "Помилка", "Будь ласка, виберіть коректну робочу папку."); return
        if not selected_items: QMessageBox.warning(self, "Помилка", "Будь ласка, виберіть хоча б одну мову."); return
        self.task_counter += 1
        new_task = {"id": self.task_counter, "work_dir": work_dir, "languages": [item.data(Qt.UserRole) for item in selected_items],
                    "image_service": self.image_service_combo.currentText(), "status": "Queued",
                    "lang_statuses": {item.data(Qt.UserRole): "Queued" for item in selected_items}}
        if 'tasks' not in self.settings: self.settings['tasks'] = []
        self.settings['tasks'].append(new_task)
        self.add_task_to_tree(new_task)
        self.work_dir_edit.clear(); self.lang_list_widget.clearSelection()

    def add_task_to_tree(self, task):
        task_item = QTreeWidgetItem(self.task_tree)
        task_item.setText(0, f"ID: {task['id']}  |  {os.path.basename(task['work_dir'])}")
        task_item.setData(0, Qt.UserRole, task['id'])
        task_item.setExpanded(True)
        font = task_item.font(0)
        font.setBold(True)
        task_item.setFont(0, font)

        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)
        start_btn, stop_btn, remove_btn = QPushButton("▶"), QPushButton("■"), QPushButton("❌")
        start_btn.setToolTip("Запустити це завдання"); stop_btn.setToolTip("Зупинити це завдання")
        remove_btn.setToolTip("Видалити це завдання з черги"); stop_btn.setEnabled(False)
        
        start_btn.clicked.connect(partial(self.on_start_button_clicked, task_item))
        stop_btn.clicked.connect(partial(self.on_stop_button_clicked, task_item))
        remove_btn.clicked.connect(partial(self.on_remove_button_clicked, task_item))
        
        actions_layout.addWidget(start_btn); actions_layout.addWidget(stop_btn); actions_layout.addWidget(remove_btn)
        self.task_tree.setItemWidget(task_item, 2, actions_widget)

        for lang_id in task['languages']:
            lang_item = QTreeWidgetItem(task_item)
            lang_name = self.settings['languages'].get(lang_id, {}).get('name', lang_id)
            lang_item.setText(0, f"    ↳ {lang_name} ({lang_id})")
            lang_item.setData(0, Qt.UserRole, lang_id)

            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget); status_layout.setContentsMargins(4, 2, 4, 2)
            progress_bar = QProgressBar(minimumHeight=18, textVisible=True, format="В черзі...")
            progress_bar.setRange(0, 100); progress_bar.setValue(0)
            status_layout.addWidget(progress_bar)
            self.task_tree.setItemWidget(lang_item, 1, status_widget)

    def on_start_button_clicked(self, item):
        task_id = item.data(0, Qt.UserRole)
        task_row = next((i for i, t in enumerate(self.settings['tasks']) if t['id'] == task_id), -1)
        if task_row != -1: self.start_task_signal.emit(task_row)

    def on_stop_button_clicked(self, item):
        task_id = item.data(0, Qt.UserRole)
        task_row = next((i for i, t in enumerate(self.settings['tasks']) if t['id'] == task_id), -1)
        if task_row != -1: self.stop_task_signal.emit(task_row)
            
    def on_remove_button_clicked(self, item):
        task_id = item.data(0, Qt.UserRole)
        if QMessageBox.question(self, "Видалити завдання", f"Ви впевнені, що хочете видалити завдання #{task_id}?") != QMessageBox.Yes: return
        
        self.settings['tasks'] = [t for t in self.settings['tasks'] if t['id'] != task_id]
        self.task_tree.invisibleRootItem().removeChild(item)
        logging.info(f"Task #{task_id} removed from queue.")
        
    def populate_tasks(self):
        self.task_tree.clear()
        for task in self.settings.get('tasks', []): self.add_task_to_tree(task)
            
    @Slot(int, int, str)
    def update_task_status(self, task_row, lang_index, status):
        if task_row >= self.task_tree.topLevelItemCount(): return

        task_item = self.task_tree.topLevelItem(task_row)
        if not task_item: return

        if lang_index < task_item.childCount():
            lang_item = task_item.child(lang_index)
            status_widget = self.task_tree.itemWidget(lang_item, 1)
            if status_widget:
                progress_bar = status_widget.findChild(QProgressBar)
                if progress_bar:
                    progress_value, s_lower = 0, status.lower()
                    
                    # Більш гнучке визначення прогресу за ключовими словами/емодзі
                    if "сценарії" in s_lower or "промти" in s_lower: progress_value = 15
                    elif "🖼️" in status or "зображення" in s_lower: progress_value = 30
                    elif "🎤" in status or "audio" in s_lower: progress_value = 50
                    elif "✒️" in status or "subtitles" in s_lower: progress_value = 65
                    elif "🎞️" in status or "montage" in s_lower: progress_value = 80
                    elif "🎬" in status or "finalizing" in s_lower: progress_value = 95
                    elif "✅" in status or "completed" in s_lower: progress_value = 100
                    elif "❌" in status or "failed" in s_lower: progress_value = 100
                    
                    # Якщо статус вже існує, оновлюємо лише текст, зберігаючи прогрес
                    current_progress = progress_bar.value()
                    if progress_value == 0 and current_progress > 0:
                        progress_value = current_progress

                    progress_bar.setValue(progress_value)
                    progress_bar.setFormat(status)
                    
                    style = ""
                    if "✅" in status or "completed" in s_lower:
                        style = "QProgressBar::chunk { background-color: #4CAF50; }"
                    elif "❌" in status or "failed" in s_lower:
                        style = "QProgressBar::chunk { background-color: #F44336; }"
                    
                    if style:
                        progress_bar.setStyleSheet(style)
    
    def set_task_running_state(self, row, is_running):
        if row >= len(self.settings['tasks']): return
        task_id_to_find = self.settings['tasks'][row]['id']

        root = self.task_tree.invisibleRootItem()
        for i in range(root.childCount()):
            task_item = root.child(i)
            if task_item.data(0, Qt.UserRole) == task_id_to_find:
                actions_widget = self.task_tree.itemWidget(task_item, 2)
                if actions_widget:
                    actions_widget.layout().itemAt(0).widget().setEnabled(not is_running)
                    actions_widget.layout().itemAt(1).widget().setEnabled(is_running)
                break

class SettingsTab(QWidget):
    settings_saved = Signal()
    refresh_languages = Signal()
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.settings = main_window.settings
        self.loaded_styles = {} # Сховище для завантажених стилів
        # Словник для перетворення числових значень вирівнювання в текст
        self.alignment_map = { 
            '1': "Bottom Left", '2': "Bottom Center", '3': "Bottom Right",
            '4': "Middle Left", '5': "Middle Center", '6': "Middle Right",
            '7': "Top Left",    '8': "Top Center",    '9': "Top Right"
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.tabs.addTab(self.create_api_tab(), "API")
        self.tabs.addTab(self.create_lang_tab(), "Налаштування мов")
        self.tabs.addTab(self.create_ffmpeg_tab(), "Налаштування монтажу")
        save_btn = QPushButton("Зберегти всі налаштування")
        save_btn.clicked.connect(self.save_all_settings)
        layout.addWidget(save_btn, alignment=Qt.AlignRight)

    # --- Метод create_api_tab залишається без змін ---
    def create_api_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        api_tabs = QTabWidget()
        
        or_tab = QWidget()
        or_layout = QFormLayout(or_tab)
        self.or_api_key = QLineEdit()
        or_key_layout = QHBoxLayout(); or_key_layout.addWidget(self.or_api_key)
        test_or_btn = QPushButton("Тест"); test_or_btn.clicked.connect(lambda: self.test_api('openrouter'))
        or_key_layout.addWidget(test_or_btn)
        or_layout.addRow("API Key:", or_key_layout)
        self.or_models_table = QTableWidget(0, 4)
        self.or_models_table.setHorizontalHeaderLabels(["Model ID", "Temperature", "Max Tokens", "Дії"])
        or_layout.addRow(self.or_models_table)
        add_model_btn = QPushButton("Додати модель"); add_model_btn.clicked.connect(self.add_or_model)
        or_layout.addRow(add_model_btn)
        
        img_tab = QWidget()
        img_layout = QFormLayout(img_tab)
        recraft_group = QGroupBox("Recraft")
        recraft_form = QFormLayout(recraft_group)
        self.recraft_api_key = QLineEdit()
        recraft_key_layout = QHBoxLayout(); recraft_key_layout.addWidget(self.recraft_api_key)
        test_recraft_btn = QPushButton("Тест"); test_recraft_btn.clicked.connect(lambda: self.test_api('recraft'))
        recraft_key_layout.addWidget(test_recraft_btn)
        recraft_form.addRow("API Key:", recraft_key_layout)
        self.recraft_negative_prompt = QLineEdit()
        recraft_form.addRow("Negative Prompt:", self.recraft_negative_prompt)
        self.recraft_model_combo = QComboBox(); self.recraft_model_combo.addItems(["recraftv3", "recraftv2"])
        recraft_form.addRow("Model:", self.recraft_model_combo)
        self.recraft_style_combo = QComboBox(); self.recraft_style_combo.addItems(["digital_illustration", "realistic_image", "vector_illustration", "icon"])
        recraft_form.addRow("Style:", self.recraft_style_combo)
        self.recraft_size_combo = QComboBox(); self.recraft_size_combo.addItems(["1024x1024", "1024x1536", "1536x1024"])
        recraft_form.addRow("Size:", self.recraft_size_combo)
        img_layout.addWidget(recraft_group)
        
        poll_group = QGroupBox("Pollinations")
        poll_form = QFormLayout(poll_group)
        self.pollinations_token = QLineEdit()
        poll_form.addRow("API Token (Optional):", self.pollinations_token)
        self.pollinations_model = QComboBox()
        self.pollinations_model.addItems(["flux", "flux-realism", "flux-3d", "flux-cablyai", "dall-e-3", "midjourney", "boreal"])
        poll_form.addRow("Model:", self.pollinations_model)
        self.pollinations_width = QSpinBox(); self.pollinations_width.setRange(256, 2048); self.pollinations_width.setSingleStep(64); self.pollinations_width.setValue(1024)
        self.pollinations_height = QSpinBox(); self.pollinations_height.setRange(256, 2048); self.pollinations_height.setSingleStep(64); self.pollinations_height.setValue(1024)
        size_layout = QHBoxLayout(); size_layout.addWidget(QLabel("Width:")); size_layout.addWidget(self.pollinations_width); size_layout.addWidget(QLabel("Height:")); size_layout.addWidget(self.pollinations_height)
        poll_form.addRow("Size:", size_layout)
        self.pollinations_nologo = QCheckBox("Видалити логотип (для преміум)")
        poll_form.addRow(self.pollinations_nologo)
        test_poll_btn = QPushButton("Тест з'єднання"); test_poll_btn.clicked.connect(lambda: self.test_api('pollinations'))
        poll_form.addRow(test_poll_btn)
        img_layout.addWidget(poll_group)
        
        voice_tab = QWidget()
        voice_layout = QFormLayout(voice_tab)
        eleven_group = QGroupBox("ElevenLabsBot")
        eleven_form = QFormLayout(eleven_group)
        self.elevenlabs_api_key = QLineEdit()
        eleven_key_layout = QHBoxLayout(); eleven_key_layout.addWidget(self.elevenlabs_api_key)
        test_eleven_btn = QPushButton("Тест"); test_eleven_btn.clicked.connect(lambda: self.test_api('elevenlabs'))
        eleven_key_layout.addWidget(test_eleven_btn)
        eleven_form.addRow("API Key:", eleven_key_layout)
        voice_layout.addWidget(eleven_group)
        
        vm_group = QGroupBox("Voicemaker")
        vm_form = QFormLayout(vm_group)
        self.voicemaker_api_key = QLineEdit()
        vm_key_layout = QHBoxLayout(); vm_key_layout.addWidget(self.voicemaker_api_key)
        test_vm_btn = QPushButton("Тест"); test_vm_btn.clicked.connect(lambda: self.test_api('voicemaker'))
        vm_key_layout.addWidget(test_vm_btn)
        vm_form.addRow("API Key:", vm_key_layout)
        voice_layout.addWidget(vm_group)

        api_tabs.addTab(or_tab, "OpenRouter"); api_tabs.addTab(img_tab, "Image"); api_tabs.addTab(voice_tab, "Voice")
        layout.addWidget(api_tabs)
        return widget

    # --- Метод create_lang_tab залишається без змін ---
    def create_lang_tab(self):
        widget = QWidget()
        splitter = QSplitter(Qt.Horizontal)
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel)
        self.lang_list = QListWidget(); self.lang_list.currentItemChanged.connect(self.display_lang_settings)
        left_layout.addWidget(self.lang_list)
        lang_btns_layout = QHBoxLayout()
        add_lang_btn = QPushButton("Додати"); add_lang_btn.clicked.connect(self.add_language)
        remove_lang_btn = QPushButton("Видалити"); remove_lang_btn.clicked.connect(self.remove_language)
        lang_btns_layout.addWidget(add_lang_btn); lang_btns_layout.addWidget(remove_lang_btn)
        left_layout.addLayout(lang_btns_layout)
        
        self.right_panel = QScrollArea(); self.right_panel.setWidgetResizable(True)
        self.lang_settings_widget = QWidget(); self.lang_settings_layout = QFormLayout(self.lang_settings_widget)
        self.lang_name_edit = QLineEdit()
        self.lang_id_edit = QLineEdit()
        self.lang_voice_code_edit = QLineEdit()
        self.scenario_prompt_edit = QTextEdit()
        self.image_prompt_edit = QTextEdit()
        self.title_prompt_edit = QTextEdit() # Нове поле для промпту назви
        self.voice_service_combo = QComboBox(); self.voice_service_combo.addItems(["ElevenLabsBot", "Voicemaker"])
        
        self.voice_template_widget = QWidget()
        self.voice_template_layout = QHBoxLayout(self.voice_template_widget)
        self.voice_template_layout.setContentsMargins(0,0,0,0)
        
        self.eleven_template_combo = QComboBox()
        self.eleven_refresh_btn = QPushButton("Оновити шаблони")
        self.eleven_refresh_btn.clicked.connect(self.refresh_voice_templates)
        self.voice_template_layout.addWidget(self.eleven_template_combo)
        self.voice_template_layout.addWidget(self.eleven_refresh_btn)

        self.vm_voice_combo = QComboBox()
        self.voice_template_layout.addWidget(self.vm_voice_combo)

        self.lang_settings_layout.addRow("Назва мови:", self.lang_name_edit)
        self.lang_settings_layout.addRow("Ідентифікатор (напр. UA):", self.lang_id_edit)
        self.lang_settings_layout.addRow("Код мови для голосу (напр. uk-UA):", self.lang_voice_code_edit)
        self.lang_settings_layout.addRow("Промт для сценаріїв:", self.scenario_prompt_edit)
        self.lang_settings_layout.addRow("Промт для зображень:", self.image_prompt_edit)
        self.lang_settings_layout.addRow("Промт для назви відео:", self.title_prompt_edit) # Новий рядок
        self.lang_settings_layout.addRow("Сервіс озвучки:", self.voice_service_combo)
        self.lang_settings_layout.addRow("Шаблон/Голос:", self.voice_template_widget)
        
        self.voice_service_combo.currentTextChanged.connect(self.toggle_voice_widgets)
        self.lang_voice_code_edit.textChanged.connect(self.populate_vm_voices)
        
        self.right_panel.setWidget(self.lang_settings_widget); self.lang_settings_widget.hide()
        splitter.addWidget(left_panel); splitter.addWidget(self.right_panel); splitter.setSizes([200, 500])
        main_layout = QHBoxLayout(widget); main_layout.addWidget(splitter)
        return widget

    # --- Метод create_ffmpeg_tab повністю оновлено ---
    def create_ffmpeg_tab(self):
        widget = QScrollArea(); widget.setWidgetResizable(True)
        content_widget = QWidget(); layout = QFormLayout(content_widget)

        # -- Стиль Субтитрів (тепер нагорі) --
        subs_group = QGroupBox("Стиль субтитрів")
        subs_layout = QFormLayout(subs_group)
        
        # --- НОВЕ: Блок керування шаблонами стилів ---
        style_preset_layout = QHBoxLayout()
        self.sub_style_preset_combo = QComboBox()
        self.sub_style_preset_combo.addItem("-- Ручне налаштування --")
        self.sub_style_preset_combo.currentTextChanged.connect(self.apply_style_preset)
        style_preset_layout.addWidget(self.sub_style_preset_combo)
        
        load_style_btn = QPushButton("Завантажити стилі з .ass")
        load_style_btn.clicked.connect(self.load_styles_from_ass_file)
        style_preset_layout.addWidget(load_style_btn)
        subs_layout.addRow("Шаблони стилів:", style_preset_layout)
        # --- Кінець нового блоку ---

        self.sub_fontname_combo = QComboBox()
        popular_fonts = ["Arial", "Arial Black", "Impact", "Roboto", "Verdana", "Georgia", "Courier New", "Tahoma", "Trebuchet MS", "Times New Roman", "Comic Sans MS"]
        self.sub_fontname_combo.addItems(popular_fonts)
        self.sub_fontsize = QSpinBox(); self.sub_fontsize.setRange(10, 200)
        
        font_layout = QHBoxLayout()
        font_layout.addWidget(self.sub_fontname_combo)
        font_layout.addWidget(QLabel("Розмір:"))
        font_layout.addWidget(self.sub_fontsize)
        subs_layout.addRow("Шрифт:", font_layout)

        self.sub_primary_color = QLineEdit()
        self.sub_secondary_color = QLineEdit() # НОВЕ
        self.sub_outline_color = QLineEdit()
        self.sub_shadow_color = QLineEdit()
        subs_layout.addRow("Основний колір:", self.sub_primary_color)
        subs_layout.addRow("Вторинний (для караоке):", self.sub_secondary_color)
        subs_layout.addRow("Колір обводки:", self.sub_outline_color)
        subs_layout.addRow("Колір тіні:", self.sub_shadow_color)
        
        effects_layout = QHBoxLayout()
        self.sub_bold = QCheckBox("Жирний") # НОВЕ
        self.sub_italic = QCheckBox("Курсив") # НОВЕ
        effects_layout.addWidget(self.sub_bold)
        effects_layout.addWidget(self.sub_italic)
        effects_layout.addStretch()
        subs_layout.addRow("Ефекти шрифту:", effects_layout)

        self.sub_outline = QDoubleSpinBox(); self.sub_outline.setRange(0, 20); self.sub_outline.setSingleStep(0.5)
        self.sub_shadow = QDoubleSpinBox(); self.sub_shadow.setRange(0, 20); self.sub_shadow.setSingleStep(0.5)
        border_layout = QHBoxLayout()
        border_layout.addWidget(QLabel("Обводка:"))
        border_layout.addWidget(self.sub_outline)
        border_layout.addWidget(QLabel("Тінь:"))
        border_layout.addWidget(self.sub_shadow)
        border_layout.addStretch()
        subs_layout.addRow("Межі:", border_layout)
        
        self.sub_alignment = QComboBox() # НОВЕ
        for key, value in self.alignment_map.items():
            self.sub_alignment.addItem(value, key)
        subs_layout.addRow("Вирівнювання:", self.sub_alignment)

        self.sub_marginl = QSpinBox(); self.sub_marginl.setRange(0, 500) # НОВЕ
        self.sub_marginr = QSpinBox(); self.sub_marginr.setRange(0, 500) # НОВЕ
        self.sub_marginv = QSpinBox(); self.sub_marginv.setRange(0, 500)
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Зліва:"))
        margin_layout.addWidget(self.sub_marginl)
        margin_layout.addWidget(QLabel("Справа:"))
        margin_layout.addWidget(self.sub_marginr)
        margin_layout.addWidget(QLabel("Знизу:"))
        margin_layout.addWidget(self.sub_marginv)
        subs_layout.addRow("Відступи (Margins):", margin_layout)

        self.sub_max_words = QSpinBox(); self.sub_max_words.setRange(1, 20)
        self.sub_animation = QComboBox(); self.sub_animation.addItems(["None", "Fade", "Karaoke"])
        subs_layout.addRow("Макс. слів у сегменті:", self.sub_max_words)
        subs_layout.addRow("Анімація появи:", self.sub_animation)
        layout.addWidget(subs_group)

        # -- Кодування --
        codec_group = QGroupBox("Налаштування кодування")
        codec_layout = QFormLayout(codec_group)
        self.codec_combo = QComboBox()
        codec_layout.addRow("Кодек:", self.codec_combo)
        self.codec_options_stack = QStackedWidget()
        codec_layout.addRow("Налаштування кодека:", self.codec_options_stack)
        self.codec_widgets = {}
        for name, codec in [("NVIDIA (h264_nvenc)", "h264_nvenc"), ("AMD (h264_amf)", "h264_amf"), ("Apple (h264_videotoolbox)", "h264_videotoolbox")]:
            gpu_widget = QWidget(); gpu_layout = QFormLayout(gpu_widget)
            bitrate_edit = QLineEdit(); gpu_layout.addRow("Bitrate (e.g., 8000k):", bitrate_edit)
            self.codec_options_stack.addWidget(gpu_widget)
            self.codec_combo.addItem(name)
            self.codec_widgets[name] = {"widget": gpu_widget, "bitrate": bitrate_edit}
        cpu_widget = QWidget(); cpu_layout = QFormLayout(cpu_widget)
        cpu_preset = QComboBox(); cpu_preset.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"])
        cpu_crf = QSpinBox(); cpu_crf.setRange(0, 51)
        cpu_layout.addRow("Preset:", cpu_preset); cpu_layout.addRow("CRF (0=lossless, 23=default):", cpu_crf)
        self.codec_options_stack.addWidget(cpu_widget)
        self.codec_combo.addItem("CPU (libx264)")
        self.codec_widgets["CPU (libx264)"] = {"widget": cpu_widget, "preset": cpu_preset, "crf": cpu_crf}
        self.codec_combo.currentIndexChanged.connect(self.codec_options_stack.setCurrentIndex)
        layout.addWidget(codec_group)

        # -- Ефекти руху --
        motion_group = QGroupBox("Ефекти руху")
        motion_layout = QFormLayout(motion_group)
        self.zoom_effect = QCheckBox("Ефект наближення (Zoom)"); motion_layout.addRow(self.zoom_effect)
        self.zoom_start = QDoubleSpinBox(); self.zoom_start.setRange(1.0, 5.0); self.zoom_start.setSingleStep(0.05); self.zoom_start.setDecimals(2)
        self.zoom_end = QDoubleSpinBox(); self.zoom_end.setRange(1.0, 5.0); self.zoom_end.setSingleStep(0.05); self.zoom_end.setDecimals(2)
        motion_layout.addRow("Початковий зум:", self.zoom_start); motion_layout.addRow("Кінцевий зум:", self.zoom_end)
        self.pan_effect = QCheckBox("Ефект руху камери (Pan)"); motion_layout.addRow(self.pan_effect)
        self.pan_direction = QComboBox(); self.pan_direction.addItems(["random", "horizontal", "vertical"])
        self.pan_amount = QDoubleSpinBox(); self.pan_amount.setRange(0.0, 0.5); self.pan_amount.setSingleStep(0.01); self.pan_amount.setDecimals(2)
        motion_layout.addRow("Напрямок руху:", self.pan_direction); motion_layout.addRow("Сила руху (0.0-0.5):", self.pan_amount)
        layout.addWidget(motion_group)
        
        # -- Загальні налаштування --
        general_group = QGroupBox("Загальні налаштування та Тестування")
        general_layout = QFormLayout(general_group)
        self.transition_duration = QDoubleSpinBox(); self.transition_duration.setRange(0.0, 5.0); self.transition_duration.setSingleStep(0.1)
        general_layout.addRow("Тривалість переходу (сек):", self.transition_duration)
        self.max_concurrent_ffmpeg = QSpinBox(); self.max_concurrent_ffmpeg.setRange(1, 10)
        general_layout.addRow("Макс. одночасних процесів монтажу:", self.max_concurrent_ffmpeg)
        self.clear_queue_checkbox = QCheckBox("Очищати чергу завдань при виході")
        general_layout.addRow(self.clear_queue_checkbox)
        
        # --- НОВИЙ ВІДЖЕТ ---
        self.auto_fallback_checkbox = QCheckBox("Автоматично перемикати сервіс зображень при помилці")
        general_layout.addRow(self.auto_fallback_checkbox)
        # --- КІНЕЦЬ НОВОГО ВІДЖЕТУ ---

        self.preview_btn = QPushButton("Створити попередній перегляд")
        self.preview_btn.setToolTip("Створює тестове відео з поточними налаштуваннями, використовуючи файли з папки /preview")
        self.preview_btn.clicked.connect(self.generate_preview)
        general_layout.addRow(self.preview_btn)
        layout.addWidget(general_group)
        
        widget.setWidget(content_widget)
        return widget

    def load_styles_from_ass_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Вибрати .ass файл зі стилями", "", "ASS Subtitles (*.ass)")
        if not file_path:
            return
        
        self.loaded_styles = parse_ass_styles(file_path)
        if not self.loaded_styles:
            QMessageBox.warning(self, "Помилка", "Не вдалося завантажити стилі з файлу. Перевірте формат файлу.")
            return

        self.sub_style_preset_combo.blockSignals(True)
        self.sub_style_preset_combo.clear()
        self.sub_style_preset_combo.addItem("-- Ручне налаштування --")
        self.sub_style_preset_combo.addItems(self.loaded_styles.keys())
        self.sub_style_preset_combo.blockSignals(False)
        QMessageBox.information(self, "Успіх", f"Завантажено {len(self.loaded_styles)} стилів.")

    def apply_style_preset(self, style_name):
        if style_name == "-- Ручне налаштування --" or not style_name in self.loaded_styles:
            return
        
        style = self.loaded_styles[style_name]
        
        # Застосовуємо значення до віджетів
        self.sub_fontname_combo.setCurrentText(style.get('Fontname', 'Arial'))
        self.sub_fontsize.setValue(int(style.get('Fontsize', 32)))
        self.sub_primary_color.setText(style.get('PrimaryColour', '&H00FFFFFF'))
        self.sub_secondary_color.setText(style.get('SecondaryColour', '&H000000FF'))
        self.sub_outline_color.setText(style.get('OutlineColour', '&H00000000'))
        self.sub_shadow_color.setText(style.get('BackColour', '&H80000000'))
        self.sub_bold.setChecked(style.get('Bold', '0') == '-1')
        self.sub_italic.setChecked(style.get('Italic', '0') == '-1')
        self.sub_outline.setValue(float(style.get('Outline', 2.0)))
        self.sub_shadow.setValue(float(style.get('Shadow', 2.0)))
        self.sub_marginl.setValue(int(style.get('MarginL', 10)))
        self.sub_marginr.setValue(int(style.get('MarginR', 10)))
        self.sub_marginv.setValue(int(style.get('MarginV', 40)))
        
        alignment_key = style.get('Alignment', '2')
        index = self.sub_alignment.findData(alignment_key)
        if index != -1:
            self.sub_alignment.setCurrentIndex(index)

    def load_settings_to_ui(self):
        api = self.settings.get('api', {})
        self.or_api_key.setText(api.get('openrouter', {}).get('api_key', ''))
        recraft_cfg = api.get('recraft', {})
        self.recraft_api_key.setText(recraft_cfg.get('api_key', ''))
        self.recraft_negative_prompt.setText(recraft_cfg.get('negative_prompt', ''))
        self.recraft_model_combo.setCurrentText(recraft_cfg.get('model', 'recraftv3'))
        self.recraft_style_combo.setCurrentText(recraft_cfg.get('style', 'digital_illustration'))
        self.recraft_size_combo.setCurrentText(recraft_cfg.get('size', '1024x1024'))
        poll_cfg = api.get('pollinations', {})
        self.pollinations_token.setText(poll_cfg.get('token', ''))
        self.pollinations_model.setCurrentText(poll_cfg.get('model', 'flux'))
        self.pollinations_width.setValue(poll_cfg.get('width', 1024))
        self.pollinations_height.setValue(poll_cfg.get('height', 1024))
        self.pollinations_nologo.setChecked(poll_cfg.get('nologo', False))
        self.elevenlabs_api_key.setText(api.get('elevenlabs', {}).get('api_key', ''))
        self.voicemaker_api_key.setText(api.get('voicemaker', {}).get('api_key', ''))
        self.or_models_table.setRowCount(0)
        for model in api.get('openrouter', {}).get('models', []): self.add_or_model(model['id'], model['temperature'], model['max_tokens'])
        self.lang_list.clear()
        for lang_id, lang_data in self.settings.get('languages', {}).items():
            item = QListWidgetItem(lang_data.get('name', lang_id)); item.setData(Qt.UserRole, lang_id); self.lang_list.addItem(item)
        
        ffmpeg = self.settings.get('ffmpeg', {})
        codecs_cfg = ffmpeg.get('codecs', {})
        for name in ["NVIDIA (h264_nvenc)", "AMD (h264_amf)", "Apple (h264_videotoolbox)"]:
            cfg = codecs_cfg.get(name, {})
            self.codec_widgets[name]["bitrate"].setText(cfg.get("bitrate", "8000k"))
        cpu_cfg = codecs_cfg.get("CPU (libx264)", {})
        self.codec_widgets["CPU (libx264)"]["preset"].setCurrentText(cpu_cfg.get("preset", "medium"))
        self.codec_widgets["CPU (libx264)"]["crf"].setValue(int(cpu_cfg.get("crf", 23)))
        self.codec_combo.setCurrentText(ffmpeg.get('selected_codec', 'NVIDIA (h264_nvenc)'))
        self.zoom_effect.setChecked(ffmpeg.get('zoom_effect', True))
        self.zoom_start.setValue(ffmpeg.get('zoom_start', 1.0))
        self.zoom_end.setValue(ffmpeg.get('zoom_end', 1.2))
        self.pan_effect.setChecked(ffmpeg.get('pan_effect', True))
        self.pan_direction.setCurrentText(ffmpeg.get('pan_direction', 'random'))
        self.pan_amount.setValue(ffmpeg.get('pan_amount', 0.05))

        # Оновлений блок завантаження налаштувань субтитрів
        sub_cfg = ffmpeg.get('subtitle', {})
        self.sub_fontname_combo.setCurrentText(sub_cfg.get('fontname', 'Arial'))
        self.sub_fontsize.setValue(sub_cfg.get('fontsize', 60))
        self.sub_primary_color.setText(sub_cfg.get('primary_color', '&H00FFFFFF'))
        self.sub_secondary_color.setText(sub_cfg.get('secondary_color', '&H000000FF'))
        self.sub_outline_color.setText(sub_cfg.get('outline_color', '&H00000000'))
        self.sub_shadow_color.setText(sub_cfg.get('shadow_color', '&H96000000'))
        self.sub_bold.setChecked(sub_cfg.get('bold', True))
        self.sub_italic.setChecked(sub_cfg.get('italic', False))
        self.sub_outline.setValue(sub_cfg.get('outline', 3.0))
        self.sub_shadow.setValue(sub_cfg.get('shadow', 3.0))
        
        alignment_key = sub_cfg.get('alignment', '2')
        index = self.sub_alignment.findData(alignment_key)
        if index != -1: self.sub_alignment.setCurrentIndex(index)
        
        self.sub_marginl.setValue(sub_cfg.get('marginl', 20))
        self.sub_marginr.setValue(sub_cfg.get('marginr', 20))
        self.sub_marginv.setValue(sub_cfg.get('marginv', 60))
        self.sub_max_words.setValue(sub_cfg.get('max_words_per_segment', 8))
        self.sub_animation.setCurrentText(sub_cfg.get('animation', 'Fade'))

        self.transition_duration.setValue(ffmpeg.get('transition_duration', 1.0))
        self.max_concurrent_ffmpeg.setValue(ffmpeg.get('max_concurrent', 3))
        self.main_window.task_tab.image_service_combo.setCurrentText(self.settings.get('default_image_service', 'Recraft'))
        self.clear_queue_checkbox.setChecked(self.settings.get('clear_queue_on_exit', True))
        self.auto_fallback_checkbox.setChecked(self.settings.get('auto_fallback_image_service', True))

    def save_all_settings(self):
        self.settings['api']['openrouter']['api_key'] = self.or_api_key.text()
        self.settings['api']['recraft'] = {'api_key': self.recraft_api_key.text(), 'model': self.recraft_model_combo.currentText(),'style': self.recraft_style_combo.currentText(), 'size': self.recraft_size_combo.currentText(),'negative_prompt': self.recraft_negative_prompt.text()}
        self.settings['api']['pollinations'] = {'token': self.pollinations_token.text(), 'model': self.pollinations_model.currentText(),'width': self.pollinations_width.value(), 'height': self.pollinations_height.value(),'nologo': self.pollinations_nologo.isChecked()}
        self.settings['api']['elevenlabs']['api_key'] = self.elevenlabs_api_key.text()
        self.settings['api']['voicemaker']['api_key'] = self.voicemaker_api_key.text()
        models = [{"id": self.or_models_table.item(r, 0).text(), "temperature": float(self.or_models_table.cellWidget(r, 1).value()), "max_tokens": int(self.or_models_table.cellWidget(r, 2).value())} for r in range(self.or_models_table.rowCount())]
        self.settings['api']['openrouter']['models'] = models
        if self.lang_list.currentItem(): self.save_current_lang_settings(self.lang_list.currentItem())
        if 'ffmpeg' not in self.settings: self.settings['ffmpeg'] = {}
        if 'codecs' not in self.settings['ffmpeg']: self.settings['ffmpeg']['codecs'] = {}
        self.settings['ffmpeg']['selected_codec'] = self.codec_combo.currentText()
        for name, data in self.codec_widgets.items():
            if 'bitrate' in data: self.settings['ffmpeg']['codecs'][name] = {"codec": name.split(' ')[1].strip('()'), "bitrate": data['bitrate'].text()}
            elif 'preset' in data: self.settings['ffmpeg']['codecs'][name] = {"codec": name.split(' ')[1].strip('()'), "preset": data['preset'].currentText(), "crf": str(data['crf'].value())}
        self.settings['ffmpeg']['zoom_effect'] = self.zoom_effect.isChecked()
        self.settings['ffmpeg']['zoom_start'] = self.zoom_start.value()
        self.settings['ffmpeg']['zoom_end'] = self.zoom_end.value()
        self.settings['ffmpeg']['pan_effect'] = self.pan_effect.isChecked()
        self.settings['ffmpeg']['pan_direction'] = self.pan_direction.currentText()
        self.settings['ffmpeg']['pan_amount'] = self.pan_amount.value()
        
        # Оновлений блок збереження налаштувань субтитрів
        self.settings['ffmpeg']['subtitle'] = {
            "fontname": self.sub_fontname_combo.currentText(),
            "fontsize": self.sub_fontsize.value(),
            "primary_color": self.sub_primary_color.text(),
            "secondary_color": self.sub_secondary_color.text(),
            "outline_color": self.sub_outline_color.text(),
            "shadow_color": self.sub_shadow_color.text(),
            "bold": self.sub_bold.isChecked(),
            "italic": self.sub_italic.isChecked(),
            "outline": self.sub_outline.value(),
            "shadow": self.sub_shadow.value(),
            "alignment": self.sub_alignment.currentData(),
            "marginl": self.sub_marginl.value(),
            "marginr": self.sub_marginr.value(),
            "marginv": self.sub_marginv.value(),
            "max_words_per_segment": self.sub_max_words.value(),
            "animation": self.sub_animation.currentText()
        }
        
        self.settings['ffmpeg']['transition_duration'] = self.transition_duration.value()
        self.settings['ffmpeg']['max_concurrent'] = self.max_concurrent_ffmpeg.value()
        self.settings['default_image_service'] = self.main_window.task_tab.image_service_combo.currentText()
        self.settings['clear_queue_on_exit'] = self.clear_queue_checkbox.isChecked()
        self.settings['detailed_logging'] = self.main_window.log_tab.detailed_log_checkbox.isChecked()
        self.settings['auto_fallback_image_service'] = self.auto_fallback_checkbox.isChecked()

        self.settings_saved.emit()
        QMessageBox.information(self, "Успіх", "Налаштування збережено.")
    
    # --- Решта методів класу залишається без змін ---
    def add_or_model(self, id="", temp=0.7, tokens=1500):
        row = self.or_models_table.rowCount(); self.or_models_table.insertRow(row)
        self.or_models_table.setItem(row, 0, QTableWidgetItem(id))
        temp_spin = QDoubleSpinBox(); temp_spin.setRange(0.0, 2.0); temp_spin.setSingleStep(0.1); temp_spin.setValue(temp); self.or_models_table.setCellWidget(row, 1, temp_spin)
        token_spin = QSpinBox(); token_spin.setRange(1, 32000); token_spin.setValue(tokens); self.or_models_table.setCellWidget(row, 2, token_spin)
        remove_btn = QPushButton("X"); remove_btn.clicked.connect(lambda: self.or_models_table.removeRow(self.or_models_table.indexAt(remove_btn.pos()).row())); self.or_models_table.setCellWidget(row, 3, remove_btn)
    def test_api(self, service_name):
        client_map = {'openrouter': (OpenRouterClient, self.or_api_key.text()), 'recraft': (RecraftClient, self.recraft_api_key.text()), 'pollinations': (PollinationsClient, None), 'elevenlabs': (ElevenLabsBotClient, self.elevenlabs_api_key.text()), 'voicemaker': (VoicemakerClient, self.voicemaker_api_key.text())}
        if service_name not in client_map: return
        client_class, api_key = client_map[service_name]
        client = client_class(api_key)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        success, message = client.test_connection()
        QApplication.restoreOverrideCursor()
        msg_box = QMessageBox.information if success else QMessageBox.warning
        msg_box(self, f"Тест {service_name}", message)
    def add_language(self):
        dialog = NewLanguageDialog(self)
        if dialog.exec():
            name, lang_id = dialog.get_data()
            if not name or not lang_id: QMessageBox.warning(self, "Помилка", "Назва та ідентифікатор не можуть бути порожніми."); return
            if lang_id in self.settings['languages']: QMessageBox.warning(self, "Помилка", "Мова з таким ідентифікатором вже існує."); return
            self.settings['languages'][lang_id] = {"id": lang_id, "name": name, "voice_code": "","scenario_prompt": "", "image_prompt_prompt": "", "title_prompt": "", "voice_service": "ElevenLabsBot", "voice_template": ""}
            item = QListWidgetItem(name); item.setData(Qt.UserRole, lang_id); self.lang_list.addItem(item)
            self.lang_list.setCurrentItem(item); self.refresh_languages.emit()
    def remove_language(self):
        item = self.lang_list.currentItem()
        if not item: return
        lang_id = item.data(Qt.UserRole)
        if QMessageBox.question(self, "Видалити мову", f"Ви впевнені, що хочете видалити '{lang_id}'?") == QMessageBox.Yes:
            del self.settings['languages'][lang_id]
            self.lang_list.takeItem(self.lang_list.row(item))
            self.lang_settings_widget.hide(); self.refresh_languages.emit()
    def display_lang_settings(self, current, previous):
        if previous: self.save_current_lang_settings(previous)
        if not current: self.lang_settings_widget.hide(); return
        lang_id = current.data(Qt.UserRole)
        data = self.settings['languages'][lang_id]
        self.lang_name_edit.setText(data.get('name', ''))
        self.lang_id_edit.setText(data.get('id', '')); self.lang_id_edit.setReadOnly(True)
        self.lang_voice_code_edit.setText(data.get('voice_code', ''))
        self.scenario_prompt_edit.setPlainText(data.get('scenario_prompt', ''))
        self.image_prompt_edit.setPlainText(data.get('image_prompt_prompt', ''))
        self.title_prompt_edit.setPlainText(data.get('title_prompt', '')) # Новий рядок
        self.voice_service_combo.setCurrentText(data.get('voice_service', 'ElevenLabsBot'))
        self.populate_vm_voices(data.get('voice_code', ''))
        self.toggle_voice_widgets(self.voice_service_combo.currentText())
        if self.voice_service_combo.currentText() == 'Voicemaker':
            current_voice_id = data.get('voice_template', '')
            index = self.vm_voice_combo.findData(current_voice_id)
            if index != -1: self.vm_voice_combo.setCurrentIndex(index)
        else:
            self.eleven_template_combo.clear()
            saved_template = data.get('voice_template', '')
            if saved_template: self.eleven_template_combo.addItem(f"Saved: {saved_template[:15]}...", saved_template)
        self.lang_settings_widget.show()
    def save_current_lang_settings(self, item):
        lang_id = item.data(Qt.UserRole)
        if lang_id in self.settings['languages']:
            service = self.voice_service_combo.currentText()
            voice_template = ""
            if service == 'ElevenLabsBot': voice_template = self.eleven_template_combo.currentData()
            elif service == 'Voicemaker': voice_template = self.vm_voice_combo.currentData()
            self.settings['languages'][lang_id] = {
                "id": self.lang_id_edit.text(), 
                "name": self.lang_name_edit.text(),
                "voice_code": self.lang_voice_code_edit.text(),
                "scenario_prompt": self.scenario_prompt_edit.toPlainText(),
                "image_prompt_prompt": self.image_prompt_edit.toPlainText(), 
                "title_prompt": self.title_prompt_edit.toPlainText(), # Новий рядок
                "voice_service": service, 
                "voice_template": voice_template
            }
            item.setText(f"{self.lang_name_edit.text()} ({lang_id})")
            self.refresh_languages.emit()
    def refresh_voice_templates(self):
        service = self.voice_service_combo.currentText()
        if service == 'ElevenLabsBot':
            api_key = self.settings.get('api', {}).get('elevenlabs', {}).get('api_key')
            if not api_key: QMessageBox.warning(self, "Помилка", "Введіть API ключ для ElevenLabsBot."); return
            worker = TemplateUpdateWorker(api_key)
            worker.signals.templates_updated.connect(self.update_template_combo)
            self.main_window.threadpool.start(worker)
    @Slot(list, str)
    def update_template_combo(self, templates, service):
        if service == 'elevenlabs':
            current_item = self.lang_list.currentItem()
            if not current_item: return
            current_uuid = self.settings['languages'].get(current_item.data(Qt.UserRole), {}).get('voice_template')
            self.eleven_template_combo.clear()
            idx_to_set = -1
            for i, t in enumerate(templates):
                self.eleven_template_combo.addItem(f"{t['name']}", t['uuid'])
                if t['uuid'] == current_uuid: idx_to_set = i
            if idx_to_set != -1: self.eleven_template_combo.setCurrentIndex(idx_to_set)
    def toggle_voice_widgets(self, service_name):
        is_eleven = (service_name == 'ElevenLabsBot')
        self.eleven_template_combo.setVisible(is_eleven)
        self.eleven_refresh_btn.setVisible(is_eleven)
        self.vm_voice_combo.setVisible(not is_eleven)
    def populate_vm_voices(self, voice_code):
        self.vm_voice_combo.clear()
        if voice_code in VOICEMAKER_VOICES:
            for voice in VOICEMAKER_VOICES[voice_code]: self.vm_voice_combo.addItem(voice['VoiceId'], voice['VoiceId'])
    def generate_preview(self):
        self.preview_btn.setEnabled(False); self.preview_btn.setText("Підготовка..."); QApplication.processEvents()
        preview_dir, audio_path, img_dir, ass_path, temp_video_path, output_path = "preview", "preview/audio.mp3", "preview/images", "preview/subtitles.ass", "preview/preview_temp.mp4", "preview/preview_video.mp4"
        
        def restore_button():
            self.preview_btn.setText("Створити попередній перегляд"); self.preview_btn.setEnabled(True)
            if os.path.exists(temp_video_path):
                try: os.remove(temp_video_path)
                except OSError: pass

        if not all(os.path.exists(p) for p in [audio_path, img_dir]):
            QMessageBox.warning(self, "Помилка", f"Не знайдено файли для попереднього перегляду."); restore_button(); return
        
        images = sorted([os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        if not images: QMessageBox.warning(self, "Помилка", f"В папці '{img_dir}' не знайдено зображень."); restore_button(); return
        
        try:
            self.preview_btn.setText("Етап 1: Створення відео..."); QApplication.processEvents()
            ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
            total_duration = float(subprocess.check_output(ffprobe_cmd).decode('utf-8').strip())
            transition_duration = self.transition_duration.value(); num_transitions = max(0, len(images) - 1)
            img_duration = (total_duration - num_transitions * transition_duration) / len(images) if len(images) > 0 else 0
            if img_duration <= 0: img_duration = total_duration / len(images) if len(images) > 0 else 0; transition_duration = 0
            
            cmd1, filter_complex = ['ffmpeg', '-y'], []
            for i, img_path in enumerate(images): cmd1.extend(['-loop', '1', '-t', str(img_duration + transition_duration if i < len(images) - 1 else img_duration), '-i', img_path])
            cmd1.extend(['-i', audio_path])
            
            import random
            for i in range(len(images)):
                stream = f"[{i}:v]scale=2160:3840,setsar=1,format=yuv420p"
                use_zoom, use_pan = self.zoom_effect.isChecked(), self.pan_effect.isChecked()
                if (use_zoom or use_pan) and img_duration > 0:
                    fr, total_frames = 30, int(img_duration * 30)
                    px, py = "0", "0"
                    if use_pan:
                        m_type, amp = self.pan_direction.currentText(), self.pan_amount.value() * 100
                        if m_type == "random": m_type = random.choice(["horizontal", "vertical", "infinity"])
                        m_period = 20.0 * fr
                        if m_type == "horizontal": px = f"sin(2*PI*on/{m_period})*{amp}"
                        elif m_type == "vertical": py = f"sin(2*PI*on/{m_period})*{amp}"
                        elif m_type == "infinity": px, py = f"sin(2*PI*on/{m_period})*{amp}", f"sin(4*PI*on/{m_period})*{amp/2}"
                    z_expr = "1.1"
                    if use_zoom:
                        z_start, z_end = self.zoom_start.value(), self.zoom_end.value()
                        if z_end < z_start: z_end = z_start
                        base_z, amp_z = (z_start + z_end) / 2.0, (z_end - z_start) / 2.0
                        z_expr = f"{base_z}+{amp_z}*cos(2*PI*on/{(10.0*fr)})"
                    x_final, y_final = f"(iw-iw/({z_expr}))/2+{px}", f"(ih-ih/({z_expr}))/2+{py}"
                    stream += f",zoompan=z='{z_expr}':d={total_frames}:s=1080x1920:x='{x_final}':y='{y_final}':fps={fr}"
                else: stream += ",scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
                filter_complex.append(stream + f"[v{i}]")

            last_stream = "[v0]"
            if len(images) > 1:
                for i in range(len(images) - 1):
                    offset = (i + 1) * img_duration + i * transition_duration
                    filter_complex.append(f"{last_stream}[v{i+1}]xfade=transition=fade:duration={transition_duration}:offset={offset}[vt{i}]")
                    last_stream = f"[vt{i}]"
            
            filter_complex.append(f"{last_stream}format=yuv420p[outv]")
            cmd1.extend(['-filter_complex', ";".join(filter_complex), '-map', '[outv]', '-map', f'{len(images)}:a'])
            selected_codec_key = self.codec_combo.currentText(); codec_widgets = self.codec_widgets.get(selected_codec_key, {})
            if 'bitrate' in codec_widgets: cmd1.extend(['-c:v', selected_codec_key.split(' ')[1].strip('()'), '-b:v', codec_widgets['bitrate'].text()])
            elif 'preset' in codec_widgets: cmd1.extend(['-c:v', selected_codec_key.split(' ')[1].strip('()'), '-preset', codec_widgets['preset'].currentText(), '-crf', str(codec_widgets['crf'].value())])
            cmd1.extend(['-c:a', 'aac', '-b:a', '192k', '-shortest', temp_video_path])
            
            process1 = subprocess.run(cmd1, capture_output=True, text=True, encoding='utf-8')
            if process1.returncode != 0: raise RuntimeError(f"FFmpeg Stage 1 failed:\n{process1.stderr}")

            self.preview_btn.setText("Етап 2: Транскрипція..."); QApplication.processEvents()
            model = whisper.load_model("base")
            result = model.transcribe(temp_video_path, verbose=False, word_timestamps=True)
            
            subs = pysubs2.SSAFile()
            style = subs.styles["Default"].copy()
            
            # Використовуємо значення прямо з віджетів UI
            style.fontname = self.sub_fontname_combo.currentText()
            style.fontsize = float(self.sub_fontsize.value())

            def _ass_to_pysubs2_color(ass_color):
                try:
                    if not ass_color.startswith('&H'): return pysubs2.Color(255, 255, 255)
                    hex_color = ass_color.lstrip('&H').rstrip('&')
                    if len(hex_color) == 8: aa, bb, gg, rr = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16), int(hex_color[6:8], 16); return pysubs2.Color(r=rr, g=gg, b=bb, a=aa)
                    else: bb, gg, rr = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16); return pysubs2.Color(r=rr, g=gg, b=bb)
                except Exception: return pysubs2.Color(255, 255, 255)
            
            style.primarycolor = _ass_to_pysubs2_color(self.sub_primary_color.text())
            style.secondarycolor = _ass_to_pysubs2_color(self.sub_secondary_color.text())
            style.outlinecolor = _ass_to_pysubs2_color(self.sub_outline_color.text())
            style.backcolor = _ass_to_pysubs2_color(self.sub_shadow_color.text())
            style.bold = self.sub_bold.isChecked()
            style.italic = self.sub_italic.isChecked()
            style.outline = self.sub_outline.value()
            style.shadow = self.sub_shadow.value()

            alignment_map_pysubs2 = {'1': 1, '2': 2, '3': 3, '4': 5, '5': 6, '6': 7, '7': 9, '8': 10, '9': 11}
            style.alignment = alignment_map_pysubs2.get(self.sub_alignment.currentData(), 2)

            style.marginl = self.sub_marginl.value()
            style.marginr = self.sub_marginr.value()
            style.marginv = self.sub_marginv.value()
            subs.styles["Default"] = style

            all_words = [word for s in result['segments'] if 'words' in s for word in s['words']]
            animation, max_words = self.sub_animation.currentText(), self.sub_max_words.value()
            anim_tag = ""
            if animation == "Fade": anim_tag = "{\\fad(250,250)}"
            elif animation == "Karaoke": anim_tag = "{\\fad(150,150)}"
            
            current_pos = 0
            while current_pos < len(all_words):
                segment_words = all_words[current_pos : current_pos + max_words]
                if not segment_words: break
                start_time, end_time = segment_words[0]['start'] * 1000, segment_words[-1]['end'] * 1000
                text = " ".join(word['word'] for word in segment_words).strip()
                event = pysubs2.SSAEvent(start=start_time, end=end_time, text=f"{anim_tag}{text}")
                subs.events.append(event)
                current_pos += max_words
            subs.save(ass_path)
            
            self.preview_btn.setText("Етап 3: Фіналізація..."); QApplication.processEvents()
            safe_ass_path = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
            font_dir = 'C:/Windows/Fonts'.replace(':', '\\:')
            vf_string = f"ass=filename='{safe_ass_path}':fontsdir='{font_dir}'"
            cmd2 = ['ffmpeg', '-y', '-i', temp_video_path, '-vf', vf_string]
            if 'bitrate' in codec_widgets: cmd2.extend(['-c:v', selected_codec_key.split(' ')[1].strip('()'), '-b:v', codec_widgets['bitrate'].text()])
            elif 'preset' in codec_widgets: cmd2.extend(['-c:v', selected_codec_key.split(' ')[1].strip('()'), '-preset', codec_widgets['preset'].currentText(), '-crf', str(codec_widgets['crf'].value())])
            cmd2.extend(['-c:a', 'copy', output_path])
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            worker = PreviewWorker(cmd2, output_path)
            worker.signals.finished.connect(self.on_preview_finished)
            worker.signals.finished.connect(lambda success, path: os.path.exists(temp_video_path) and os.remove(temp_video_path))
            self.main_window.threadpool.start(worker)

        except Exception as e:
            QMessageBox.critical(self, "Помилка створення прев'ю", f"Не вдалося згенерувати відео.\nДеталі: {e}"); logging.error(f"Preview generation failed: {e}", exc_info=True); restore_button()
    @Slot(bool, str)
    def on_preview_finished(self, success, output_path):
        QApplication.restoreOverrideCursor(); self.preview_btn.setText("Створити попередній перегляд"); self.preview_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "Успіх", f"Відео для попереднього перегляду успішно створено. Файл: {output_path}")
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(output_path)))
        else: QMessageBox.critical(self, "Помилка", "Не вдалося створити відео. Перевірте лог.")
class LogTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.detailed_log_checkbox = QCheckBox("Увімкнути детальний лог (записується у файл в папці /log)")
        layout.addWidget(self.detailed_log_checkbox)
        self.log_edit = QTextEdit(); self.log_edit.setReadOnly(True)
        palette = self.log_edit.palette(); palette.setColor(QPalette.Base, QColor(30, 30, 30)); palette.setColor(QPalette.Text, QColor(220, 220, 220))
        self.log_edit.setPalette(palette); self.log_edit.setFont(QFont("Courier", 10))
        layout.addWidget(self.log_edit)

    @Slot(str)
    def log(self, message):
        self.log_edit.append(message)
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

# #############################################################################
# # ЗАПУСК ПРОГРАМИ / APPLICATION START
# #############################################################################
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())