import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import os

import os

class Database:
    def __init__(self, db_name=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_name = db_name or os.path.join(base_dir, "aidetector.db")
        self.init_db()


    
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analysis history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_name TEXT NOT NULL,
                file_size TEXT,
                file_type TEXT,
                is_ai BOOLEAN,
                confidence REAL,
                verdict TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Create demo user if not exists
        cursor.execute('SELECT * FROM users WHERE email = ?', ('demo@test.com',))
        if not cursor.fetchone():
            cursor.execute(
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                ('Demo User', 'demo@test.com', generate_password_hash('demo123'))
            )
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def create_user(self, name, email, password):
        """Create new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                (name, email, hashed_password)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'id': user_id, 'name': name, 'email': email}
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def verify_user(self, email, password):
        """Verify user credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            return {'id': user['id'], 'name': user['name'], 'email': user['email']}
        return None
    
    def save_analysis(self, user_id, file_name, file_size, file_type, is_ai, confidence, verdict):
        """Save analysis result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_history 
            (user_id, file_name, file_size, file_type, is_ai, confidence, verdict)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, file_name, file_size, file_type, is_ai, confidence, verdict))
        
        conn.commit()
        conn.close()
    
    def get_user_history(self, user_id, limit=10):
        """Get user's analysis history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM analysis_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return history
