# reset_db.py - COMPLETE DATABASE DESTROYER
import os
import sys
import time
import sqlite3
import shutil
import subprocess

def kill_all_python_processes():
    """Kill ALL Python processes to release database locks"""
    print("🛑 Killing all Python processes...")
    
    if os.name == 'nt':  # Windows
        commands = [
            'taskkill /f /im python.exe /t',
            'taskkill /f /im pythonw.exe /t',
            'taskkill /f /im flask.exe /t'
        ]
    else:  # Linux/Mac
        commands = [
            'pkill -9 -f python',
            'pkill -9 -f flask',
            'pkill -9 -f "app.py"'
        ]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, capture_output=True)
            time.sleep(1)
        except:
            pass

def force_delete_file(file_path):
    """Force delete a file using multiple methods"""
    if not os.path.exists(file_path):
        return True
    
    print(f"  Deleting {os.path.basename(file_path)}...")
    
    methods = [
        # Method 1: Normal delete
        lambda: os.remove(file_path),
        
        # Method 2: Rename and delete
        lambda: (os.rename(file_path, file_path + '.old') and 
                os.remove(file_path + '.old') if os.path.exists(file_path + '.old') else True),
        
        # Method 3: System command
        lambda: (os.system(f'del /f "{file_path}"' if os.name == 'nt' else f'rm -f "{file_path}"') == 0),
        
        # Method 4: Change permissions and delete
        lambda: (os.chmod(file_path, 0o777) and os.remove(file_path)),
    ]
    
    for i, method in enumerate(methods):
        try:
            result = method()
            time.sleep(0.5)
            
            if not os.path.exists(file_path):
                print(f"    ✅ Method {i+1} succeeded")
                return True
            else:
                print(f"    ⚠️ Method {i+1} failed - file still exists")
                
        except Exception as e:
            print(f"    ❌ Method {i+1} error: {e}")
            continue
    
    return False

def reset_database_completely():
    """COMPLETELY reset the database - NO MERCY VERSION"""
    print("\n" + "="*70)
    print("🔥 COMPLETE DATABASE DESTROYER")
    print("="*70)
    
    # Database files to delete
    db_files = [
        'attendance_system.db',
        'attendance_system.db-journal',
        'attendance_system.db-wal',
        'attendance_system.db-shm',
        'attendance_system_backup.db',
        'test.db'
    ]
    
    # Step 1: Kill all Python processes
    kill_all_python_processes()
    time.sleep(3)
    
    # Step 2: Check current state
    print("\n📊 Checking current database state...")
    
    if os.path.exists('attendance_system.db'):
        try:
            conn = sqlite3.connect('attendance_system.db')
            cursor = conn.cursor()
            
            # Try to get employee count
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM employees")
                    emp_count = cursor.fetchone()[0]
                    print(f"   👥 Found {emp_count} employees in database")
                    
                    cursor.execute("SELECT employee_id, name FROM employees LIMIT 5")
                    employees = cursor.fetchall()
                    if employees:
                        print("   📋 Sample employees:")
                        for emp_id, name in employees:
                            print(f"      • {name} ({emp_id})")
                else:
                    print("   ℹ️ No employees table found")
                    emp_count = 0
            except:
                print("   ⚠️ Could not read employees table")
                emp_count = "unknown"
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Could not connect to database: {e}")
            emp_count = "corrupted"
    else:
        print("   ℹ️ No database file found")
        emp_count = 0
    
    # Step 3: Get confirmation
    print(f"\n⚠️  WARNING: This will DESTROY ALL DATA")
    print(f"   {emp_count} employees will be PERMANENTLY deleted")
    
    response = input("\n❓ Type 'DESTROY' to continue (or anything else to cancel): ")
    
    if response.strip().upper() != 'DESTROY':
        print("\n🚫 Operation cancelled by user.")
        print("="*70)
        return
    
    # Step 4: Delete ALL database files
    print("\n🗑️  Deleting ALL database files...")
    
    deleted_count = 0
    failed_files = []
    
    for db_file in db_files:
        if os.path.exists(db_file):
            if force_delete_file(db_file):
                deleted_count += 1
            else:
                failed_files.append(db_file)
                print(f"   ❌ FAILED to delete: {db_file}")
        else:
            print(f"   ℹ️ {db_file} not found - skipping")
    
    # Step 5: Verify deletion
    print("\n🔍 Verifying deletion...")
    
    still_exist = []
    for db_file in db_files:
        if os.path.exists(db_file):
            still_exist.append(db_file)
    
    if still_exist:
        print(f"❌ FAILED: {len(still_exist)} files still exist:")
        for file in still_exist:
            print(f"   • {file}")
        
        print("\n💡 MANUAL FIX REQUIRED:")
        print("   1. Close ALL programs (VS Code, terminals, browsers)")
        print("   2. Open Task Manager (Ctrl+Shift+Esc)")
        print("   3. End ALL Python processes")
        print("   4. Manually delete these files from File Explorer:")
        for file in still_exist:
            print(f"      - {os.path.abspath(file)}")
        print("="*70)
        
        # Try manual deletion prompt
        if os.name == 'nt':
            input("\n📋 Press Enter to try opening File Explorer to the folder...")
            os.system(f'explorer /select,"{os.path.abspath(".")}"')
        
        sys.exit(1)
    
    print(f"✅ SUCCESS: Deleted {deleted_count} database files")
    
    # Step 6: Create fresh empty database
    print("\n🔄 Creating fresh empty database...")
    try:
        # Create a completely new database
        conn = sqlite3.connect('attendance_system.db')
        
        # Create basic schema
        conn.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                registration_date TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS face_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                encrypted_template BLOB NOT NULL,
                face_features BLOB,
                face_hash TEXT,
                created_date TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS attendance_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                checkin_type TEXT DEFAULT 'IN',
                timezone TEXT DEFAULT 'Asia/Kolkata',
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Fresh database created with empty tables")
        
    except Exception as e:
        print(f"❌ Error creating fresh database: {e}")
        # Still continue - app.py will create the tables
    
    # Step 7: Final verification
    print("\n🔍 Final verification...")
    
    if os.path.exists('attendance_system.db'):
        try:
            conn = sqlite3.connect('attendance_system.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM employees")
            final_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM face_templates")
            template_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"✅ Database reset COMPLETE")
            print(f"   👥 Employees in new database: {final_count}")
            print(f"   📸 Face templates: {template_count}")
            
            if final_count == 0 and template_count == 0:
                print("🎉 SUCCESS: Database is completely empty!")
            else:
                print("⚠️  WARNING: Database is not empty!")
                
        except Exception as e:
            print(f"❌ Verification error: {e}")
    else:
        print("❌ Database file was not created")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Run: python app.py")
    print("   2. Register employees from scratch")
    print("   3. Test face recognition")
    print("="*70)

def main():
    """Main function"""
    try:
        # Check if we're in the right directory
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📁 Directory contents:")
        for file in os.listdir('.'):
            if '.db' in file or '.py' in file:
                print(f"   {file}")
        
        reset_database_completely()
        
    except KeyboardInterrupt:
        print("\n\n🚫 Operation cancelled by user")
        print("="*70)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        print("\n💡 MANUAL SOLUTION:")
        print("   1. Close ALL programs")
        print("   2. Navigate to your project folder")
        print("   3. Delete ALL files ending with .db")
        print("   4. Run 'python app.py'")
        print("="*70)

if __name__ == '__main__':
    main()