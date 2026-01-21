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
    """Conecta no SQLite"""
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
    """Página principal"""
    return render_template("index.html")

@app.route("/comando", methods=["POST"])
def comando():
    """Ligar/desligar LED"""
    global estado_led
    data = request.get_json() or request.form
    estado_led = data.get("led", estado_led)
    return jsonify({"status": "ok", "led": estado_led})

@app.route("/mensagem", methods=["POST"])
def set_mensagem():
    """Enviar mensagem para ESP32"""
    global mensagem
    data = request.get_json() or request.form
    mensagem = data.get("msg", mensagem)
    return jsonify({"mensagem": mensagem})

@app.route("/status", methods=["GET"])
def status():
    """Retorna status do LED e mensagem (mensagem é entregue apenas uma vez)"""
    global mensagem
    msg_para_envio = mensagem
    mensagem = ""  # limpa a mensagem após ser entregue
    return jsonify({"led": estado_led, "mensagem": msg_para_envio})

@app.route("/api/esp32", methods=["POST"])
def receber_esp32():
    """Recebe dados do ESP32"""
    dados = request.get_json()
    try:
        criar_tabela()  # garante que a tabela exista antes de inserir
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

@app.route("/api/registros", methods=["GET"])
def listar():
    """Lista todos os registros"""
    try:
        criar_tabela()  # garante que a tabela exista antes de consultar
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registros ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except sqlite3.OperationalError as e:
        return jsonify({"error": str(e)}), 500

# =========================
# Start do servidor
# =========================
criar_tabela()  # garante que a tabela exista antes de receber requisições

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
