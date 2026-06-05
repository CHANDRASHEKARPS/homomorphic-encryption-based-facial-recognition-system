import tenseal as ts
import base64
import numpy as np

class EncryptionManager:
    def __init__(self):
        self.context = self.create_context()
        
    def create_context(self):
        """Create identical encryption context for both client and server"""
        context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[40, 21, 21, 21, 21, 21, 21, 40]
        )
        context.generate_galois_keys()
        context.global_scale = 2**21
        return context
    
    def encrypt_vector(self, vector):
        """Encrypt face vector"""
        try:
            if len(vector) != 256:  # Ensure consistent vector size
                # Pad or truncate to 256
                if len(vector) > 256:
                    vector = vector[:256]
                else:
                    padding = 256 - len(vector)
                    vector = np.pad(vector, (0, padding), 'constant', constant_values=0.5)
            
            encrypted = ts.ckks_vector(self.context, vector)
            serialized = encrypted.serialize()
            encoded = base64.b64encode(serialized).decode('utf-8')
            return encoded
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return None
    
    def decrypt_vector(self, encrypted_data_b64):
        """Decrypt face data"""
        try:
            encrypted_data = base64.b64decode(encrypted_data_b64)
            encrypted_vector = ts.ckks_vector_from(self.context, encrypted_data)
            return encrypted_vector
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return None
    
    def calculate_encrypted_similarity(self, encrypted_vec1, encrypted_vec2):
        """Calculate similarity between two encrypted vectors"""
        try:
            # Compute dot product in encrypted space
            dot_product = encrypted_vec1.dot(encrypted_vec2)
            
            # Compute norms (encrypted)
            norm1_sq = encrypted_vec1.dot(encrypted_vec1)
            norm2_sq = encrypted_vec2.dot(encrypted_vec2)
            
            # Decrypt the results
            dot_product_decrypted = dot_product.decrypt()[0]
            norm1_decrypted = np.sqrt(norm1_sq.decrypt()[0])
            norm2_decrypted = np.sqrt(norm2_sq.decrypt()[0])
            
            if norm1_decrypted == 0 or norm2_decrypted == 0:
                return 0.0
            
            similarity = dot_product_decrypted / (norm1_decrypted * norm2_decrypted)
            
            # Ensure valid range
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            print(f"❌ Encrypted similarity calculation error: {e}")
            return 0.0
    
    def get_plaintext_comparator(self, reference_vector):
        """Create a comparator for plaintext matching (for threshold verification)"""
        class PlaintextComparator:
            def __init__(self, ref_vector):
                self.reference = ref_vector
            
            def compare(self, test_vector):
                """Compare with reference vector"""
                if len(test_vector) != len(self.reference):
                    return 0.0
                
                # Cosine similarity
                dot = np.dot(test_vector, self.reference)
                norm_test = np.linalg.norm(test_vector)
                norm_ref = np.linalg.norm(self.reference)
                
                if norm_test == 0 or norm_ref == 0:
                    return 0.0
                
                return dot / (norm_test * norm_ref)
        
        return PlaintextComparator(reference_vector)

# Global encryption manager
encryption_manager = EncryptionManager()