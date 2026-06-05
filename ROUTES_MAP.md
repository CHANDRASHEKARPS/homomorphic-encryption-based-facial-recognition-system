# 🗺️ ROUTES MAP - Quick Reference Guide

## 📄 PAGE ROUTES (User Interface)

### Home & Dashboard
```
GET  /                    → index.html (Dashboard/Home)
```

### Employee Management
```
GET  /register           → register.html (Register new employee)
GET  /employees          → employees.html (View all employees)
```

### Attendance Operations
```
GET  /checkin            → checkin.html (Check-in interface)
GET  /checkout           → checkout.html (Check-out interface)
GET  /attendance         → attendance.html (View attendance records)
```

### Analytics & Security
```
GET  /stats              → stats.html (Statistics dashboard)
GET  /encrypted-data     → encrypted_data.html (View encrypted templates)
```

---

## 🔌 API ROUTES (Backend Endpoints)

### Employee Management APIs
```
POST   /api/register                      # Register new employee with face
DELETE /api/delete-employee/<employee_id> # Delete employee and all data
GET    /api/employees                     # Get all active employees
```

### Attendance APIs
```
POST   /api/checkin                       # Check-in with face recognition
POST   /api/checkout                      # Check-out with face recognition
GET    /api/attendance?date=YYYY-MM-DD    # Get attendance for date
```

### Data & Monitoring APIs
```
GET    /api/encrypted-templates           # View encrypted biometric data
GET    /api/stats                         # Get system statistics
GET    /api/health                        # Health check endpoint
```

---

## 📊 REQUEST/RESPONSE FORMATS

### POST /api/register
**Request:**
```json
{
    "employee_id": "EMP001",
    "name": "John Doe",
    "department": "Engineering",
    "face_images": ["base64_img1", "base64_img2", "base64_img3"]
}
```
**Response (Success):**
```json
{
    "status": "success",
    "message": "Employee registered successfully"
}
```
**Response (Error):**
```json
{
    "status": "error",
    "message": "Face already registered as Jane Smith (Similarity: 92.34%)"
}
```

---

### POST /api/checkin
**Request:**
```json
{
    "face_image": "base64_encoded_image"
}
```
**Response (Success):**
```json
{
    "status": "success",
    "employee_id": "EMP001",
    "name": "John Doe",
    "department": "Engineering",
    "confidence": 95.67,
    "timestamp": "2025-12-09 09:00:00",
    "time_display": "09:00:00 AM"
}
```
**Response (Not Registered):**
```json
{
    "status": "not_registered",
    "message": "Face not registered in the system.",
    "confidence": 65.23
}
```
**Response (Already Checked In):**
```json
{
    "status": "already_checked_in",
    "message": "John Doe already checked in",
    "employee_id": "EMP001",
    "name": "John Doe",
    "department": "Engineering",
    "confidence": 95.67,
    "time_display": "09:00:00 AM"
}
```

---

### POST /api/checkout
**Request:**
```json
{
    "face_image": "base64_encoded_image"
}
```
**Response (Success):**
```json
{
    "status": "success",
    "employee_id": "EMP001",
    "name": "John Doe",
    "department": "Engineering",
    "confidence": 95.67,
    "timestamp": "2025-12-09 18:30:00",
    "time_display": "06:30:00 PM",
    "type": "OUT"
}
```

---

### DELETE /api/delete-employee/EMP001
**Response:**
```json
{
    "status": "success",
    "message": "Employee EMP001 deleted"
}
```

---

### GET /api/employees
**Response:**
```json
{
    "status": "success",
    "employees": [
        {
            "employee_id": "EMP001",
            "name": "John Doe",
            "department": "Engineering",
            "registration_date": "2025-12-09 10:30:45",
            "status": "active",
            "last_checkin": "2025-12-09 09:00:00",
            "last_checkout": "2025-12-09 18:30:00"
        }
    ]
}
```

---

### GET /api/attendance?date=2025-12-09
**Response:**
```json
{
    "status": "success",
    "records": [
        {
            "employee_id": "EMP001",
            "name": "John Doe",
            "department": "Engineering",
            "timestamp": "2025-12-09 09:00:00",
            "time_display": "09:00:00 AM",
            "confidence": 95.67,
            "checkin_type": "IN"
        },
        {
            "employee_id": "EMP001",
            "name": "John Doe",
            "department": "Engineering",
            "timestamp": "2025-12-09 18:30:00",
            "time_display": "06:30:00 PM",
            "confidence": 93.45,
            "checkin_type": "OUT"
        }
    ]
}
```

---

### GET /api/stats
**Response:**
```json
{
    "status": "success",
    "stats": {
        "total_employees": 15,
        "total_templates": 15,
        "today_checkins": 12,
        "today_checkouts": 8
    }
}
```

---

### GET /api/encrypted-templates
**Response:**
```json
{
    "status": "success",
    "templates": [
        {
            "employee_id": "EMP001",
            "name": "John Doe",
            "department": "Engineering",
            "encrypted_data_preview": "a3f7e8d9c2b1a0f...",
            "data_length": 45678,
            "face_hash": "8a7f6e5d4c3b2a1...",
            "created_date": "2025-12-09 10:30:45"
        }
    ]
}
```

---

### GET /api/health
**Response:**
```json
{
    "status": "healthy",
    "time_display": "10:20:36 PM",
    "employees_count": 15,
    "today_checkins": 12
}
```

---

## 🔐 AUTHENTICATION

**Current Status:** No authentication required (internal system)

**Recommended for Production:**
- JWT token authentication
- Role-based access control (Admin, User)
- API key authentication for external integrations

---

## 📝 NOTES

### Status Codes
- `success` - Operation completed successfully
- `error` - Server error or validation failure
- `not_registered` - Face not found in system
- `already_checked_in` - Already checked in today
- `already_checked_out` - Already checked out today

### Confidence Scores
- **95%+** - Excellent match
- **88-95%** - Good match (accepted)
- **65-88%** - Weak match (rejected)
- **<65%** - Not registered

### Date Formats
- **Timestamp:** YYYY-MM-DD HH:MM:SS (24-hour format)
- **Time Display:** HH:MM:SS AM/PM (12-hour format)
- **Date:** YYYY-MM-DD
- **Timezone:** Asia/Kolkata (IST)

---

## 🚦 ROUTE FLOW DIAGRAMS

### Registration Flow
```
User → /register page
  ↓ (Captures 3+ photos)
POST /api/register
  ↓ (Validates & encrypts)
Database: employees + face_templates
  ↓
Success → Redirect to /employees
```

### Check-in Flow
```
User → /checkin page
  ↓ (Captures photo)
POST /api/checkin
  ↓ (Face recognition)
If Match: Database: attendance_logs (type=IN)
  ↓
Success → Display employee info
```

### Check-out Flow
```
User → /checkout page
  ↓ (Captures photo)
POST /api/checkout
  ↓ (Face recognition)
If Match: Database: attendance_logs (type=OUT)
  ↓
Success → Display employee info
```

### View Attendance Flow
```
User → /attendance page
  ↓ (Select date)
GET /api/attendance?date=YYYY-MM-DD
  ↓ (Query database)
Display: All check-ins/check-outs for date
```

---

## 🎯 QUICK ACCESS URLs

**Local Development:**
- Dashboard: http://localhost:5000/
- Register: http://localhost:5000/register
- Check-in: http://localhost:5000/checkin
- Check-out: http://localhost:5000/checkout
- Employees: http://localhost:5000/employees
- Attendance: http://localhost:5000/attendance
- Stats: http://localhost:5000/stats
- Encrypted Data: http://localhost:5000/encrypted-data

**API Base:** http://localhost:5000/api/

---

*Route map generated on 2025-12-09*
