from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging
from sqlalchemy.exc import SQLAlchemyError

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy(app)

# Database Models
class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    position = db.Column(db.String(80), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)

class WorkHours(db.Model):
    __tablename__ = 'work_hours'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    hours = db.Column(db.Float, nullable=False)

# Create tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database creation failed: {str(e)}")
        raise

# Role base salaries
ROLE_BASE_SALARY = {
    "tinker": 20000,
    "car internal worker": 25000,
    "car external worker": 27000,
    "manager": 45000,
    "accountant": 40000,
}

@app.route('/')
def home():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        records = Attendance.query.filter_by(date=today).order_by(Attendance.time).all()
        employee_count = Employee.query.count()
        return render_template('index.html', 
                             records=records, 
                             employee_count=employee_count,
                             today=today)
    except Exception as e:
        logger.error(f"Home page error: {str(e)}")
        flash('Error loading dashboard', 'danger')
        return render_template('error.html')

@app.route('/mark', methods=['POST'])
def mark_attendance():
    try:
        name = request.form.get('name')
        if not name:
            flash('Name cannot be empty', 'warning')
            return redirect(url_for('home'))

        today = datetime.now().strftime("%Y-%m-%d")
        
        # Verify employee exists
        if not Employee.query.filter_by(name=name).first():
            flash(f'{name} is not a registered employee', 'danger')
            return redirect(url_for('home'))

        # Check if already marked today
        if Attendance.query.filter_by(name=name, date=today).first():
            flash(f'{name} already marked attendance today', 'info')
            return redirect(url_for('home'))

        # Create new record
        new_record = Attendance(
            name=name,
            time=datetime.now().strftime("%H:%M:%S"),
            date=today
        )
        
        db.session.add(new_record)
        db.session.commit()
        flash(f'Attendance marked for {name}', 'success')
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error marking attendance: {str(e)}")
        flash('Failed to mark attendance', 'danger')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        flash('An error occurred', 'danger')
    
    return redirect(url_for('home'))

@app.route('/attendance')
def view_attendance():
    try:
        records = Attendance.query.order_by(
            Attendance.date.desc(),
            Attendance.time.desc()
        ).all()
        
        if not records:
            flash('No attendance records found', 'info')
            
        return render_template('attendance.html', 
                           records=records,
                           now=datetime.now().strftime("%Y-%m-%d"))
    
    except SQLAlchemyError as e:
        logger.error(f"Database error viewing attendance: {str(e)}")
        flash('Failed to load attendance records', 'danger')
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        try:
            name = request.form.get('name').strip()
            position = request.form.get('position').lower().strip()
            
            if not name:
                flash('Name cannot be empty', 'danger')
                return redirect(url_for('add_employee'))
                
            if position not in ROLE_BASE_SALARY:
                flash('Invalid position selected', 'danger')
                return redirect(url_for('add_employee'))
                
            new_employee = Employee(
                name=name,
                position=position,
                base_salary=ROLE_BASE_SALARY[position]
            )
            
            db.session.add(new_employee)
            db.session.commit()
            flash(f'Employee {name} added successfully!', 'success')
            return redirect(url_for('view_employees'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error adding employee: {str(e)}")
            flash('Employee already exists', 'danger')
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            flash('An error occurred', 'danger')
    
    return render_template('add_employee.html', 
                         roles=sorted(ROLE_BASE_SALARY.keys()))

@app.route('/employees')
def view_employees():
    try:
        employees = Employee.query.order_by(Employee.name).all()
        return render_template('employees.html', 
                           employees=employees,
                           roles=ROLE_BASE_SALARY)
    except Exception as e:
        logger.error(f"Error loading employees: {str(e)}")
        flash('Failed to load employee list', 'danger')
        return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Error: {str(e)}")
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))  # Default to 5001
    app.run(host='0.0.0.0', port=port, debug=True)