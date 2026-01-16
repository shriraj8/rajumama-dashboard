"""
RAJUMAMA MT5 EA Web Dashboard
Flask application for monitoring and controlling MT5 EA
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rajumama-ea-secret-key-change-in-production'

# Database file path
DB_FILE = 'ea_data.db'

def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Trades table
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticket INTEGER,
                  open_time TEXT,
                  close_time TEXT,
                  symbol TEXT,
                  type TEXT,
                  volume REAL,
                  open_price REAL,
                  close_price REAL,
                  sl REAL,
                  tp REAL,
                  profit REAL,
                  status TEXT)''')
    
    # EA status table
    c.execute('''CREATE TABLE IF NOT EXISTS ea_status
                 (id INTEGER PRIMARY KEY,
                  is_running INTEGER,
                  last_update TEXT,
                  mama_value REAL,
                  fama_value REAL,
                  trend TEXT,
                  position_status TEXT,
                  balance REAL,
                  equity REAL)''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (id INTEGER PRIMARY KEY,
                  stop_loss_percent REAL,
                  take_profit_percent REAL,
                  trailing_stop_percent REAL,
                  lot_size REAL,
                  enable_short_trades INTEGER,
                  fast_limit REAL,
                  slow_limit REAL)''')
    
    # Initialize default status
    c.execute("SELECT COUNT(*) FROM ea_status")
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO ea_status VALUES 
                     (1, 0, ?, 0, 0, "NEUTRAL", "NONE", 10000, 10000)''',
                  (datetime.now().isoformat(),))
    
    # Initialize default settings
    c.execute("SELECT COUNT(*) FROM settings")
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO settings VALUES 
                     (1, 0.5, 1.0, 0.3, 0.1, 1, 0.5, 0.05)''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current EA status"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM ea_status WHERE id=1")
    status = c.fetchone()
    conn.close()
    
    if status:
        return jsonify({
            'is_running': bool(status[1]),
            'last_update': status[2],
            'mama_value': status[3],
            'fama_value': status[4],
            'trend': status[5],
            'position_status': status[6],
            'balance': status[7],
            'equity': status[8]
        })
    return jsonify({'error': 'No status data'}), 404

@app.route('/api/trades')
def get_trades():
    """Get trade history"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 50")
    trades = c.fetchall()
    conn.close()
    
    trades_list = []
    for trade in trades:
        trades_list.append({
            'id': trade[0],
            'ticket': trade[1],
            'open_time': trade[2],
            'close_time': trade[3],
            'symbol': trade[4],
            'type': trade[5],
            'volume': trade[6],
            'open_price': trade[7],
            'close_price': trade[8],
            'sl': trade[9],
            'tp': trade[10],
            'profit': trade[11],
            'status': trade[12]
        })
    
    return jsonify(trades_list)

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Get or update EA settings"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM settings WHERE id=1")
        settings = c.fetchone()
        conn.close()
        
        if settings:
            return jsonify({
                'stop_loss_percent': settings[1],
                'take_profit_percent': settings[2],
                'trailing_stop_percent': settings[3],
                'lot_size': settings[4],
                'enable_short_trades': bool(settings[5]),
                'fast_limit': settings[6],
                'slow_limit': settings[7]
            })
        return jsonify({'error': 'No settings data'}), 404
    
    elif request.method == 'POST':
        data = request.json
        c.execute('''UPDATE settings SET 
                     stop_loss_percent=?, take_profit_percent=?, 
                     trailing_stop_percent=?, lot_size=?, 
                     enable_short_trades=?, fast_limit=?, slow_limit=?
                     WHERE id=1''',
                  (data.get('stop_loss_percent', 0.5),
                   data.get('take_profit_percent', 1.0),
                   data.get('trailing_stop_percent', 0.3),
                   data.get('lot_size', 0.1),
                   int(data.get('enable_short_trades', True)),
                   data.get('fast_limit', 0.5),
                   data.get('slow_limit', 0.05)))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Settings updated'})

@app.route('/api/update', methods=['POST'])
def update_status():
    """Endpoint for MT5 EA to send updates"""
    data = request.json
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Update EA status
    c.execute('''UPDATE ea_status SET 
                 is_running=?, last_update=?, mama_value=?, fama_value=?,
                 trend=?, position_status=?, balance=?, equity=?
                 WHERE id=1''',
              (1, datetime.now().isoformat(),
               data.get('mama_value', 0),
               data.get('fama_value', 0),
               data.get('trend', 'NEUTRAL'),
               data.get('position_status', 'NONE'),
               data.get('balance', 0),
               data.get('equity', 0)))
    
    # If trade data included, insert trade
    if 'trade' in data:
        trade = data['trade']
        c.execute('''INSERT INTO trades 
                     (ticket, open_time, close_time, symbol, type, volume,
                      open_price, close_price, sl, tp, profit, status)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (trade.get('ticket'),
                   trade.get('open_time'),
                   trade.get('close_time'),
                   trade.get('symbol'),
                   trade.get('type'),
                   trade.get('volume'),
                   trade.get('open_price'),
                   trade.get('close_price'),
                   trade.get('sl'),
                   trade.get('tp'),
                   trade.get('profit'),
                   trade.get('status')))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/stats')
def get_stats():
    """Get trading statistics"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Total trades
    c.execute("SELECT COUNT(*) FROM trades WHERE status='closed'")
    total_trades = c.fetchone()[0]
    
    # Winning trades
    c.execute("SELECT COUNT(*) FROM trades WHERE status='closed' AND profit > 0")
    winning_trades = c.fetchone()[0]
    
    # Total profit
    c.execute("SELECT SUM(profit) FROM trades WHERE status='closed'")
    total_profit = c.fetchone()[0] or 0
    
    # Win rate
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    # Average profit
    c.execute("SELECT AVG(profit) FROM trades WHERE status='closed' AND profit > 0")
    avg_win = c.fetchone()[0] or 0
    
    c.execute("SELECT AVG(profit) FROM trades WHERE status='closed' AND profit < 0")
    avg_loss = c.fetchone()[0] or 0
    
    # Profit factor
    c.execute("SELECT SUM(profit) FROM trades WHERE status='closed' AND profit > 0")
    gross_profit = c.fetchone()[0] or 0
    
    c.execute("SELECT SUM(ABS(profit)) FROM trades WHERE status='closed' AND profit < 0")
    gross_loss = c.fetchone()[0] or 1
    
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    conn.close()
    
    return jsonify({
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': total_trades - winning_trades,
        'win_rate': round(win_rate, 2),
        'total_profit': round(total_profit, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2)
    })

@app.route('/api/control/<action>', methods=['POST'])
def control_ea(action):
    """Control EA (start/stop)"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    if action == 'start':
        c.execute("UPDATE ea_status SET is_running=1 WHERE id=1")
        message = 'EA started'
    elif action == 'stop':
        c.execute("UPDATE ea_status SET is_running=0 WHERE id=1")
        message = 'EA stopped'
    else:
        conn.close()
        return jsonify({'error': 'Invalid action'}), 400
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
