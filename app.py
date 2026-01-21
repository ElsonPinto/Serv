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
    """Cria a tabela se não existir."""
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

def atualizar_tabela():
    """Adiciona colunas faltando se já existir tabela antiga."""
    conn = conectar_db()
    cursor = conn.cursor()
    colunas = {
        "numero_pacote": "INTEGER",
        "fazenda": "TEXT",
        "u1": "REAL",
        "u2": "REAL",
        "u3": "REAL",
        "u4": "REAL",
        "u5": "REAL",
        "fruto": "TEXT"
    }
    for nome, tipo in colunas.items():
        try:
            cursor.execute(f"ALTER TABLE registros ADD COLUMN {nome} {tipo}")
        except sqlite3.OperationalError:
            pass  # coluna já existe
    conn.commit()
    conn.close()

# =========================
# Página principal
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# Comando LED
# =========================
@app.route("/comando", methods=["POST"])
def comando():
    global estado_led
    data = request.get_json()
    estado_led = data.get("led", estado_led)
    return jsonify({"status": "ok", "led": estado_led})

# =========================
# Enviar mensagem
# =========================
@app.route("/mensagem", methods=["POST"])
def set_mensagem():
    global mensagem
    data = request.get_json()
    mensagem = data.get("msg", mensagem)
    return jsonify({"mensagem": mensagem})

# =========================
# Status do ESP32
# =========================
@app.route("/status", methods=["GET"])
def status():
    return jsonify({"led": estado_led, "mensagem": mensagem})

# =========================
# Receber dados do ESP32
# =========================
@app.route("/api/esp32", methods=["POST"])
def receber_esp32():
    dados = request.get_json()
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

# =========================
# Listar registros
# =========================
@app.route("/api/registros", methods=["GET"])
def listar():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registros ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# =========================
# Start
# =========================
if __name__ == "__main__":
    criar_tabela()
    atualizar_tabela()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
