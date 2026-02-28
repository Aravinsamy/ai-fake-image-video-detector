import sqlite3
import os

def view_database():
    """View users and analysis history from the AI Detector database"""

    # Always point to backend/aidetector.db
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "aidetector.db")

    if not os.path.exists(db_path):
        print("❌ Database not found at:", db_path)
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("👤 USERS TABLE")
    print("=" * 100)

    try:
        cursor.execute("""
            SELECT id, name, email, created_at
            FROM users
            ORDER BY id DESC
        """)
        users = cursor.fetchall()

        if not users:
            print("No users found.")
        else:
            print(f"{'ID':<5} {'Name':<20} {'Email':<30} {'Created At'}")
            print("-" * 100)
            for u in users:
                print(
                    f"{u['id']:<5} "
                    f"{u['name']:<20} "
                    f"{u['email']:<30} "
                    f"{u['created_at']}"
                )
    except sqlite3.Error as e:
        print("❌ Users table error:", e)

    print("\n" + "=" * 100)
    print("📊 ANALYSIS HISTORY")
    print("=" * 100)

    try:
        cursor.execute("""
            SELECT 
                id,
                user_id,
                file_name,
                file_type,
                verdict,
                confidence,
                timestamp
            FROM analysis_history
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()

        if not rows:
            print("No analysis records found.")
        else:
            print(
                f"{'ID':<5} {'User':<6} {'File':<28} "
                f"{'Type':<10} {'Verdict':<22} {'Conf%':<7} {'Date'}"
            )
            print("-" * 100)

            for r in rows:
                print(
                    f"{r['id']:<5} "
                    f"{r['user_id']:<6} "
                    f"{r['file_name'][:26]:<28} "
                    f"{(r['file_type'] or '-'):<10} "
                    f"{r['verdict']:<22} "
                    f"{r['confidence']:<7.1f} "
                    f"{r['timestamp']}"
                )

            print("\nTotal Analyses:", len(rows))

    except sqlite3.Error as e:
        print("❌ Analysis history error:", e)

    finally:
        conn.close()
        print("=" * 100 + "\n")


if __name__ == "__main__":
    view_database()
