from flask import Flask, jsonify, request
from flask_cors import CORS
import json
from bin import models
# Загружаем конфигурацию
try:
    with open('config.json', 'r') as config_file:
        config = json.loads(config_file.read())
except FileNotFoundError:
    config = {"host": "0.0.0.0", "port": 5050}

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для React приложения

class AppState:
    def __init__(self):
        self.users = []  # Список пользователей с их размещением по столам
        self.metrics = dict()  # Метрики сессии
        self.settings = models.Settings(10, 5, 4, 2)  # По умолчанию: 10 столов, 5 мест, 4 раунда, 2 мин перерыв
        self.current_round = 0
        self.ready_users = set()
        self.session_started = False

# Глобальное состояние приложения
app_state = AppState()

@app.route('/api/users', methods=['POST'])
def update_users():
    """Обновление списка пользователей от бота"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            if data == []:
                app_state.users = []
                return jsonify({"message": f"Успешно"}), 200
            return jsonify({"error": "Неверный формат данных. Ожидается список пользователей"}), 400
        
        app_state.users = data
        print(f"Обновлены данные пользователей: {len(data)} записей")
        return jsonify({"message": f"Успешно обновлено {len(data)} пользователей", "count": len(data)}), 200
    
    except Exception as e:
        print(f"Ошибка при обновлении пользователей: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Получение списка пользователей для дашборда"""
    try:
        return jsonify(app_state.users), 200
    except Exception as e:
        print(f"Ошибка при получении списка пользователей: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route('/api/metrics', methods=['POST'])
def update_metrics():
    """Обновление метрик от бота"""
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Неверный формат данных. Ожидается объект"}), 400
        
        app_state.metrics = data
        print(f"Обновлены метрики: {len(data)} записей")
        return jsonify({"message": f"Успешно обновлено {len(data)} метрик", "count": len(data)}), 200
    
    except Exception as e:
        print(f"Ошибка при обновлении метрик: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Получение метрик для дашборда"""
    try:
        return jsonify(app_state.metrics), 200
    except Exception as e:
        print(f"Ошибка при получении метрик: {e}")
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500
    
@app.route('/api/ready', methods=['GET'])
def get_ready():
    try:
        return jsonify({"session_started": app_state.session_started})
    except Exception as e:
        print(f"error: {str(e)}"), 200
        return jsonify({"error": f"Внутренняя ошибка сервера: {str(e)}"}), 500

@app.route('/api/start', methods=['POST', 'GET'])
def start_session():
    app_state.session_started = True
    return jsonify({"message": "Сессия начата"}), 200
    
@app.route('/api/stop', methods=['POST', 'GET'])
def stop_session():
    app_state.session_started = False
    return jsonify({"message": "Сессия остановлена"}), 200

if __name__ == '__main__':
    print(f"Запуск сервера на {config['server']['host']}:{config['server']['port']}")
    print("Доступные endpoints:")
    print("  POST /api/users - обновление списка пользователей")
    print("  GET /api/users - получение списка пользователей")
    print("  POST /api/metrics - обновление метрик")
    print("  GET /api/metrics - получение метрик")
    print("  GET /api/ready - получение статуса сессии")
    print("  POST /api/start - начать сессию")
    print("  POST /api/stop - остановить сессию")
    
    app.run(debug=True, host=config['server']['host'], port=config['server']['port'])
