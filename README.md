# 🖥 Smart Attendance System (Face Recognition + Salary Analytics)

## 📌 Overview
The **Smart Attendance System** is a Python-based application that uses **face recognition** to automatically mark attendance, store records in a **SQLite database**, track daily work hours, and calculate **monthly salary reports** with deductions and increments.

It combines:

- 🎯 **Face Recognition** (via `face_recognition` & `OpenCV`)
- 🗂 **SQLite Database** for attendance & employee records
- 📊 **Work Hours Tracking**
- 💰 **Role-based Salary Calculation**
- 📈 **Monthly Attendance Analytics & CSV Reports**

---

## ✨ Features

- 📸 **Add New Face** – Capture and save employee face images.
- 🎥 **Real-time Attendance Detection** – Recognize faces via webcam and log attendance.
- 📄 **View & Export Attendance** – See records or export as CSV.
- 🧹 **Delete Attendance Records** – Clear all stored attendance data.
- 👨‍💼 **Employee Management** – Add employees with role-based salaries.
- ⏳ **Work Hours Tracking** – Log daily working hours for employees.
- 📊 **Attendance & Salary Reports** – Calculate deductions and increments based on absences and overtime.
- 💾 **Persistent Storage** – Stores all data locally using SQLite.

---

## 🛠 Tech Stack
- **Python** 3.x
- **Libraries**:
  - [`opencv-python`](https://pypi.org/project/opencv-python/) – Webcam access & image processing
  - [`face_recognition`](https://pypi.org/project/face-recognition/) – Face detection & recognition
  - [`numpy`](https://numpy.org/) – Array processing
  - [`pandas`](https://pandas.pydata.org/) – Data manipulation & CSV export
  - [`sqlite3`](https://docs.python.org/3/library/sqlite3.html) – Database storage

---

## 📂 Project Structure

SmartAttendance/
│-- faces/ # Saved employee face images
│-- exports/ # Exported attendance & salary CSVs
│-- attendance.db # SQLite database
│-- Attendance.csv # Attendance records in CSV
│-- attendance.py # Main application file
│-- README.md # Project documentation

📸 Usage

Add Employee – Use menu option 6 to add an employee (name + position).
Capture Face – Use option 1 to capture and save a new face image.
Start Attendance – Use option 2 to start real-time face detection.
View Records – Use option 3 to view attendance logs.
Export CSV – Use option 4 to export attendance data.
Analytics – Use option 9 to generate monthly attendance & salary reports.

🧮 Salary Calculation Logic
Base Salary – Defined by role:
Tinker → ₹20,000
Car Internal Worker → ₹25,000
Car External Worker → ₹27,000
Manager → ₹45,000
Accountant → ₹40,000
Deductions – ₹200 per absent day.
Increments – ₹200 for each day worked over 8 hours.
