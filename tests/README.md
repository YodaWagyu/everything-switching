# Tests Directory

This folder contains automated tests for the Everything-Switching application.

## Structure
```
tests/
├── __init__.py
├── test_tracking.py      # Unit tests for tracking module
├── test_data_processor.py # Unit tests for data processor
└── test_e2e.py           # End-to-end browser tests
```

## Running Tests

### Unit Tests (pytest)
```bash
# Install pytest
pip install pytest

# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_tracking.py -v
```

### E2E Tests (Playwright)
```bash
# Install Playwright
pip install playwright pytest-playwright
playwright install chromium

# Start app first (in another terminal)
streamlit run app.py

# Run E2E tests
pytest tests/test_e2e.py -v
```

## What is Testing?

### Unit Test = ทดสอบ function เดี่ยว
- ทดสอบว่า function ทำงานถูกต้อง
- ไม่ต้องรัน app จริง
- รันเร็วมาก (วินาที)

### E2E Test = ทดสอบเหมือนคนใช้งานจริง
- เปิด browser จริง
- กดปุ่ม, พิมพ์ข้อมูล, ตรวจสอบผลลัพธ์
- ช้ากว่า แต่ครอบคลุมมาก
