"""
Unit Tests for Tracking Module
==============================
ทดสอบ functions ใน modules/tracking.py

Unit Test คือการทดสอบ function แต่ละตัวว่าทำงานถูกต้องหรือไม่
- ไม่ต้องรัน app จริง
- รันเร็วมาก
- ช่วยจับ bugs ตั้งแต่เนิ่นๆ

วิธีรัน:
    pytest tests/test_tracking.py -v
"""

import pytest
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# TEST 1: ทดสอบการ init database
# ============================================================================
def test_init_db_creates_tables():
    """
    ทดสอบว่า init_db() สร้าง database และ tables ได้ถูกต้อง
    
    นี่คือ "Arrange-Act-Assert" pattern ที่ใช้กันทั่วไป:
    - Arrange: เตรียมข้อมูล
    - Act: เรียก function ที่จะทดสอบ
    - Assert: ตรวจสอบผลลัพธ์
    """
    from modules import tracking
    import sqlite3
    
    # Arrange: ลบ database เก่า (ถ้ามี) เพื่อทดสอบจากศูนย์
    test_db_path = tracking.DB_PATH
    
    # Act: เรียก init_db()
    tracking.init_db()
    
    # Assert: ตรวจสอบว่า tables ถูกสร้าง
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    
    # ตรวจสอบว่า sessions table มีอยู่
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    assert cursor.fetchone() is not None, "sessions table should exist"
    
    # ตรวจสอบว่า events table มีอยู่
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
    assert cursor.fetchone() is not None, "events table should exist"
    
    conn.close()
    print("✅ test_init_db_creates_tables PASSED")


# ============================================================================
# TEST 2: ทดสอบการ log event
# ============================================================================
def test_log_event_stores_data():
    """
    ทดสอบว่า log_event() บันทึกข้อมูลลง database ได้ถูกต้อง
    """
    from modules import tracking
    import sqlite3
    import json
    
    # Arrange
    tracking.init_db()
    test_session_id = "test123"
    test_event_type = "test_event"
    test_event_data = {"action": "click", "button": "submit"}
    
    # Act
    tracking.log_event(test_session_id, test_event_type, test_event_data)
    
    # Assert
    conn = sqlite3.connect(str(tracking.DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, event_data 
        FROM events 
        WHERE session_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (test_session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None, "Event should be stored in database"
    assert row[0] == test_event_type, f"Event type should be '{test_event_type}'"
    
    stored_data = json.loads(row[1])
    assert stored_data["action"] == "click", "Event data should contain action"
    
    print("✅ test_log_event_stores_data PASSED")


# ============================================================================
# TEST 3: ทดสอบ analytics summary
# ============================================================================
def test_get_analytics_summary_returns_dict():
    """
    ทดสอบว่า get_analytics_summary() คืนค่า dictionary ที่มี keys ครบ
    """
    from modules import tracking
    
    # Arrange
    tracking.init_db()
    
    # Act
    summary = tracking.get_analytics_summary()
    
    # Assert: ต้องมี keys เหล่านี้
    required_keys = [
        'total_sessions',
        'sessions_today',
        'total_queries',
        'queries_today',
        'avg_query_time_ms',
        'ai_generations',
        'total_exports',
        'unique_ips'
    ]
    
    for key in required_keys:
        assert key in summary, f"Summary should contain '{key}'"
        assert isinstance(summary[key], (int, float)), f"'{key}' should be a number"
    
    print("✅ test_get_analytics_summary_returns_dict PASSED")


# ============================================================================
# TEST 4: ทดสอบ daily usage
# ============================================================================
def test_get_daily_usage_returns_dataframe():
    """
    ทดสอบว่า get_daily_usage() คืนค่า DataFrame ที่มี columns ถูกต้อง
    """
    from modules import tracking
    import pandas as pd
    
    # Arrange
    tracking.init_db()
    
    # Act
    df = tracking.get_daily_usage(7)
    
    # Assert
    assert isinstance(df, pd.DataFrame), "Should return a DataFrame"
    
    # ถ้ามีข้อมูล ต้องมี columns เหล่านี้
    if not df.empty:
        assert 'date' in df.columns, "Should have 'date' column"
        assert 'sessions' in df.columns, "Should have 'sessions' column"
        assert 'queries' in df.columns, "Should have 'queries' column"
    
    print("✅ test_get_daily_usage_returns_dataframe PASSED")


# ============================================================================
# TEST 5: ทดสอบ get_recent_events
# ============================================================================
def test_get_recent_events_returns_dataframe():
    """
    ทดสอบว่า get_recent_events() คืนค่า DataFrame ที่มี columns ถูกต้อง
    """
    from modules import tracking
    import pandas as pd
    
    # Arrange
    tracking.init_db()
    
    # Act
    df = tracking.get_recent_events(10)
    
    # Assert
    assert isinstance(df, pd.DataFrame), "Should return a DataFrame"
    
    # ตรวจสอบ columns (ถ้า empty จะมี default columns)
    expected_columns = ['timestamp', 'user_role', 'ip_address', 'event_type', 'details']
    for col in expected_columns:
        assert col in df.columns, f"Should have '{col}' column"
    
    print("✅ test_get_recent_events_returns_dataframe PASSED")


# ============================================================================
# รันทุก tests ถ้าเรียกไฟล์นี้โดยตรง
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 Running Unit Tests for Tracking Module")
    print("="*60 + "\n")
    
    # รันแต่ละ test
    test_init_db_creates_tables()
    test_log_event_stores_data()
    test_get_analytics_summary_returns_dict()
    test_get_daily_usage_returns_dataframe()
    test_get_recent_events_returns_dataframe()
    
    print("\n" + "="*60)
    print("✅ All Unit Tests PASSED!")
    print("="*60 + "\n")
