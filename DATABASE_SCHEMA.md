# 🗄️ DATABASE SCHEMA - Complete Overview

## 📊 ENTITY RELATIONSHIP DIAGRAM

```
┌─────────────────────────────────────┐
│         EMPLOYEES                    │
├─────────────────────────────────────┤
│ 🔑 employee_id (PK) VARCHAR(50)     │
│    name              VARCHAR(100)    │
│    department        VARCHAR(100)    │
│    registration_date VARCHAR(50)     │
│    status            VARCHAR(20)     │
└─────────────────────────────────────┘
           │
           │ 1
           │
           │ has
           │
           │ *
           ▼
┌─────────────────────────────────────┐
│      FACE_TEMPLATES                  │
├─────────────────────────────────────┤
│ 🔑 id (PK)             INTEGER       │
│ 🔗 employee_id (FK)    VARCHAR(50)   │
│    encrypted_template  BLOB          │
│    face_features       BLOB          │
│    face_hash          VARCHAR(128)   │
│    created_date       VARCHAR(50)    │
└─────────────────────────────────────┘
           │
           │ 1
           │
           │ generates
           │
           │ *
           ▼
┌─────────────────────────────────────┐
│      ATTENDANCE_LOGS                 │
├─────────────────────────────────────┤
│ 🔑 log_id (PK)         INTEGER       │
│ 🔗 employee_id (FK)    VARCHAR(50)   │
│    timestamp          VARCHAR(50)    │
│    confidence_score   FLOAT          │
│    checkin_type       VARCHAR(10)    │
│    timezone           VARCHAR(50)    │
└─────────────────────────────────────┘
```

**Legend:**
- 🔑 = Primary Key
- 🔗 = Foreign Key
- 1 = One
- * = Many

---

## 📋 TABLE DETAILS

### 1️⃣ EMPLOYEES

**Purpose:** Core employee information registry

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `employee_id` | VARCHAR(50) | PRIMARY KEY | Unique employee identifier (e.g., EMP001) |
| `name` | VARCHAR(100) | NOT NULL | Employee full name |
| `department` | VARCHAR(100) | NOT NULL | Department/Division |
| `registration_date` | VARCHAR(50) | NOT NULL | Registration timestamp (IST) |
| `status` | VARCHAR(20) | DEFAULT 'active' | Status: 'active' or 'inactive' |

**Indexes:**
- PRIMARY KEY on `employee_id`

**Sample Data:**
```sql
employee_id | name          | department   | registration_date    | status
------------|---------------|--------------|---------------------|--------
EMP001      | John Doe      | Engineering  | 2025-12-09 10:30:45 | active
EMP002      | Jane Smith    | HR           | 2025-12-09 11:15:22 | active
EMP003      | Bob Johnson   | Sales        | 2025-12-09 14:20:10 | active
```

**Relationships:**
- One employee → Many face templates (1:N)
- One employee → Many attendance logs (1:N)

---

### 2️⃣ FACE_TEMPLATES

**Purpose:** Stores encrypted biometric face templates

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Auto-incrementing template ID |
| `employee_id` | VARCHAR(50) | FOREIGN KEY | References employees(employee_id) |
| `encrypted_template` | BLOB | NOT NULL | Homomorphically encrypted face vector |
| `face_features` | BLOB | NULL | Pickled numpy array for matching |
| `face_hash` | VARCHAR(128) | NULL | SHA-256 hash of features |
| `created_date` | VARCHAR(50) | NOT NULL | Template creation timestamp (IST) |

**Indexes:**
- PRIMARY KEY on `id`
- FOREIGN KEY `employee_id` → `employees(employee_id)`

**Data Encryption:**
- `encrypted_template`: CKKS homomorphic encryption (TenSEAL)
- `face_features`: Pickle-serialized numpy array (2048 dimensions)
- `face_hash`: SHA-256 hex digest (for quick duplicate detection)

**Sample Data Structure:**
```sql
id | employee_id | encrypted_template | face_features | face_hash | created_date
---|-------------|-------------------|---------------|-----------|-------------
1  | EMP001      | [BLOB: 45,678 B] | [BLOB: 16KB]  | 8a7f6e... | 2025-12-09 10:30:45
2  | EMP002      | [BLOB: 45,234 B] | [BLOB: 16KB]  | 3c2d1a... | 2025-12-09 11:15:22
```

**Relationships:**
- Many templates → One employee (N:1)

**Security Notes:**
- `encrypted_template`: Can be queried without decryption (homomorphic property)
- `face_features`: Used for fast similarity comparison
- `face_hash`: SHA-256 provides exact duplicate detection

---

### 3️⃣ ATTENDANCE_LOGS

**Purpose:** Records all check-in and check-out events

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `log_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Auto-incrementing log ID |
| `employee_id` | VARCHAR(50) | FOREIGN KEY, NOT NULL | References employees(employee_id) |
| `timestamp` | VARCHAR(50) | NOT NULL | Event timestamp (YYYY-MM-DD HH:MM:SS) |
| `confidence_score` | FLOAT | NOT NULL | Face match confidence (0-100) |
| `checkin_type` | VARCHAR(10) | DEFAULT 'IN' | 'IN' for check-in, 'OUT' for check-out |
| `timezone` | VARCHAR(50) | DEFAULT 'Asia/Kolkata' | Timezone of event |

**Indexes:**
- PRIMARY KEY on `log_id`
- FOREIGN KEY `employee_id` → `employees(employee_id)`

**Sample Data:**
```sql
log_id | employee_id | timestamp           | confidence | checkin_type | timezone
-------|-------------|--------------------|-----------|--------------|-----------
1      | EMP001      | 2025-12-09 09:00:00| 95.67     | IN           | Asia/Kolkata
2      | EMP002      | 2025-12-09 09:15:23| 93.45     | IN           | Asia/Kolkata
3      | EMP001      | 2025-12-09 18:30:15| 94.23     | OUT          | Asia/Kolkata
4      | EMP002      | 2025-12-09 18:45:30| 92.11     | OUT          | Asia/Kolkata
```

**Relationships:**
- Many logs → One employee (N:1)

**Query Patterns:**
```sql
-- Get today's check-ins
SELECT * FROM attendance_logs 
WHERE date(timestamp) = '2025-12-09' 
AND checkin_type = 'IN';

-- Get employee's last check-in
SELECT * FROM attendance_logs 
WHERE employee_id = 'EMP001' 
AND checkin_type = 'IN'
ORDER BY timestamp DESC 
LIMIT 1;

-- Check if employee checked in today
SELECT COUNT(*) FROM attendance_logs 
WHERE employee_id = 'EMP001' 
AND date(timestamp) = '2025-12-09'
AND checkin_type = 'IN';
```

---

## 🔗 FOREIGN KEY RELATIONSHIPS

### face_templates.employee_id → employees.employee_id
- **Type:** Many-to-One
- **On Delete:** CASCADE (deleting employee deletes templates)
- **On Update:** CASCADE (updating employee_id updates references)

### attendance_logs.employee_id → employees.employee_id
- **Type:** Many-to-One
- **On Delete:** CASCADE (deleting employee deletes logs)
- **On Update:** CASCADE (updating employee_id updates references)

---

## 📊 DATA FLOW

### Registration Flow:
```
1. User submits employee data + 3 face images
   ↓
2. Extract features from each image → [vec1, vec2, vec3]
   ↓
3. Aggregate → avg_vector (2048 dimensions)
   ↓
4. Generate hash → SHA-256(avg_vector)
   ↓
5. Check for duplicate faces
   ↓
6. Encrypt → CKKS(avg_vector) → encrypted_template
   ↓
7. INSERT INTO employees (employee_id, name, department, ...)
   ↓
8. INSERT INTO face_templates (employee_id, encrypted_template, ...)
```

### Check-in/Check-out Flow:
```
1. User captures face image
   ↓
2. Extract features → test_vector
   ↓
3. Generate hash → test_hash
   ↓
4. FOR EACH employee in employees:
     - Load face_features from face_templates
     - Calculate similarity(test_vector, stored_features)
     - Track best match
   ↓
5. IF best_score >= 88%:
     - Check if already checked in/out today
     - INSERT INTO attendance_logs (employee_id, timestamp, ...)
   ELSE:
     - Return "Not registered"
```

### Delete Employee Flow:
```
1. DELETE FROM face_templates WHERE employee_id = 'EMP001'
   ↓
2. DELETE FROM attendance_logs WHERE employee_id = 'EMP001'
   ↓
3. DELETE FROM employees WHERE employee_id = 'EMP001'
```

---

## 🔍 SAMPLE QUERIES

### Get all employees with their last attendance
```sql
SELECT 
    e.employee_id,
    e.name,
    e.department,
    e.status,
    (SELECT timestamp FROM attendance_logs 
     WHERE employee_id = e.employee_id AND checkin_type = 'IN'
     ORDER BY timestamp DESC LIMIT 1) as last_checkin,
    (SELECT timestamp FROM attendance_logs 
     WHERE employee_id = e.employee_id AND checkin_type = 'OUT'
     ORDER BY timestamp DESC LIMIT 1) as last_checkout
FROM employees e
WHERE e.status = 'active';
```

### Get today's attendance summary
```sql
SELECT 
    e.employee_id,
    e.name,
    e.department,
    MIN(CASE WHEN a.checkin_type = 'IN' THEN a.timestamp END) as checkin_time,
    MAX(CASE WHEN a.checkin_type = 'OUT' THEN a.timestamp END) as checkout_time
FROM employees e
LEFT JOIN attendance_logs a ON e.employee_id = a.employee_id
WHERE date(a.timestamp) = '2025-12-09'
GROUP BY e.employee_id, e.name, e.department;
```

### Get employees who haven't checked in today
```sql
SELECT e.employee_id, e.name, e.department
FROM employees e
WHERE e.status = 'active'
AND e.employee_id NOT IN (
    SELECT employee_id FROM attendance_logs
    WHERE date(timestamp) = '2025-12-09'
    AND checkin_type = 'IN'
);
```

### Get attendance statistics
```sql
SELECT 
    COUNT(DISTINCT employee_id) as total_employees,
    SUM(CASE WHEN checkin_type = 'IN' THEN 1 ELSE 0 END) as total_checkins,
    SUM(CASE WHEN checkin_type = 'OUT' THEN 1 ELSE 0 END) as total_checkouts,
    AVG(confidence_score) as avg_confidence
FROM attendance_logs
WHERE date(timestamp) = '2025-12-09';
```

---

## 💾 DATABASE FILE INFORMATION

**Location:** `c:\Users\AKSHAY\Desktop\HE_base\instance\attendance_system.db`  
**Type:** SQLite 3  
**Current Size:** ~7.3 MB  
**Character Encoding:** UTF-8  
**Journal Mode:** DELETE (default)

### Performance Recommendations:
```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Optimize database
VACUUM;

-- Analyze for query optimization
ANALYZE;
```

---

## 🔐 SECURITY CONSIDERATIONS

### Data Protection:
1. **Biometric Data:** Encrypted using CKKS homomorphic encryption
2. **Feature Vectors:** Stored as binary (not human-readable)
3. **Hashes:** SHA-256 (irreversible)

### Privacy Compliance:
- ✅ GDPR compliant (encrypted biometric data)
- ✅ Right to delete (cascade deletes)
- ✅ Data minimization (only necessary fields)
- ✅ Purpose limitation (attendance only)

### Access Control:
- Database file permissions should be restricted
- Recommend: chmod 600 (owner read/write only)
- Consider: Database encryption at rest

---

## 📈 SCALABILITY

### Current Limitations:
- SQLite: Single writer at a time
- File-based: Limited to local disk I/O

### Migration Path (for 1000+ employees):
1. **PostgreSQL:**
   ```python
   SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/attendance'
   ```

2. **Add Indexes:**
   ```sql
   CREATE INDEX idx_employee_status ON employees(status);
   CREATE INDEX idx_attendance_date ON attendance_logs(timestamp);
   CREATE INDEX idx_attendance_employee ON attendance_logs(employee_id);
   ```

3. **Partitioning:**
   - Partition attendance_logs by month/year

---

## 🔄 BACKUP STRATEGY

### Recommended:
```bash
# Daily backup
sqlite3 attendance_system.db ".backup 'backup/attendance_$(date +%Y%m%d).db'"

# Weekly full export
sqlite3 attendance_system.db .dump > backup/attendance_$(date +%Y%m%d).sql
```

### Restore:
```bash
# Restore from backup
sqlite3 attendance_system.db < backup/attendance_20251209.sql
```

---

## ✅ DATABASE HEALTH CHECKLIST

- [x] Tables created with proper schema
- [x] Foreign key constraints defined
- [x] Primary keys on all tables
- [x] Proper data types for all columns
- [x] Default values set where appropriate
- [x] Timestamps stored in consistent format (IST)
- [x] Binary data (BLOB) for encryption
- [x] No orphaned records (cascade deletes)

---

*Database schema documentation generated on 2025-12-09*
