from flask import Flask

app = Flask(__name__)

@app.get("/")
def index():
    return "home", 200

@app.get("/health")
def health():
    return "ok", 200
