from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = 'time_tracker.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            task TEXT NOT NULL,
            hours REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    employee_filter = request.args.get('employee', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = 'SELECT * FROM entries WHERE 1=1'
    params = []

    if employee_filter:
        query += ' AND employee LIKE ?'
        params.append(f'%{employee_filter}%')
    if date_from:
        query += ' AND date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND date <= ?'
        params.append(date_to)

    query += ' ORDER BY date DESC'

    conn = get_db()
    entries = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('index.html', entries=entries,
                           employee_filter=employee_filter,
                           date_from=date_from, date_to=date_to)

@app.route('/add', methods=['POST'])
def add():
    employee = request.form['employee']
    task = request.form['task']
    hours = request.form['hours']
    date = request.form['date']
    conn = get_db()
    conn.execute('INSERT INTO entries (employee, task, hours, date) VALUES (?, ?, ?, ?)',
                 (employee, task, hours, date))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    conn.execute('DELETE FROM entries WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()
    if request.method == 'POST':
        employee = request.form['employee']
        task = request.form['task']
        hours = request.form['hours']
        date = request.form['date']
        conn.execute('UPDATE entries SET employee=?, task=?, hours=?, date=? WHERE id=?',
                     (employee, task, hours, date, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        entry = conn.execute('SELECT * FROM entries WHERE id = ?', (id,)).fetchone()
        conn.close()
        return render_template('edit.html', entry=entry)

@app.route('/report')
def report():
    conn = get_db()
    report_data = conn.execute('''
        SELECT employee, SUM(hours) as total_hours, COUNT(*) as total_tasks
        FROM entries
        GROUP BY employee
        ORDER BY total_hours DESC
    ''').fetchall()
    conn.close()
    return render_template('report.html', report_data=report_data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
