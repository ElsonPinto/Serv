from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)

# =========================
# Variáveis globais
# =========================
estado_led = "off"
mensagem = "Nenhuma mensagem"

# =========================
# Banco de dados
# =========================
DB_FILE = "dados.db"

def conectar_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    """Cria a tabela registros se não existir"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_pacote INTEGER,
            fazenda TEXT,
            dispositivo_id TEXT,
            temperatura REAL,
            u1 REAL,
            u2 REAL,
            u3 REAL,
            u4 REAL,
            u5 REAL,
            fruto TEXT,
            data TEXT,
            hora TEXT
        )
    """)
    conn.commit()
    conn.close()

# =========================
# Rotas
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# Ligar/desligar LED
@app.route("/comando", methods=["POST"])
def comando():
    global estado_led
    data = request.get_json() or request.form
    estado_led = data.get("led", estado_led)
    return jsonify({"status": "ok", "led": estado_led})

# Enviar mensagem para ESP32
@app.route("/mensagem", methods=["POST"])
def set_mensagem():
    global mensagem
    data = request.get_json() or request.form
    mensagem = data.get("msg", mensagem)
    return jsonify({"mensagem": mensagem})

# Status do LED e mensagem (mensagem entregue apenas uma vez)
@app.route("/status", methods=["GET"])
def status():
    global mensagem
    msg_para_envio = mensagem
    mensagem = ""  # limpa a mensagem após ser entregue
    return jsonify({"led": estado_led, "mensagem": msg_para_envio})

# Receber dados do ESP32
@app.route("/api/esp32", methods=["POST"])
def receber_esp32():
    dados = request.get_json()
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registros (numero_pacote, fazenda, dispositivo_id, temperatura,
                                   u1, u2, u3, u4, u5, fruto, data, hora)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados.get("numero_pacote"),
            dados.get("fazenda"),
            dados.get("dispositivo_id"),
            dados.get("temperatura"),
            dados.get("u1"),
            dados.get("u2"),
            dados.get("u3"),
            dados.get("u4"),
            dados.get("u5"),
            dados.get("fruto"),
            dados.get("data"),
            dados.get("hora")
        ))
        conn.commit()
        conn.close()
        return jsonify({"status": "dados salvos"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Listar todos os registros
@app.route("/api/registros", methods=["GET"])
def listar():
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registros ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except sqlite3.OperationalError:
        return jsonify({"error": "Tabela ainda não existe"}), 500

# =========================
# Start
# =========================
if __name__ == "__main__":
    criar_tabela()  # garante que a tabela exista
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
