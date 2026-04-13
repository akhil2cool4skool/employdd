FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8080
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
