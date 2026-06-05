# test_reset.py - Test if database reset works
import os
import sqlite3

def test_reset():
    """Test if database is properly reset"""
    db_file = 'attendance_system.db'
    
    print("🧪 TESTING DATABASE RESET")
    print("="*40)
    
    # Check if file exists
    if os.path.exists(db_file):
        print(f"❌ FAIL: Database file still exists at: {os.path.abspath(db_file)}")
        print(f"   Size: {os.path.getsize(db_file)} bytes")
        
        # Try to connect and check contents
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check for employees table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
            if cursor.fetchone():
                print("   ⚠️ Employees table still exists!")
                
                cursor.execute("SELECT COUNT(*) FROM employees")
                count = cursor.fetchone()[0]
                print(f"   ⚠️ Still has {count} employees!")
            
            conn.close()
            
        except Exception as e:
            print(f"   Error reading: {e}")
            
    else:
        print("✅ PASS: Database file deleted successfully")
    
    print("="*40)
    
    # Check current directory contents
    print("\n📁 Current directory contents:")
    for file in os.listdir('.'):
        if 'attendance_system' in file or '.db' in file:
            print(f"   {file}")

if __name__ == '__main__':
    test_reset()