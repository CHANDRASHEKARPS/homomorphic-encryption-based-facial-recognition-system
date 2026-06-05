# verify_reset.py - Verify database reset worked
import os
import sqlite3
import sys

def verify_database_reset():
    """Verify database is truly empty"""
    print("\n" + "="*60)
    print("🔍 DATABASE VERIFICATION TOOL")
    print("="*60)
    
    db_file = 'attendance_system.db'
    
    if not os.path.exists(db_file):
        print(f"❌ Database file '{db_file}' does not exist!")
        print("   Run 'python app.py' first to create it.")
        print("="*60)
        return False
    
    print(f"📊 Checking database: {db_file}")
    print(f"📏 File size: {os.path.getsize(db_file)} bytes")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Found {len(tables)} tables:")
        
        total_records = 0
        has_data = False
        
        for table_name, in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            print(f"   📊 {table_name}: {count} records")
            
            if count > 0:
                has_data = True
                total_records += count
                
                # Show sample data
                if table_name == 'employees':
                    cursor.execute(f"SELECT employee_id, name FROM {table_name} LIMIT 3")
                    records = cursor.fetchall()
                    if records:
                        print(f"      Sample employees:")
                        for emp_id, name in records:
                            print(f"        • {name} ({emp_id})")
        
        conn.close()
        
        print(f"\n📈 TOTAL RECORDS: {total_records}")
        
        if total_records == 0:
            print("✅ VERIFICATION PASSED: Database is completely empty!")
            print("🎉 You can now register new employees")
            print("="*60)
            return True
        else:
            print(f"❌ VERIFICATION FAILED: Database has {total_records} records!")
            print("⚠️  The database was NOT properly reset")
            print("\n💡 Run 'python reset_db.py' again to COMPLETELY reset")
            print("="*60)
            return False
            
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        print("="*60)
        return False

if __name__ == '__main__':
    success = verify_database_reset()
    sys.exit(0 if success else 1)