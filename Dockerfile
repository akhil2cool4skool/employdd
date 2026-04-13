FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN playwright install --with-deps

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120"]
