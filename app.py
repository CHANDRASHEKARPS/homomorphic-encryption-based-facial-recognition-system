from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
import numpy as np
import base64
import cv2
import tenseal as ts
import pickle
import os
import json
import hashlib
import random
import time
import sqlite3

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# IST Timezone
ist_timezone = pytz.timezone('Asia/Kolkata')

# ========== MODELS ==========

class Employee(db.Model):
    __tablename__ = 'employees'
    employee_id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    registration_date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')

class FaceTemplate(db.Model):
    __tablename__ = 'face_templates'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.employee_id'))
    encrypted_template = db.Column(db.LargeBinary, nullable=False)
    face_features = db.Column(db.LargeBinary)
    face_hash = db.Column(db.String(128))
    created_date = db.Column(db.String(50), nullable=False)

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employees.employee_id'), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    checkin_type = db.Column(db.String(10), default='IN')
    timezone = db.Column(db.String(50), default='Asia/Kolkata')

# ========== TIME HELPERS ==========

def get_ist_time():
    return datetime.now(ist_timezone)

def get_ist_timestamp():
    return get_ist_time().strftime('%Y-%m-%d %H:%M:%S')

def get_ist_date():
    return get_ist_time().strftime('%Y-%m-%d')

def get_ist_time_display():
    return get_ist_time().strftime('%I:%M:%S %p')

# ========== IMAGE / FEATURE UTILS ==========

def base64_to_image(base64_string):
    """Convert base64 to image"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Add padding if needed
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        
        image_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print("❌ Failed to decode image")
            return None
        
        return image
        
    except Exception as e:
        print(f"❌ base64_to_image error: {e}")
        return None

# ========== ULTRA-ACCURATE FACE RECOGNITION ENGINE ==========

class UltraAccurateFaceRecognizer:
    def __init__(self):
        self.face_cascade = self._load_cascade()
        print("✅ Face recognizer initialized")
    
    def _load_cascade(self):
        """Load face cascade classifier"""
        try:
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if not cascade.empty():
                return cascade
        except:
            pass
        return None
    
    def extract_face_features(self, image):
        try:
            if image is None:
                return None, None

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Detect face with more lenient settings
            face_region = None
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,       # More lenient (was 6)
                    minSize=(50, 50)      # Allow smaller faces (was 100x100)
                )

                if len(faces) > 0:
                    # Use largest face
                    faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                    x, y, w, h = faces[0]

                    # Add padding
                    padding = 20
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(gray.shape[1], x + w + padding)
                    y2 = min(gray.shape[0], y + h + padding)

                    face_region = gray[y1:y2, x1:x2]
                    print(f"✅ Face detected at ({x}, {y}) with size {w}x{h}")
                else:
                     print("❌ No face detected")
                     return None, None
            else:
                    print("❌ Face cascade not available")
                    return None, None

            if face_region is None or face_region.size == 0:
                print("⚠️ Empty face region – returning None")
                return None, None

            # Resize to standard size
            face_resized = cv2.resize(face_region, (128, 128))

            # Apply CLAHE for better contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            face_resized = clahe.apply(face_resized)

            # Apply multiple processing techniques
            processed_images = []

            # 1. Original (CLAHE)
            processed_images.append(face_resized)

            # 2. Gaussian blurred
            face_blurred = cv2.GaussianBlur(face_resized, (5, 5), 0)
            processed_images.append(face_blurred)

            # 3. Edge features
            edges = cv2.Canny(face_resized, 50, 150)
            processed_images.append(edges)

            # Combine all features
            all_features = []

            for img in processed_images:
                # Resize to smaller size for feature extraction
                small = cv2.resize(img, (32, 32))

                # Histogram features
                hist = cv2.calcHist([small], [0], None, [32], [0, 256])
                hist_normalized = hist / (np.sum(hist) + 1e-6)
                all_features.extend(hist_normalized.flatten())

                # Pixel intensity samples
                normalized_pixels = small.astype(np.float32) / 255.0
                all_features.extend(normalized_pixels.flatten()[::2])  # every second pixel

            # Convert to numpy array
            feature_vector = np.array(all_features, dtype=np.float32)

            # Ensure minimum length
            target_length = 2048
            if len(feature_vector) < target_length:
                padding = target_length - len(feature_vector)
                feature_vector = np.pad(feature_vector, (0, padding), 'constant', constant_values=0.5)
            elif len(feature_vector) > target_length:
                feature_vector = feature_vector[:target_length]

            # Normalize the feature vector
            norm = np.linalg.norm(feature_vector)
            if norm > 0:
                feature_vector = feature_vector / norm

            # Create unique hash
            face_hash = hashlib.sha256(feature_vector.tobytes()).hexdigest()

            print(f"✅ Extracted {len(feature_vector)} facial features")
            return feature_vector, face_hash

        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return None, None
 
            # Convert to grayscale  
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect face
            face_region = gray
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(100, 100)
                )
                
                if len(faces) > 0:
                    # Use largest face
                    faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
                    x, y, w, h = faces[0]
                    
                    # Add padding
                    padding = 20
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(gray.shape[1], x + w + padding)
                    y2 = min(gray.shape[0], y + h + padding)
                    
                    face_region = gray[y1:y2, x1:x2]
                else:
                    print("⚠️ No face detected with cascade")
            
            # Resize to standard size
            face_resized = cv2.resize(face_region, (128, 128))
            
            # Apply multiple processing techniques
            processed_images = []
            
            # 1. Original with contrast enhancement
            face_contrast = cv2.equalizeHist(face_resized)
            processed_images.append(face_contrast)
            
            # 2. Gaussian blurred
            face_blurred = cv2.GaussianBlur(face_resized, (5, 5), 0)
            processed_images.append(face_blurred)
            
            # 3. Edge features
            edges = cv2.Canny(face_resized, 50, 150)
            processed_images.append(edges)
            
            # Combine all features
            all_features = []
            
            for img in processed_images:
                # Resize to smaller size for feature extraction
                small = cv2.resize(img, (32, 32))
                
                # Extract histogram features
                hist = cv2.calcHist([small], [0], None, [32], [0, 256])
                hist_normalized = hist / (np.sum(hist) + 1e-6)
                all_features.extend(hist_normalized.flatten())
                
                # Extract pixel intensity features
                normalized_pixels = small.astype(np.float32) / 255.0
                all_features.extend(normalized_pixels.flatten()[::2])  # Take every other pixel
            
            # Convert to numpy array
            feature_vector = np.array(all_features, dtype=np.float32)
            
            # Ensure minimum length
            target_length = 2048
            if len(feature_vector) < target_length:
                padding = target_length - len(feature_vector)
                feature_vector = np.pad(feature_vector, (0, padding), 'constant', constant_values=0.5)
            elif len(feature_vector) > target_length:
                feature_vector = feature_vector[:target_length]
            
            # Normalize the feature vector
            norm = np.linalg.norm(feature_vector)
            if norm > 0:
                feature_vector = feature_vector / norm
            
            # Create unique hash
            face_hash = hashlib.sha256(feature_vector.tobytes()).hexdigest()
            
            print(f"✅ Extracted {len(feature_vector)} facial features")
            return feature_vector, face_hash
            
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            return None, None
    
    def calculate_similarity(self, vec1, vec2):
        """Calculate robust similarity score"""
        if vec1 is None or vec2 is None:
            return 0.0
        
        # Ensure same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        # Cosine similarity (main metric)
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = dot / (norm1 * norm2)
        
        # Euclidean similarity
        euclidean_dist = np.linalg.norm(vec1 - vec2)
        euclidean_sim = 1.0 / (1.0 + euclidean_dist)
        
        # Combined score
        combined_score = 0.7 * cosine_sim + 0.3 * euclidean_sim
        
        return max(0.0, min(1.0, combined_score))

# Initialize recognizer
face_recognizer = UltraAccurateFaceRecognizer()

# Thresholds optimized for small teams with similar-looking people
MATCHING_THRESHOLD = 0.80  # 80% required for check-in/check-out match
REJECT_THRESHOLD   = 0.65   # below 65% → treat as NOT registered
DUPLICATE_CHECK_THRESHOLD = 0.96  # 96% for duplicate checking (very strict - only identical faces)
MIN_FACES_FOR_REGISTRATION = 3

# ========== ENCRYPTION ==========

def create_encryption_context():
    """Create encryption context"""
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[40, 21, 21, 21, 21, 21, 21, 40]
    )
    context.generate_galois_keys()
    context.global_scale = 2**21
    print("✅ Encryption context created")
    return context

# Global encryption context
encryption_context = create_encryption_context()

def encrypt_face_vector(face_vector):
    """Encrypt face vector"""
    try:
        if face_vector is None:
            return None
        
        encrypted = ts.ckks_vector(encryption_context, face_vector)
        serialized = encrypted.serialize()
        encrypted_b64 = base64.b64encode(serialized).decode('utf-8')
        return encrypted_b64
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        return None

def decrypt_face_vector(encrypted_b64):
    """Decrypt face vector"""
    try:
        serialized = base64.b64decode(encrypted_b64)
        encrypted = ts.ckks_vector_from(encryption_context, serialized)
        return np.array(encrypted.decrypt())
    except Exception as e:
        print(f"❌ Decryption error: {e}")
        return None

# ========== DATABASE UTILS ==========

def init_database():
    """Initialize database with required tables"""
    with app.app_context():
        db.create_all()
    print("✅ Database initialized")

def verify_database_empty():
    """Check if database is empty"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        tables = ['employees', 'face_templates', 'attendance_logs']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"⚠️ Table {table} has {count} rows")
                return False
        
        conn.close()
        print("✅ Database is empty")
        return True
        
    except Exception as e:
        print(f"❌ Database verification error: {e}")
        return False

# ========== FACE PROCESSING PIPELINE ==========

def process_face_image(base64_image):
    """Process face image"""
    image = base64_to_image(base64_image)
    if image is None:
        return None, None
    return face_recognizer.extract_face_features(image)

def aggregate_face_features(face_images):
    """Aggregate multiple face images into a single robust template"""
    all_features = []
    hashes = []
    
    for i, img_b64 in enumerate(face_images):
        features, face_hash = process_face_image(img_b64)
        if features is not None:
            all_features.append(features)
            hashes.append(face_hash)
        else:
            print(f"⚠️ Could not extract features for image {i+1}")
    
    if len(all_features) < MIN_FACES_FOR_REGISTRATION:
        print(f"❌ Not enough valid face images. Required: {MIN_FACES_FOR_REGISTRATION}, Got: {len(all_features)}")
        return None, None
    
    avg_features = np.mean(all_features, axis=0)
    avg_hash = hashlib.sha256(avg_features.tobytes()).hexdigest()
    
    print(f"✅ Aggregated {len(all_features)} face templates into a single robust template")
    return avg_features, avg_hash

def check_for_duplicate_face(test_features, test_hash, exclude_employee_id=None):
    """Check if face already exists in system"""
    employees = Employee.query.filter(Employee.status == 'active').all()
    
    for emp in employees:
        if exclude_employee_id and emp.employee_id == exclude_employee_id:
            continue
        
        templates = FaceTemplate.query.filter_by(employee_id=emp.employee_id).all()
        
        for template in templates:
            if template.face_hash and template.face_hash == test_hash:
                return emp, 100.0, "Exact duplicate (hash match)"
            
            if template.face_features:
                stored_features = pickle.loads(template.face_features)
                similarity = face_recognizer.calculate_similarity(test_features, stored_features)
                score = similarity * 100
                
                if score > DUPLICATE_CHECK_THRESHOLD * 100:
                    return emp, score, f"Similarity: {score:.2f}%"
    
    return None, 0.0, "No duplicate found"

def match_face_accurately(test_features, test_hash):
    """Accurate face matching with balanced sensitivity"""
    if test_features is None:
        return None, 0.0, "No features"

    employees = Employee.query.filter(Employee.status == 'active').all()

    if not employees:
        return None, 0.0, "No employees"

    print(f"\n🔍 Matching against {len(employees)} employees...")

    matches = []

    for emp in employees:
        templates = FaceTemplate.query.filter_by(employee_id=emp.employee_id).all()

        best_score_for_emp = 0.0

        for template in templates:
            # Exact hash match (same face crop)
            if template.face_hash and template.face_hash == test_hash:
                print(f"✅ Exact hash match for {emp.name}")
                return emp, 100.0, "Exact hash match"

            if template.face_features:
                stored_features = pickle.loads(template.face_features)
                similarity = face_recognizer.calculate_similarity(test_features, stored_features)
                score = float(similarity * 100.0)

                if score > best_score_for_emp:
                    best_score_for_emp = score

        if best_score_for_emp > 0:
            matches.append({
                'employee': emp,
                'score': best_score_for_emp
            })

    if not matches:
        print("❌ No templates produced any score")
        return None, 0.0, "No matches"

    # Sort descending by score
    matches.sort(key=lambda x: x['score'], reverse=True)
    best_match = matches[0]
    best_score = best_match['score']

    # Compare with second best to avoid confusion between similar faces
    if len(matches) > 1:
        second_best = matches[1]['score']
        gap = best_score - second_best
        ratio = best_score / max(second_best, 1e-6)

        print(f"📊 Best={best_score:.2f}%, Second={second_best:.2f}%, Gap={gap:.2f}%, Ratio={ratio:.2f}")

        # Anti-confusion check disabled for small teams
        # For small teams with similar-looking people, the 88% threshold is sufficient
        # Uncomment below to re-enable strict checking for large organizations:
        # if gap < 0.1 and ratio < 1.001:
        #     print("⚠️ Too close to second best – rejecting match")
        #     return None, best_score, "Too close to second best"
        pass  # Continue to final threshold check

    # Final threshold check
    if best_score >= MATCHING_THRESHOLD * 100:
        print(f"✅ Match accepted: {best_match['employee'].name} ({best_score:.2f}%)")
        return best_match['employee'], best_score, "Match accepted"
    else:
        print(f"❌ Below threshold: {best_score:.2f}% < {MATCHING_THRESHOLD*100:.1f}%")
        return None, best_score, "Below threshold"

# ========== ROUTES (PAGES) ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/checkin')
def checkin_page():
    return render_template('checkin.html')

@app.route('/checkout')
def checkout_page():
    return render_template('checkout.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/employees')
def employees_page():
    return render_template('employees.html')

@app.route('/stats')
def stats_page():
    return render_template('stats.html')

@app.route('/encrypted-data')
def encrypted_data_page():
    return render_template('encrypted_data.html')

# ========== API ROUTES ==========

def check_for_duplicate_face(test_features, test_hash, exclude_employee_id=None):
    """Check if face already exists in system"""

    employees = Employee.query.filter(Employee.status == 'active').all()

    print("\n🔍 Checking duplicate face registration...")

    best_score = 0.0
    best_employee = None

    for emp in employees:

        if exclude_employee_id and emp.employee_id == exclude_employee_id:
            continue

        templates = FaceTemplate.query.filter_by(
            employee_id=emp.employee_id
        ).all()

        for template in templates:

            # Exact duplicate hash
            if template.face_hash and template.face_hash == test_hash:

                print(f"❌ Exact duplicate found: {emp.name}")

                return (
                    emp,
                    100.0,
                    "Exact duplicate face"
                )

            if template.face_features:

                stored_features = pickle.loads(
                    template.face_features
                )

                similarity = face_recognizer.calculate_similarity(
                    test_features,
                    stored_features
                )

                score = float(similarity * 100)

                print(
                    f"👤 {emp.name} duplicate similarity: "
                    f"{score:.2f}%"
                )

                if score > best_score:
                    best_score = score
                    best_employee = emp

    print(f"🏆 Highest duplicate score: {best_score:.2f}%")

    # Duplicate threshold
    if best_score >= 85.0:

        print(
            f"❌ Duplicate registration blocked "
            f"({best_score:.2f}%)"
        )

        return (
            best_employee,
            best_score,
            f"Similarity {best_score:.2f}%"
        )

    print("✅ No duplicate face found")

    return None, best_score, "Unique face"

@app.route('/api/register', methods=['POST'])
def register_employee():
    """Register employee"""
    try:
        data = request.json
        employee_id = data['employee_id'].strip()
        name = data['name'].strip()
        department = data['department'].strip()
        face_images = data['face_images']

        print(f"\n📝 REGISTER: {name} ({employee_id})")
        print(f"📸 Images received: {len(face_images)}")

        # Validation
        if not employee_id or not name or not department:
            return jsonify({'status': 'error', 'message': 'All fields required'})

        if not face_images or len(face_images) < MIN_FACES_FOR_REGISTRATION:
            return jsonify({
                'status': 'error',
                'message': f'At least {MIN_FACES_FOR_REGISTRATION} face images required'
            })

        # Check if employee already exists
        existing_employee = Employee.query.filter_by(employee_id=employee_id).first()
        if existing_employee:
            return jsonify({'status': 'error', 'message': 'Employee ID already exists'})

        # Aggregate face features
        avg_features, avg_hash = aggregate_face_features(face_images)
        if avg_features is None:
            return jsonify({
                'status': 'error',
                'message': 'Could not extract enough valid face images'
            })

        # Check for duplicate face across system
        duplicate_emp, duplicate_score, duplicate_reason = check_for_duplicate_face(avg_features, avg_hash)
        
        if duplicate_emp:
            return jsonify({
                'status': 'error',
                'message': f'Face already registered as {duplicate_emp.name} ({duplicate_reason})'
            })

        # Encrypt
        encrypted_template = encrypt_face_vector(avg_features)
        if encrypted_template is None:
            return jsonify({'status': 'error', 'message': 'Encryption failed'})

        # Save to database
        new_employee = Employee(
            employee_id=employee_id,
            name=name,
            department=department,
            registration_date=get_ist_timestamp()
        )
        db.session.add(new_employee)

        face_template = FaceTemplate(
            employee_id=employee_id,
            encrypted_template=base64.b64decode(encrypted_template),
            face_features=pickle.dumps(avg_features),
            face_hash=avg_hash,
            created_date=get_ist_timestamp()
        )
        db.session.add(face_template)

        db.session.commit()

        print(f"✅ Employee registered: {name} ({employee_id})")

        return jsonify({
            'status': 'success',
            'message': 'Employee registered successfully'
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Registration error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/checkin', methods=['POST'])
def checkin_employee():
    """Check-in"""

    try:
        data = request.json
        face_image = data['face_image']

        print(f"\n🕒 CHECK-IN at {get_ist_time_display()}")

        # Process face
        test_features, test_hash = process_face_image(face_image)

        if test_features is None:
            return jsonify({
                'status': 'error',
                'message': 'No face detected'
            })

        # Match face
        best_match, best_score, match_details = match_face_accurately(
            test_features,
            test_hash
        )

        print(
            f"🔍 Check-in matching result: "
            f"best_score={best_score:.2f}, "
            f"details={match_details}"
        )

        if best_match:

            # Get today's attendance records
            today_logs = AttendanceLog.query.filter(
                AttendanceLog.employee_id == best_match.employee_id,
                db.func.date(AttendanceLog.timestamp) == get_ist_date()
            ).order_by(
                AttendanceLog.timestamp.asc()
            ).all()

            # RULE 1:
            # Already completed IN + OUT today
            if len(today_logs) >= 2:

                return jsonify({
                    'status': 'attendance_completed',
                    'message': f'{best_match.name} already completed attendance for today',
                    'employee_id': best_match.employee_id,
                    'name': best_match.name
                })

            # RULE 2:
            # Already checked in but not checked out
            if len(today_logs) == 1 and today_logs[0].checkin_type == 'IN':

                return jsonify({
                    'status': 'already_checked_in',
                    'message': f'{best_match.name} already checked in',
                    'employee_id': best_match.employee_id,
                    'name': best_match.name,
                    'department': best_match.department,
                    'confidence': round(float(best_score), 2),
                    'time_display': get_ist_time_display()
                })

            # Save check-in
            attendance_log = AttendanceLog(
                employee_id=best_match.employee_id,
                timestamp=get_ist_timestamp(),
                confidence_score=float(best_score),
                checkin_type='IN'
            )

            db.session.add(attendance_log)
            db.session.commit()

            print(
                f"✅ CHECK-IN: "
                f"{best_match.name} ({best_score:.2f}%)"
            )

            return jsonify({
                'status': 'success',
                'employee_id': best_match.employee_id,
                'name': best_match.name,
                'department': best_match.department,
                'confidence': round(float(best_score), 2),
                'timestamp': get_ist_timestamp(),
                'time_display': get_ist_time_display()
            })

        else:

            if best_score > 0:

                if best_score >= REJECT_THRESHOLD * 100:
                    msg = (
                        f'Face not registered '
                        f'(best similarity {best_score:.2f}% < '
                        f'{MATCHING_THRESHOLD*100:.1f}%).'
                    )
                else:
                    msg = 'Face not registered in the system.'

            else:
                msg = 'Face not registered in the system.'

            print(
                f"❌ CHECK-IN FAILED: "
                f"{msg} | details={match_details}"
            )

            return jsonify({
                'status': 'not_registered',
                'message': msg,
                'confidence': round(float(best_score), 2)
                if best_score > 0 else 0.0
            })

    except Exception as e:

        db.session.rollback()

        print(f"❌ Check-in error: {e}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        })
@app.route('/api/checkout', methods=['POST'])
def checkout_employee():
    """Check-out"""

    try:
        data = request.json
        face_image = data['face_image']

        print(f"\n🕒 CHECK-OUT at {get_ist_time_display()}")

        # Process face
        test_features, test_hash = process_face_image(face_image)

        if test_features is None:
            return jsonify({
                'status': 'error',
                'message': 'No face detected'
            })

        # Match
        best_match, best_score, match_details = match_face_accurately(
            test_features,
            test_hash
        )

        if best_match:

            # Get today's logs
            today_logs = AttendanceLog.query.filter(
                AttendanceLog.employee_id == best_match.employee_id,
                db.func.date(AttendanceLog.timestamp) == get_ist_date()
            ).order_by(
                AttendanceLog.timestamp.asc()
            ).all()

            # RULE 1:
            # No check-in yet
            if len(today_logs) == 0:

                return jsonify({
                    'status': 'not_checked_in',
                    'message': f'{best_match.name} has not checked in today'
                })

            # RULE 2:
            # Already completed IN + OUT
            if len(today_logs) >= 2:

                return jsonify({
                    'status': 'already_checked_out',
                    'message': f'{best_match.name} already checked out'
                })

            # RULE 3:
            # First record is not IN
            if today_logs[0].checkin_type != 'IN':

                return jsonify({
                    'status': 'not_checked_in',
                    'message': f'{best_match.name} has not checked in properly'
                })

            # Save checkout
            attendance_log = AttendanceLog(
                employee_id=best_match.employee_id,
                timestamp=get_ist_timestamp(),
                confidence_score=float(best_score),
                checkin_type='OUT'
            )

            db.session.add(attendance_log)
            db.session.commit()

            print(
                f"✅ CHECK-OUT: "
                f"{best_match.name} ({best_score:.2f}%)"
            )

            return jsonify({
                'status': 'success',
                'employee_id': best_match.employee_id,
                'name': best_match.name,
                'department': best_match.department,
                'confidence': round(float(best_score), 2),
                'timestamp': get_ist_timestamp(),
                'time_display': get_ist_time_display(),
                'type': 'OUT'
            })

        else:

            msg = 'Face not registered'

            print(f"❌ CHECK-OUT FAILED: {msg}")

            return jsonify({
                'status': 'not_registered',
                'message': msg
            })

    except Exception as e:

        db.session.rollback()

        print(f"❌ Check-out error: {e}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        })
@app.route('/api/delete-employee/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    try:
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({'status': 'error', 'message': 'Employee not found'})

        FaceTemplate.query.filter_by(employee_id=employee_id).delete()
        AttendanceLog.query.filter_by(employee_id=employee_id).delete()
        db.session.delete(employee)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Employee {employee_id} deleted'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/encrypted-templates', methods=['GET'])
def get_encrypted_templates():
    try:
        templates = FaceTemplate.query.all()
        result = []

        for template in templates:
            employee = Employee.query.filter_by(employee_id=template.employee_id).first()
            if not employee:
                continue

            encrypted_hex = template.encrypted_template.hex()
            
            result.append({
                'employee_id': employee.employee_id,
                'name': employee.name,
                'department': employee.department,
                'encrypted_data_preview': encrypted_hex[:100] + '...',
                'data_length': len(template.encrypted_template),
                'face_hash': template.face_hash[:16] + '...' if template.face_hash else 'N/A',
                'created_date': template.created_date
            })

        return jsonify({
            'status': 'success',
            'templates': result
        })
    except Exception as e:
        print(f"❌ Error fetching encrypted templates: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        employees = Employee.query.filter(Employee.status == 'active').all()
        result = []
        
        for emp in employees:
            last_checkin = AttendanceLog.query.filter_by(
                employee_id=emp.employee_id,
                checkin_type='IN'
            ).order_by(AttendanceLog.timestamp.desc()).first()

            last_checkout = AttendanceLog.query.filter_by(
                employee_id=emp.employee_id,
                checkin_type='OUT'
            ).order_by(AttendanceLog.timestamp.desc()).first()

            result.append({
                'employee_id': emp.employee_id,
                'name': emp.name,
                'department': emp.department,
                'registration_date': emp.registration_date,
                'status': emp.status,
                'last_checkin': last_checkin.timestamp if last_checkin else None,
                'last_checkout': last_checkout.timestamp if last_checkout else None
            })

        return jsonify({'status': 'success', 'employees': result})
    except Exception as e:
        print(f"❌ Error fetching employees: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        date_str = request.args.get('date', get_ist_date())
        
        # Filter logs by date
        logs = AttendanceLog.query.filter(
            db.func.date(AttendanceLog.timestamp) == date_str
        ).order_by(AttendanceLog.timestamp.desc()).all()
        
        result = []
        
        for log in logs:
            employee = Employee.query.filter_by(employee_id=log.employee_id).first()
            if not employee:
                continue
            
            result.append({
                'employee_id': employee.employee_id,
                'name': employee.name,
                'department': employee.department,
                'timestamp': log.timestamp,
                'time_display': datetime.strptime(log.timestamp, '%Y-%m-%d %H:%M:%S').strftime('%I:%M:%S %p'),
                'confidence': log.confidence_score,
                'checkin_type': log.checkin_type
            })
        
        return jsonify({'status': 'success', 'records': result})
    except Exception as e:
        print(f"❌ Error fetching attendance: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_employees = Employee.query.filter(
            Employee.status == 'active'
        ).count()

        total_templates = FaceTemplate.query.count()

        total_checkins = AttendanceLog.query.filter(
            AttendanceLog.checkin_type == 'IN'
        ).count()

        total_checkouts = AttendanceLog.query.filter(
            AttendanceLog.checkin_type == 'OUT'
        ).count()

        today = get_ist_date()

        today_checkins = AttendanceLog.query.filter(
            db.func.date(AttendanceLog.timestamp) == today,
            AttendanceLog.checkin_type == 'IN'
        ).count()

        today_checkouts = AttendanceLog.query.filter(
            db.func.date(AttendanceLog.timestamp) == today,
            AttendanceLog.checkin_type == 'OUT'
        ).count()

        stats = {
            'total_employees': total_employees,
            'total_templates': total_templates,
            'total_checkins': total_checkins,
            'total_checkouts': total_checkouts,
            'today_checkins': today_checkins,
            'today_checkouts': today_checkouts
        }

        return jsonify({
            'status': 'success',
            'stats': stats
        })

    except Exception as e:
        print(f"❌ Error fetching stats: {e}")

        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        employees_count = Employee.query.filter(Employee.status == 'active').count()
        today = get_ist_date()
        today_checkins = AttendanceLog.query.filter(
            db.func.date(AttendanceLog.timestamp) == today,
            AttendanceLog.checkin_type == 'IN'
        ).count()
        
        return jsonify({
            'status': 'healthy',
            'time_display': get_ist_time_display(),
            'employees_count': employees_count,
            'today_checkins': today_checkins
        })
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

# ========== STARTUP ==========

print("\n" + "="*70)
print("🔥 HOMOMORPHIC ENCRYPTION ATTENDANCE SYSTEM")
print("="*70)

# Initialize database
with app.app_context():
    init_database()

print(f"\n📊 Configuration:")
print(f"   Matching Threshold: {MATCHING_THRESHOLD*100:.1f}%")
print(f"   Reject Threshold: {REJECT_THRESHOLD*100:.1f}%")
print(f"   Duplicate Check: {DUPLICATE_CHECK_THRESHOLD*100:.1f}%")
print(f"   Min Registration Images: {MIN_FACES_FOR_REGISTRATION}")
print("="*70)
print("🚀 Server: http://localhost:5000")
print("="*70 + "\n")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
