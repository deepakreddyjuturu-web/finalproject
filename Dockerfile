FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "from app import initialize_database; initialize_database()"

EXPOSE 5000

ENV FLASK_ENV=production

CMD ["python", "app.py"]
