from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime
app = Flask(__name__)
# --- PASSWORD BUAT NGEDIT DI WEB ---
ADMIN_PASSWORD = "your_password"
def get_db_connection():
    conn = sqlite3.connect('finance.db')
    conn.row_factory = sqlite3.Row
    return conn
def format_rupiah(value):
    return f"Rp {value:,.0f}".replace(",", ".")
@app.route('/')
def home():
    return "Badawi Wallet Server Running."
@app.route('/dashboard')
def dashboard():
    user_id = request.args.get('uid')
    if not user_id: return "❌ Missing UID"
    conn = get_db_connection()
    in_sum = conn.execute("SELECT sum(amount) FROM transactions WHERE user_id=? AND type='IN'", (user_id,)).fetchone()[0] or 0
    out_sum = conn.execute("SELECT sum(amount) FROM transactions WHERE user_id=? AND type='OUT'", (user_id,)).fetchone()[0] or 0
    saldo = in_sum - out_sum
    # Ambil SEMUA history untuk tabel
    query_history = "SELECT id, description, type, amount, strftime('%d-%m-%Y %H:%M', date) as formatted_date FROM transactions WHERE user_id=? ORDER BY id DESC"
    history = conn.execute(query_history, (user_id,)).fetchall()
    conn.close()
    return render_template('dashboard.html', 
                           saldo=format_rupiah(saldo), 
                           pemasukan=format_rupiah(in_sum), 
                           pengeluaran=format_rupiah(out_sum),
                           history=history,
                           uid=user_id)
@app.route('/api/chart-data')
def chart_data():
    user_id = request.args.get('uid')
    filter_type = request.args.get('filter', 'week')
    conn = get_db_connection()

    query = ""
    if filter_type == 'week':
        query = "SELECT strftime('%d-%m', date) as tgl, sum(amount) as total FROM transactions WHERE user_id=? AND type='OUT' AND date >= date('now', '-7 days') GROUP BY strftime('%Y-%m-%d', date) ORDER BY date ASC"
    elif filter_type == 'month':
        query = "SELECT strftime('%d-%m', date) as tgl, sum(amount) as total FROM transactions WHERE user_id=? AND type='OUT' AND date >= date('now', '-30 days') GROUP BY strftime('%Y-%m-%d', date) ORDER BY date ASC"
    elif filter_type == 'year':
        query = "SELECT strftime('%Y-%m', date) as tgl, sum(amount) as total FROM transactions WHERE user_id=? AND type='OUT' AND date >= date('now', '-1 year') GROUP BY strftime('%Y-%m', date) ORDER BY date ASC"
    data = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return jsonify({'labels': [row['tgl'] for row in data], 'values': [row['total'] for row in data]})
# --- API HAPUS TRANSAKSI ---
@app.route('/api/delete', methods=['POST'])
def delete_trans():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Password Salah!'}), 403

    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id=?", (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})
# --- API EDIT TRANSAKSI ---
@app.route('/api/update', methods=['POST'])
def update_trans():
    data = request.json
    if data.get('password') != ADMIN_PASSWORD:
        return jsonify({'status': 'error', 'message': 'Password Salah!'}), 403

    conn = get_db_connection()
    conn.execute("UPDATE transactions SET amount=?, description=? WHERE id=?", (data['amount'], data['desc'], data['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)