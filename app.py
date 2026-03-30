from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database setup
DATABASE = 'hotel.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS rooms
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  room_number TEXT UNIQUE NOT NULL,
                  room_type TEXT NOT NULL,
                  price REAL NOT NULL,
                  status TEXT NOT NULL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  guest_name TEXT NOT NULL,
                  guest_email TEXT NOT NULL,
                  room_id INTEGER NOT NULL,
                  checkin_date TEXT NOT NULL,
                  checkout_date TEXT NOT NULL,
                  nights INTEGER NOT NULL,
                  total_cost REAL NOT NULL,
                  FOREIGN KEY(room_id) REFERENCES rooms(id))''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ========== ROOM ENDPOINTS ==========

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM rooms')
    rooms = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(rooms)

@app.route('/api/rooms', methods=['POST'])
def add_room():
    data = request.json
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO rooms (room_number, room_type, price, status) VALUES (?, ?, ?, ?)',
                  (data['number'], data['type'], data['price'], data['status']))
        conn.commit()
        room_id = c.lastrowid
        conn.close()
        return jsonify({'id': room_id, 'message': 'Room added successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Room number already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    data = request.json
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE rooms SET room_number=?, room_type=?, price=?, status=? WHERE id=?',
                  (data['number'], data['type'], data['price'], data['status'], room_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Room updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM rooms WHERE id=?', (room_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Room deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ========== BOOKING ENDPOINTS ==========

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM bookings')
    bookings = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(bookings)

@app.route('/api/bookings', methods=['POST'])
def add_booking():
    data = request.json
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO bookings (guest_name, guest_email, room_id, checkin_date, checkout_date, nights, total_cost) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (data['guestName'], data['guestEmail'], data['roomId'], data['checkinDate'], data['checkoutDate'], data['nights'], data['totalCost']))
        conn.commit()
        booking_id = c.lastrowid
        conn.close()
        return jsonify({'id': booking_id, 'message': 'Booking created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/bookings/<int:booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM bookings WHERE id=?', (booking_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Booking deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ========== STATS ENDPOINT ==========

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) as total FROM rooms')
    total_rooms = c.fetchone()['total']
    
    c.execute('SELECT COUNT(*) as available FROM rooms WHERE status = "Available"')
    available = c.fetchone()['available']
    
    c.execute('SELECT COUNT(*) as occupied FROM rooms WHERE status = "Occupied"')
    occupied = c.fetchone()['occupied']
    
    c.execute('SELECT COUNT(*) as total FROM bookings')
    total_bookings = c.fetchone()['total']
    
    c.execute('SELECT SUM(total_cost) as revenue FROM bookings')
    revenue = c.fetchone()['revenue'] or 0
    
    conn.close()
    
    occupancy_rate = (occupied / total_rooms * 100) if total_rooms > 0 else 0
    
    return jsonify({
        'totalRooms': total_rooms,
        'availableRooms': available,
        'occupiedRooms': occupied,
        'totalBookings': total_bookings,
        'occupancyRate': round(occupancy_rate, 1),
        'totalRevenue': round(revenue, 2)
    })

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
