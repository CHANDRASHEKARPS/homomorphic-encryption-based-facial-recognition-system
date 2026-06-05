import cv2
import numpy as np
import base64
from PIL import Image
import io

class FaceProcessor:
    def __init__(self):
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            # Load face recognition model (using LBPH as it's simple and effective)
            self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.face_recognizer.setThreshold(100)  # Higher threshold = more strict
            
            # For face alignment
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            
            print("✅ Face processors loaded successfully")
        except Exception as e:
            print(f"❌ Error loading face processors: {e}")
            self.face_cascade = None
            self.face_recognizer = None

    def base64_to_image(self, base64_string):
        """Convert base64 string to OpenCV image"""
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Ensure image is in correct format
            if opencv_image is None or opencv_image.size == 0:
                print("❌ Invalid image data")
                return None
                
            print(f"✅ Base64 to image conversion successful: {opencv_image.shape}")
            return opencv_image
        except Exception as e:
            print(f"❌ Error converting base64 to image: {e}")
            return None

    def detect_and_align_face(self, image):
        """Detect face and align it for better feature extraction"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )
            
            if len(faces) == 0:
                print("❌ No face detected")
                return None
            
            # Use the largest face
            faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
            x, y, w, h = faces[0]
            
            # Extract face region
            face_region = gray[y:y+h, x:x+w]
            
            # Resize to standard size for consistency
            face_resized = cv2.resize(face_region, (150, 150))
            
            # Apply histogram equalization for better contrast
            face_equalized = cv2.equalizeHist(face_resized)
            
            # Apply Gaussian blur to reduce noise
            face_processed = cv2.GaussianBlur(face_equalized, (5, 5), 0)
            
            return face_processed
            
        except Exception as e:
            print(f"❌ Face detection/alignment error: {e}")
            return None

    def extract_robust_features(self, face_image):
        """Extract robust facial features using multiple techniques"""
        try:
            if face_image is None:
                return None
            
            # 1. LBP features (Local Binary Patterns) - good for texture
            radius = 2
            n_points = 8 * radius
            lbp = cv2.face.createLBPHFaceRecognizer().getHistograms([face_image])[0]
            
            # 2. HOG features (Histogram of Oriented Gradients)
            hog = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8), 9)
            hog_features = hog.compute(cv2.resize(face_image, (64, 64))).flatten()
            
            # 3. Haar-like features (simplified)
            integral_image = cv2.integral(face_image)
            haar_features = self.extract_haar_features(integral_image)
            
            # 4. Edge features
            edges = cv2.Canny(face_image, 50, 150)
            edge_features = edges.flatten() / 255.0
            
            # Combine all features
            combined_features = []
            
            # Normalize and add LBP features
            if lbp is not None and len(lbp) > 0:
                lbp_normalized = lbp / (np.sum(lbp) + 1e-6)
                combined_features.extend(lbp_normalized[:128])  # Take first 128
            
            # Normalize and add HOG features
            if len(hog_features) > 0:
                hog_normalized = hog_features / (np.linalg.norm(hog_features) + 1e-6)
                combined_features.extend(hog_normalized[:256])  # Take first 256
            
            # Add Haar features
            combined_features.extend(haar_features[:64])
            
            # Add edge features
            combined_features.extend(edge_features[:128])
            
            # Convert to numpy array
            feature_vector = np.array(combined_features, dtype=np.float32)
            
            # Ensure minimum length
            if len(feature_vector) < 128:
                padding = 128 - len(feature_vector)
                feature_vector = np.pad(feature_vector, (0, padding), 'constant', constant_values=0.5)
            elif len(feature_vector) > 512:
                feature_vector = feature_vector[:512]
            
            # Normalize the feature vector
            norm = np.linalg.norm(feature_vector)
            if norm > 0:
                feature_vector = feature_vector / norm
            
            print(f"✅ Extracted {len(feature_vector)} facial features")
            return feature_vector
            
        except Exception as e:
            print(f"❌ Feature extraction error: {e}")
            # Return a neutral feature vector as fallback
            fallback_vector = np.ones(256) * 0.5
            norm = np.linalg.norm(fallback_vector)
            return fallback_vector / norm

    def extract_haar_features(self, integral_img):
        """Extract simplified Haar-like features"""
        try:
            h, w = integral_img.shape
            features = []
            
            # Simple rectangle features at different positions and scales
            for scale in [2, 4, 8]:
                for y in range(0, h - scale, scale):
                    for x in range(0, w - scale, scale):
                        # Horizontal two-rectangle feature
                        if x + 2*scale < w:
                            left_sum = self.rectangle_sum(integral_img, x, y, scale, scale)
                            right_sum = self.rectangle_sum(integral_img, x + scale, y, scale, scale)
                            features.append(left_sum - right_sum)
                        
                        # Vertical two-rectangle feature
                        if y + 2*scale < h:
                            top_sum = self.rectangle_sum(integral_img, x, y, scale, scale)
                            bottom_sum = self.rectangle_sum(integral_img, x, y + scale, scale, scale)
                            features.append(top_sum - bottom_sum)
            
            # Normalize features
            if len(features) > 0:
                features = np.array(features, dtype=np.float32)
                features = features / (np.max(np.abs(features)) + 1e-6)
            
            return features[:64]  # Limit to 64 features
            
        except Exception as e:
            print(f"❌ Haar feature extraction error: {e}")
            return np.zeros(64)

    def rectangle_sum(self, integral_img, x, y, w, h):
        """Calculate sum of rectangle using integral image"""
        A = integral_img[y, x]
        B = integral_img[y, x + w]
        C = integral_img[y + h, x]
        D = integral_img[y + h, x + w]
        return D - B - C + A

    def calculate_similarity(self, vec1, vec2):
        """Calculate robust similarity score between feature vectors"""
        if vec1 is None or vec2 is None:
            return 0.0
        
        # Ensure vectors are same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        # Cosine similarity (more robust for face recognition)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = dot_product / (norm1 * norm2)
        
        # Euclidean distance (normalized)
        euclidean_dist = np.linalg.norm(vec1 - vec2)
        euclidean_sim = 1.0 / (1.0 + euclidean_dist)
        
        # Combined score (weighted average)
        combined_score = 0.7 * cosine_sim + 0.3 * euclidean_sim
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, combined_score))

    def process_face_for_matching(self, base64_image):
        """Complete pipeline for face processing"""
        try:
            # Convert base64 to image
            image = self.base64_to_image(base64_image)
            if image is None:
                return None
            
            # Detect and align face
            aligned_face = self.detect_and_align_face(image)
            if aligned_face is None:
                return None
            
            # Extract features
            features = self.extract_robust_features(aligned_face)
            
            return features
            
        except Exception as e:
            print(f"❌ Face processing error: {e}")
            return None