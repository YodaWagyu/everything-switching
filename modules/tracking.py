"""
User Tracking Module
Track usage analytics for Everything-Switching app
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st
from typing import Optional, Dict, Any, List
import pandas as pd


# Database path - stored in same directory as app
DB_PATH = Path(__file__).parent.parent / "usage_tracking.db"


def get_client_ip() -> str:
    """Get client IP address from Streamlit context"""
    try:
        # Try to get from Streamlit headers (works in Streamlit Cloud)
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            headers = st.context.headers
            # Check common headers for real IP
            for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
                if header in headers:
                    ip = headers[header]
                    # X-Forwarded-For may contain multiple IPs, take the first
                    if ',' in ip:
                        ip = ip.split(',')[0].strip()
                    return ip
        return "unknown"
    except Exception:
        return "unknown"


def init_db():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_role TEXT,
            ip_address TEXT,
            start_time TIMESTAMP,
            last_activity TIMESTAMP
        )
    ''')
    
    # Events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TIMESTAMP,
            event_type TEXT,
            event_data TEXT,
            duration_ms INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_or_create_session(user_role: str) -> str:
    """Get existing session or create new one"""
    # Initialize DB if needed
    init_db()
    
    # Check if we already have a session in this Streamlit session
    if 'tracking_session_id' in st.session_state:
        session_id = st.session_state.tracking_session_id
        # Update last activity
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sessions SET last_activity = ? WHERE session_id = ?
        ''', (datetime.now().isoformat(), session_id))
        conn.commit()
        conn.close()
        return session_id
    
    # Create new session
    session_id = str(uuid.uuid4())[:8]
    ip_address = get_client_ip()
    now = datetime.now().isoformat()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (session_id, user_role, ip_address, start_time, last_activity)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, user_role, ip_address, now, now))
    conn.commit()
    conn.close()
    
    # Store in Streamlit session
    st.session_state.tracking_session_id = session_id
    
    return session_id


def log_event(
    session_id: str,
    event_type: str,
    event_data: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[int] = None
):
    """Log an event to the database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO events (session_id, timestamp, event_type, event_data, duration_ms)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_id,
            datetime.now().isoformat(),
            event_type,
            json.dumps(event_data) if event_data else None,
            duration_ms
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        # Silently fail - don't break the app for tracking issues
        pass


def log_login(user_role: str):
    """Log a login event"""
    session_id = get_or_create_session(user_role)
    log_event(session_id, 'login', {'role': user_role})
    return session_id


def log_query(session_id: str, category: str, brands: List[str], view_mode: str, duration_ms: int):
    """Log a query execution"""
    log_event(session_id, 'query', {
        'category': category,
        'brands_count': len(brands),
        'view_mode': view_mode
    }, duration_ms)


def log_filter_change(session_id: str, filter_type: str, values: Any):
    """Log a filter selection change"""
    log_event(session_id, 'filter', {
        'filter_type': filter_type,
        'values': str(values)[:200]  # Limit length
    })


def log_ai_generation(session_id: str, view_mode: str, category: str):
    """Log AI insights generation"""
    log_event(session_id, 'ai_gen', {
        'view_mode': view_mode,
        'category': category
    })


def log_export(session_id: str, export_format: str):
    """Log an export/download"""
    log_event(session_id, 'export', {'format': export_format})


# ============ Analytics Functions ============

def get_analytics_summary() -> Dict[str, Any]:
    """Get summary analytics for admin dashboard"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # Total sessions
        total_sessions = pd.read_sql_query(
            "SELECT COUNT(DISTINCT session_id) as count FROM sessions",
            conn
        )['count'].iloc[0]
        
        # Sessions today
        sessions_today = pd.read_sql_query(
            f"SELECT COUNT(DISTINCT session_id) as count FROM sessions WHERE date(start_time) = '{today}'",
            conn
        )['count'].iloc[0]
        
        # Total queries
        total_queries = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'query'",
            conn
        )['count'].iloc[0]
        
        # Queries today
        queries_today = pd.read_sql_query(
            f"SELECT COUNT(*) as count FROM events WHERE event_type = 'query' AND date(timestamp) = '{today}'",
            conn
        )['count'].iloc[0]
        
        # Average query time
        avg_query_time = pd.read_sql_query(
            "SELECT AVG(duration_ms) as avg_ms FROM events WHERE event_type = 'query' AND duration_ms IS NOT NULL",
            conn
        )['avg_ms'].iloc[0] or 0
        
        # AI generations
        ai_generations = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'ai_gen'",
            conn
        )['count'].iloc[0]
        
        # Exports
        total_exports = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'export'",
            conn
        )['count'].iloc[0]
        
        # Unique IPs
        unique_ips = pd.read_sql_query(
            "SELECT COUNT(DISTINCT ip_address) as count FROM sessions WHERE ip_address != 'unknown'",
            conn
        )['count'].iloc[0]
        
        conn.close()
        
        return {
            'total_sessions': int(total_sessions),
            'sessions_today': int(sessions_today),
            'total_queries': int(total_queries),
            'queries_today': int(queries_today),
            'avg_query_time_ms': round(avg_query_time, 0),
            'ai_generations': int(ai_generations),
            'total_exports': int(total_exports),
            'unique_ips': int(unique_ips)
        }
    except Exception as e:
        return {
            'total_sessions': 0,
            'sessions_today': 0,
            'total_queries': 0,
            'queries_today': 0,
            'avg_query_time_ms': 0,
            'ai_generations': 0,
            'total_exports': 0,
            'unique_ips': 0,
            'error': str(e)
        }


def get_daily_usage(days: int = 14) -> pd.DataFrame:
    """Get daily usage stats for charting"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = f'''
            SELECT 
                date(timestamp) as date,
                COUNT(*) as events,
                COUNT(DISTINCT session_id) as sessions,
                SUM(CASE WHEN event_type = 'query' THEN 1 ELSE 0 END) as queries
            FROM events
            WHERE timestamp >= date('now', '-{days} days')
            GROUP BY date(timestamp)
            ORDER BY date
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame(columns=['date', 'events', 'sessions', 'queries'])


def get_recent_sessions(limit: int = 20) -> pd.DataFrame:
    """Get recent sessions with activity summary"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = f'''
            SELECT 
                s.session_id,
                s.user_role,
                s.ip_address,
                s.start_time,
                s.last_activity,
                COUNT(e.id) as event_count
            FROM sessions s
            LEFT JOIN events e ON s.session_id = e.session_id
            GROUP BY s.session_id
            ORDER BY s.start_time DESC
            LIMIT {limit}
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame()


def get_events_by_type() -> pd.DataFrame:
    """Get event counts by type for charting"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT event_type, COUNT(*) as count
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame(columns=['event_type', 'count'])


def get_role_distribution() -> pd.DataFrame:
    """Get session counts by user role"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT user_role, COUNT(*) as count
            FROM sessions
            GROUP BY user_role
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame(columns=['user_role', 'count'])
