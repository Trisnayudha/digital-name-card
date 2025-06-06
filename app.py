import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import sqlite3

# Muat file .env (jika ada)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'ganti_dengan_string_rahasia')

# Lokasi file database SQLite
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'digital_card.db')

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Buat tabel kartu_nama jika belum ada."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kartu_nama (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            perusahaan TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Pastikan tabel sudah dibuat
init_db()

@app.route('/', methods=['GET', 'POST'])
def form_card():
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        email = request.form.get('email', '').strip().lower()
        perusahaan = request.form.get('perusahaan', '').strip()

        # Validasi form
        if not nama or not email or not perusahaan:
            flash('Semua field wajib diisi.', 'danger')
            return redirect(url_for('form_card'))

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO kartu_nama (nama, email, perusahaan)
                VALUES (?, ?, ?)
            """, (nama, email, perusahaan))
            conn.commit()
            flash('Data berhasil disimpan!', 'success')
        except sqlite3.IntegrityError:
            flash('Email sudah terdaftar.', 'warning')
        finally:
            conn.close()

        return redirect(url_for('form_card'))

    return render_template('form.html')

if __name__ == '__main__':
    # Jalankan di http://127.0.0.1:5000/ dengan debug=True (hanya untuk lokal)
    app.run(host='127.0.0.1', port=5000, debug=True)
