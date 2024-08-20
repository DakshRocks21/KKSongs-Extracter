
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production

ENV SECRET_KEY=your_secret_key

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
