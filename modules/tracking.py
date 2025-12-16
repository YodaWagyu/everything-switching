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
        
        # Total sessions
        total_sessions = pd.read_sql_query(
            "SELECT COUNT(DISTINCT session_id) as count FROM sessions",
            conn
        )['count'].iloc[0]
        
        # Sessions today - using parameterized query
        sessions_today = pd.read_sql_query(
            "SELECT COUNT(DISTINCT session_id) as count FROM sessions WHERE date(start_time) = ?",
            conn, params=(today,)
        )['count'].iloc[0]
        
        # Total queries
        total_queries = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'query'",
            conn
        )['count'].iloc[0]
        
        # Queries today - using parameterized query
        queries_today = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'query' AND date(timestamp) = ?",
            conn, params=(today,)
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


def get_date_range() -> Dict[str, Any]:
    """Get the earliest and latest dates in the database"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        # Get earliest session date
        earliest = pd.read_sql_query(
            "SELECT MIN(date(start_time)) as min_date FROM sessions",
            conn
        )['min_date'].iloc[0]
        
        # Get latest session date
        latest = pd.read_sql_query(
            "SELECT MAX(date(start_time)) as max_date FROM sessions",
            conn
        )['max_date'].iloc[0]
        
        conn.close()
        
        return {
            'earliest': earliest,
            'latest': latest
        }
    except Exception:
        return {
            'earliest': None,
            'latest': None
        }


def get_analytics_summary_filtered(start_date: str, end_date: str) -> Dict[str, Any]:
    """Get summary analytics for admin dashboard with date filter"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        # Total sessions in date range - parameterized
        total_sessions = pd.read_sql_query(
            "SELECT COUNT(DISTINCT session_id) as count FROM sessions WHERE date(start_time) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['count'].iloc[0]
        
        # Total queries in date range - parameterized
        total_queries = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'query' AND date(timestamp) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['count'].iloc[0]
        
        # Average query time in date range - parameterized
        avg_query_time = pd.read_sql_query(
            "SELECT AVG(duration_ms) as avg_ms FROM events WHERE event_type = 'query' AND duration_ms IS NOT NULL AND date(timestamp) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['avg_ms'].iloc[0] or 0
        
        # AI generations in date range - parameterized
        ai_generations = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'ai_gen' AND date(timestamp) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['count'].iloc[0]
        
        # Exports in date range - parameterized
        total_exports = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'export' AND date(timestamp) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['count'].iloc[0]
        
        # Unique IPs in date range - parameterized
        unique_ips = pd.read_sql_query(
            "SELECT COUNT(DISTINCT ip_address) as count FROM sessions WHERE ip_address != 'unknown' AND date(start_time) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['count'].iloc[0]
        
        # PDF generations - parameterized
        pdf_generations = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM events WHERE event_type = 'export' AND event_data LIKE '%pdf%' AND date(timestamp) BETWEEN ? AND ?",
            conn, params=(start_date, end_date)
        )['count'].iloc[0]
        
        conn.close()
        
        return {
            'total_sessions': int(total_sessions),
            'total_queries': int(total_queries),
            'avg_query_time_ms': round(avg_query_time, 0),
            'ai_generations': int(ai_generations),
            'total_exports': int(total_exports),
            'unique_ips': int(unique_ips),
            'pdf_generations': int(pdf_generations)
        }
    except Exception as e:
        return {
            'total_sessions': 0,
            'total_queries': 0,
            'avg_query_time_ms': 0,
            'ai_generations': 0,
            'total_exports': 0,
            'unique_ips': 0,
            'pdf_generations': 0,
            'error': str(e)
        }


def get_daily_usage_filtered(start_date: str, end_date: str) -> pd.DataFrame:
    """Get daily usage stats for charting with date filter"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT 
                date(timestamp) as date,
                COUNT(*) as events,
                COUNT(DISTINCT session_id) as sessions,
                SUM(CASE WHEN event_type = 'query' THEN 1 ELSE 0 END) as queries
            FROM events
            WHERE date(timestamp) BETWEEN ? AND ?
            GROUP BY date(timestamp)
            ORDER BY date
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame(columns=['date', 'events', 'sessions', 'queries'])


def get_recent_sessions_filtered(start_date: str, end_date: str, limit: int = 50) -> pd.DataFrame:
    """Get recent sessions with activity summary in date range"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT 
                s.session_id,
                s.user_role,
                s.ip_address,
                s.start_time,
                s.last_activity,
                COUNT(e.id) as event_count
            FROM sessions s
            LEFT JOIN events e ON s.session_id = e.session_id
            WHERE date(s.start_time) BETWEEN ? AND ?
            GROUP BY s.session_id
            ORDER BY s.start_time DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date, limit))
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame()


def get_recent_events_filtered(start_date: str, end_date: str, limit: int = 100) -> pd.DataFrame:
    """Get recent events with details for activity log in date range"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT 
                e.timestamp,
                s.user_role,
                s.ip_address,
                e.event_type,
                e.event_data
            FROM events e
            JOIN sessions s ON e.session_id = s.session_id
            WHERE date(e.timestamp) BETWEEN ? AND ?
            ORDER BY e.timestamp DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date, limit))
        conn.close()
        
        # Parse event_data JSON for display
        def parse_event_data(data):
            if data:
                try:
                    parsed = json.loads(data)
                    # Format key details
                    details = []
                    if 'category' in parsed:
                        details.append(f"Category: {parsed['category']}")
                    if 'brands_count' in parsed:
                        details.append(f"Brands: {parsed['brands_count']}")
                    if 'period1' in parsed:
                        details.append(f"Period: {parsed['period1']}")
                    if 'view_mode' in parsed:
                        details.append(f"Mode: {parsed['view_mode']}")
                    if 'role' in parsed:
                        details.append(f"Role: {parsed['role']}")
                    return "; ".join(details) if details else str(parsed)
                except (json.JSONDecodeError, KeyError):
                    return str(data)[:100]
            return ""
        
        df['details'] = df['event_data'].apply(parse_event_data)
        df = df.drop(columns=['event_data'])
        
        return df
    except Exception:
        return pd.DataFrame(columns=['timestamp', 'user_role', 'ip_address', 'event_type', 'details'])


def get_events_by_type_filtered(start_date: str, end_date: str) -> pd.DataFrame:
    """Get event counts by type for charting with date filter"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT event_type, COUNT(*) as count
            FROM events
            WHERE date(timestamp) BETWEEN ? AND ?
            GROUP BY event_type
            ORDER BY count DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame(columns=['event_type', 'count'])


def get_role_distribution_filtered(start_date: str, end_date: str) -> pd.DataFrame:
    """Get session counts by user role with date filter"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = '''
            SELECT user_role, COUNT(*) as count
            FROM sessions
            WHERE date(start_time) BETWEEN ? AND ?
            GROUP BY user_role
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        
        return df
    except Exception:
        return pd.DataFrame(columns=['user_role', 'count'])


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


def get_recent_events(limit: int = 30) -> pd.DataFrame:
    """Get recent events with details for activity log"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        query = f'''
            SELECT 
                e.timestamp,
                s.user_role,
                s.ip_address,
                e.event_type,
                e.event_data
            FROM events e
            JOIN sessions s ON e.session_id = s.session_id
            ORDER BY e.timestamp DESC
            LIMIT {limit}
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Parse event_data JSON for display
        def parse_event_data(data):
            if data:
                try:
                    parsed = json.loads(data)
                    # Format key details
                    details = []
                    if 'category' in parsed:
                        details.append(f"Category: {parsed['category']}")
                    if 'brands_count' in parsed:
                        details.append(f"Brands: {parsed['brands_count']}")
                    if 'period1' in parsed:
                        details.append(f"Period: {parsed['period1']}")
                    if 'view_mode' in parsed:
                        details.append(f"Mode: {parsed['view_mode']}")
                    if 'role' in parsed:
                        details.append(f"Role: {parsed['role']}")
                    return "; ".join(details) if details else str(parsed)
                except (json.JSONDecodeError, KeyError):
                    return str(data)[:100]
            return ""
        
        df['details'] = df['event_data'].apply(parse_event_data)
        df = df.drop(columns=['event_data'])
        
        return df
    except Exception:
        return pd.DataFrame(columns=['timestamp', 'user_role', 'ip_address', 'event_type', 'details'])

