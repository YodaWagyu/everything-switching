# 🧪 Test Scenarios - Everything Switching App

## 📋 สารบัญ
1. [Authentication Tests](#1-authentication-tests)
2. [Filter & Query Tests](#2-filter--query-tests)
3. [View Mode Tests](#3-view-mode-tests)
4. [Reset Button Tests](#4-reset-button-tests)
5. [Admin Dashboard Tests](#5-admin-dashboard-tests)
6. [AI Insights Tests](#6-ai-insights-tests)
7. [Tracking System Tests](#7-tracking-system-tests)
8. [Export Tests](#8-export-tests)

---

## 1. Authentication Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| AUTH-01 | Login ด้วย User password | 1. เปิด app<br>2. ใส่ "PCB25"<br>3. กด Sign In | เข้าสู่หน้า Analysis ได้ |
| AUTH-02 | Login ด้วย Admin password | 1. เปิด app<br>2. ใส่ "admin1234"<br>3. กด Sign In | เข้า app + เห็น Admin Mode ใน sidebar |
| AUTH-03 | Login ด้วย password ผิด | 1. เปิด app<br>2. ใส่ "wrongpass"<br>3. กด Sign In | แสดง error "Invalid Access Key" |
| AUTH-04 | Logout | 1. Login สำเร็จ<br>2. กด Logout | กลับมาหน้า Login |

---

## 2. Filter & Query Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| FILTER-01 | เลือก Category | 1. Login<br>2. เลือก Category จาก dropdown | แสดง Subcategories ที่เกี่ยวข้อง |
| FILTER-02 | เลือก Period | 1. เลือก Before Period<br>2. เลือก After Period | สามารถ run query ได้ |
| FILTER-03 | Run Query | 1. ตั้งค่า filters ทั้งหมด<br>2. รอให้ query run | แสดงผลลัพธ์ในหน้า Analysis Scope |
| FILTER-04 | เลือก Brands | 1. เลือก brands จาก multiselect | แสดง status badge แสดงจำนวน brands |
| FILTER-05 | Select All Brands | 1. ติ๊ก "Select All"<br>2. | เลือกทุก brands อัตโนมัติ |

---

## 3. View Mode Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| VIEW-01 | สลับเป็น Product View | 1. เลือก "Product" ใน View Level | - Tab เปลี่ยนเป็น "Product Switching"<br>- Table headers เปลี่ยนเป็น "Product" |
| VIEW-02 | สลับกลับ Brand View | 1. เลือก "Brand" ใน View Level | - Tab เปลี่ยนเป็น "Brand Switching"<br>- Table headers เปลี่ยนเป็น "Brand" |
| VIEW-03 | Top N Filter (Disabled) | 1. ไม่ติ๊ก "Enable Top N"<br>2. | แสดงทุก items (ไม่ filter) |
| VIEW-04 | Top N Filter (Enabled) | 1. ติ๊ก "Enable Top N"<br>2. ปรับ slider เป็น 10 | แสดงเฉพาะ Top 10 items |

---

## 4. Reset Button Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| RESET-01 | Reset ล้าง Brands | 1. เลือก brands หลายตัว<br>2. กด Reset | Brands multiselect เป็น empty |
| RESET-02 | Reset ล้าง View Mode | 1. เปลี่ยนเป็น Product view<br>2. กด Reset | กลับเป็น Brand view (default) |
| RESET-03 | Reset ล้าง Top N | 1. Enable + ปรับ Top N<br>2. กด Reset | Top N ถูก disable |
| RESET-04 | Reset ล้าง Select All | 1. ติ๊ก Select All<br>2. กด Reset | Select All ถูก uncheck |

---

## 5. Admin Dashboard Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| ADMIN-01 | เข้า Dashboard ทันที | 1. Login admin<br>2. เลือก "Admin Dashboard" | แสดง Dashboard ทันที (ไม่ต้อง query) |
| ADMIN-02 | ดู KPI Cards | 1. เข้า Admin Dashboard | เห็น Total Sessions, Queries, Unique IPs |
| ADMIN-03 | ดู Daily Chart | 1. เข้า Admin Dashboard | เห็น Daily Usage Trend chart |
| ADMIN-04 | ดู Recent Sessions | 1. เข้า Admin Dashboard | เห็นตาราง Recent Sessions |
| ADMIN-05 | ดู Activity Log | 1. เข้า Admin Dashboard | เห็น Recent Activity Log พร้อม filter details |
| ADMIN-06 | User ไม่เห็น Dashboard | 1. Login ด้วย PCB25 | ไม่เห็น Admin Mode ใน sidebar |

---

## 6. AI Insights Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| AI-01 | Generate Insights (Brand) | 1. Run query<br>2. กด "Generate Complete Analysis" | แสดง AI insights เป็นภาษาไทย |
| AI-02 | Generate Insights (Product) | 1. เลือก Product view<br>2. กด Generate | ไม่ error, ใช้ Product column |
| AI-03 | Brand Highlighting | 1. Generate insights | Brand names มีสี highlight |
| AI-04 | Consistent Colors | 1. Generate insights | Brand เดียวกันมีสีเดียวกันทั้ง response |

---

## 7. Tracking System Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| TRACK-01 | Track Login | 1. Login ครั้งแรก | มี record ใน sessions table |
| TRACK-02 | Track Query | 1. Run query | มี event type "query" ใน events table |
| TRACK-03 | Track Filter Details | 1. Run query | event_data มี category, brands_count, period |
| TRACK-04 | Track AI Generation | 1. Generate AI insights | มี event type "ai_gen" |
| TRACK-05 | Track IP | 1. Login | IP address ถูกบันทึก |

---

## 8. Export Tests

| ID | Scenario | Steps | Expected Result |
|----|----------|-------|-----------------|
| EXPORT-01 | Export Excel | 1. Run query<br>2. ไปที่ Export tab<br>3. กด Excel | Download ไฟล์ .xlsx |
| EXPORT-02 | Export CSV | 1. Run query<br>2. ไปที่ Export tab<br>3. กด CSV | Download ไฟล์ .csv |

---

## 📊 Summary

| Category | Total Tests |
|----------|-------------|
| Authentication | 4 |
| Filter & Query | 5 |
| View Mode | 4 |
| Reset Button | 4 |
| Admin Dashboard | 6 |
| AI Insights | 4 |
| Tracking System | 5 |
| Export | 2 |
| **Total** | **34** |

---

## 🏃 วิธีรัน Manual Tests

1. เปิด app: `streamlit run app.py`
2. ทำตาม Steps ในแต่ละ scenario
3. ตรวจสอบ Expected Result
4. บันทึก ✅ / ❌

## 🤖 Automated Tests ที่มี

- `tests/test_tracking.py` - Unit tests (5 tests)
- `tests/test_e2e.py` - E2E browser tests (6 tests)
