import cv2
import numpy as np
import face_recognition
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# -----------------------------
# Setup paths and DB
# -----------------------------
faces_dir = "faces"
csv_file = "Attendance.csv"
db_file = "attendance.db"

if not os.path.exists(faces_dir):
    os.makedirs(faces_dir)

conn = sqlite3.connect(db_file)
c = conn.cursor()

# Create attendance table
c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                time TEXT NOT NULL,
                date TEXT NOT NULL
            )''')

# Create work_hours table to track hours worked per day per employee
c.execute('''CREATE TABLE IF NOT EXISTS work_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                hours REAL NOT NULL
            )''')

# Create employees table to store employee info and role-based salary
c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                position TEXT NOT NULL,
                base_salary REAL NOT NULL
            )''')

conn.commit()

# -----------------------------
# Role base salaries
# -----------------------------
ROLE_BASE_SALARY = {
    "tinker": 20000,
    "car internal worker": 25000,
    "car external worker": 27000,
    "manager": 45000,
    "accountant": 40000,
}

# -----------------------------
# Helper Functions for Employees
# -----------------------------
def add_employee():
    name = input("Enter employee name: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty.")
        return
    print("Available positions:")
    for role in ROLE_BASE_SALARY:
        print(f"- {role}")
    position = input("Enter position from above list: ").strip().lower()
    if position not in ROLE_BASE_SALARY:
        print("[ERROR] Invalid position.")
        return
    base_salary = ROLE_BASE_SALARY[position]

    # Insert employee
    try:
        c.execute("INSERT INTO employees (name, position, base_salary) VALUES (?, ?, ?)", (name, position, base_salary))
        conn.commit()
        print(f"[INFO] Added employee {name} with position '{position}' and base salary ₹{base_salary}.")
    except sqlite3.IntegrityError:
        print(f"[ERROR] Employee '{name}' already exists.")

def view_employees():
    c.execute("SELECT name, position, base_salary FROM employees ORDER BY name")
    rows = c.fetchall()
    if not rows:
        print("[INFO] No employees found.")
    else:
        print("\n--- Employees ---")
        for row in rows:
            print(f"Name: {row[0]}, Position: {row[1]}, Base Salary: ₹{row[2]}")
        print("-----------------\n")

def get_base_salary(name):
    c.execute("SELECT base_salary FROM employees WHERE name = ?", (name,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        # Default salary if employee not found in employees table
        return 30000

# -----------------------------
# Load known faces
# -----------------------------
def load_known_faces():
    known_face_encodings = []
    known_face_names = []

    print("[INFO] Loading known faces...")
    for filename in os.listdir(faces_dir):
        if filename.endswith((".jpg", ".png", ".jpeg")):
            path = os.path.join(faces_dir, filename)
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)

            if encoding:
                known_face_encodings.append(encoding[0])
                known_face_names.append(os.path.splitext(filename)[0])
            else:
                print(f"[WARNING] No face found in {filename}")
    print(f"[INFO] Loaded {len(known_face_names)} faces.")
    return known_face_encodings, known_face_names

# -----------------------------
# Mark attendance
# -----------------------------
def mark_attendance(name):
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")

    c.execute("SELECT 1 FROM attendance WHERE name = ? AND date = ?", (name, date_str))
    exists = c.fetchone()

    if not exists:
        c.execute("INSERT INTO attendance (name, time, date) VALUES (?, ?, ?)", (name, time_str, date_str))
        conn.commit()

        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
        else:
            df = pd.DataFrame(columns=["Name", "Time", "Date"])

        new_entry = pd.DataFrame([[name, time_str, date_str]], columns=["Name", "Time", "Date"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(csv_file, index=False)

        print(f"[INFO] Marked attendance for {name} at {time_str} on {date_str}")

# -----------------------------
# Capture and save a new face
# -----------------------------
def add_new_face():
    name = input("Enter the name of the person: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty.")
        return
    # Ensure employee exists for this face
    c.execute("SELECT 1 FROM employees WHERE name = ?", (name,))
    if not c.fetchone():
        print(f"[ERROR] Employee '{name}' not found in employee records. Please add employee first (Option 6).")
        return

    cap = cv2.VideoCapture(0)
    print("[INFO] Capturing face. Press 's' to save, 'q' to quit without saving.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Add New Face", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            img_path = os.path.join(faces_dir, f"{name}.jpg")
            cv2.imwrite(img_path, frame)
            print(f"[INFO] Saved new face for {name} at {img_path}")
            break
        elif key == ord('q'):
            print("[INFO] Cancelled face capture.")
            break

    cap.release()
    cv2.destroyAllWindows()

# -----------------------------
# Start attendance detection
# -----------------------------
def start_attendance():
    known_face_encodings, known_face_names = load_known_faces()
    if not known_face_names:
        print("[ERROR] No known faces found. Please add faces first.")
        return
    cap = cv2.VideoCapture(0)
    print("[INFO] Starting camera... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches and matches[best_match_index]:
                name = known_face_names[best_match_index]
                mark_attendance(name)

            top, right, bottom, left = [v * 4 for v in face_location]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow('Attendance', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# -----------------------------
# View attendance records
# -----------------------------
def view_attendance():
    c.execute("SELECT * FROM attendance ORDER BY date, time")
    rows = c.fetchall()
    if not rows:
        print("[INFO] No attendance records found.")
    else:
        print("\n--- Attendance Records ---")
        for row in rows:
            print(row)
        print("--------------------------\n")

# -----------------------------
# Export attendance
# -----------------------------
def export_attendance():
    df = pd.read_sql_query("SELECT * FROM attendance", conn)
    export_path = "exports"
    os.makedirs(export_path, exist_ok=True)
    file_path = os.path.join(export_path, "attendance_export.csv")
    df.to_csv(file_path, index=False)
    print(f"[INFO] Attendance exported to {file_path}")

# -----------------------------
# Delete all attendance
# -----------------------------
def delete_attendance():
    confirm = input("Are you sure you want to delete all attendance records? (y/n): ")
    if confirm.lower() == 'y':
        c.execute("DELETE FROM attendance")
        conn.commit()
        print("[INFO] All attendance records deleted.")
    else:
        print("[INFO] Deletion cancelled.")

# -----------------------------
# Add daily work hours for an employee
# -----------------------------
def add_work_hours():
    name = input("Enter employee name: ").strip()
    c.execute("SELECT 1 FROM employees WHERE name = ?", (name,))
    if not c.fetchone():
        print(f"[ERROR] Employee '{name}' does not exist. Please add employee first.")
        return

    date_str = input("Enter date (YYYY-MM-DD), leave empty for today: ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("[ERROR] Invalid date format.")
        return
    try:
        hours = float(input("Enter hours worked on this day: "))
        if hours < 0:
            print("[ERROR] Hours cannot be negative.")
            return
    except ValueError:
        print("[ERROR] Invalid number for hours.")
        return

    # Check if record exists for the day, update if yes
    c.execute("SELECT id FROM work_hours WHERE name = ? AND date = ?", (name, date_str))
    row = c.fetchone()
    if row:
        c.execute("UPDATE work_hours SET hours = ? WHERE id = ?", (hours, row[0]))
        print(f"[INFO] Updated work hours for {name} on {date_str} to {hours} hours.")
    else:
        c.execute("INSERT INTO work_hours (name, date, hours) VALUES (?, ?, ?)", (name, date_str, hours))
        print(f"[INFO] Added work hours for {name} on {date_str}: {hours} hours.")
    conn.commit()

# -----------------------------
# Calculate attendance analytics & salary report for a given month
# -----------------------------
def attendance_analytics():
    deduction_per_absent_day = 200
    increment_per_extra_hour_day = 200  # If hours worked > 8, increment per day

    month_input = input("Enter month and year to analyze (YYYY-MM), leave empty for current month: ").strip()
    if not month_input:
        month_input = datetime.now().strftime("%Y-%m")
    try:
        datetime.strptime(month_input + "-01", "%Y-%m-%d")
    except ValueError:
        print("[ERROR] Invalid month format.")
        return

    print(f"\n[INFO] Generating attendance and salary report for {month_input}")

    # Calculate first and last day of the month
    year, month = map(int, month_input.split('-'))
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    # Get distinct employees from employees table
    c.execute("SELECT name FROM employees")
    employees = [row[0] for row in c.fetchall()]
    if not employees:
        print("[INFO] No employees found in records.")
        return

    total_days_in_month = (last_day - first_day).days + 1

    report = []

    for employee in employees:
        # Get base salary for employee from employees table
        base_salary_per_month = get_base_salary(employee)

        # Count days attended (attendance records in the month)
        c.execute(
            "SELECT COUNT(DISTINCT date) FROM attendance WHERE name = ? AND date BETWEEN ? AND ?",
            (employee, first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
        )
        attended_days = c.fetchone()[0] or 0

        absent_days = total_days_in_month - attended_days

        # Get days with >8 hours worked
        c.execute(
            "SELECT COUNT(DISTINCT date) FROM work_hours WHERE name = ? AND date BETWEEN ? AND ? AND hours > 8",
            (employee, first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
        )
        extra_hour_days = c.fetchone()[0] or 0

        # Calculate salary adjustments
        deduction = absent_days * deduction_per_absent_day
        increment = extra_hour_days * increment_per_extra_hour_day
        final_salary = base_salary_per_month - deduction + increment

        attendance_percentage = (attended_days / total_days_in_month) * 100

        report.append({
            "Employee": employee,
            "Days Attended": attended_days,
            "Absent Days": absent_days,
            "Extra Hour Days": extra_hour_days,
            "Attendance %": f"{attendance_percentage:.2f}%",
            "Base Salary": f"₹{base_salary_per_month}",
            "Salary Deduction": f"-₹{deduction}",
            "Salary Increment": f"+₹{increment}",
            "Final Salary": f"₹{final_salary}"
        })

    df_report = pd.DataFrame(report)
    print("\n--- Monthly Attendance & Salary Report ---")
    print(df_report.to_string(index=False))

    # Optional: save to CSV
    save_csv = input("Save report as CSV? (y/n): ").strip().lower()
    if save_csv == 'y':
        export_path = "exports"
        os.makedirs(export_path, exist_ok=True)
        file_path = os.path.join(export_path, f"salary_report_{month_input}.csv")
        df_report.to_csv(file_path, index=False)
        print(f"[INFO] Report saved to {file_path}")

# -----------------------------
# Main menu with all options
# -----------------------------
def main_menu():
    while True:
        print("\n--- Smart Attendance System ---")
        print("1. Add New Face")
        print("2. Start Attendance Detection")
        print("3. View Attendance Records")
        print("4. Export Attendance to CSV")
        print("5. Delete All Attendance Records")
        print("6. Add Employee (Name + Position)")
        print("7. View Employees")
        print("8. Add Daily Work Hours for Employee")
        print("9. Attendance Analytics & Salary Report")
        print("10. Exit")

        choice = input("Enter choice: ").strip()

        if choice == '1':
            add_new_face()
        elif choice == '2':
            start_attendance()
        elif choice == '3':
            view_attendance()
        elif choice == '4':
            export_attendance()
        elif choice == '5':
            delete_attendance()
        elif choice == '6':
            add_employee()
        elif choice == '7':
            view_employees()
        elif choice == '8':
            add_work_hours()
        elif choice == '9':
            attendance_analytics()
        elif choice == '10':
            print("[INFO] Exiting program.")
            break
        else:
            print("[ERROR] Invalid choice, try again.")

if __name__ == "__main__":
    main_menu()
    conn.close()
