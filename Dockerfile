FROM python:3.11-slim

WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Открываем порт для Flask API
EXPOSE 5000

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["python", "server.py"] 