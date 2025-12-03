from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Drug, Message
from datetime import datetime
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()  

#DB_USER = os.environ.get("MYSQL_USER", "root")
#DB_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
#DB_HOST = os.environ.get("MYSQL_HOST", "localhost")
#DB_NAME = os.environ.get("MYSQL_DATABASE", "inventory")




app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drug_inventory.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/inventory'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:rootpassword@db:3306/inventory'
#app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
# Near the database configuration
if os.environ.get("TESTING") == "1":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    # Get DATABASE_URL from environment with fallback
    database_url = os.environ.get('DATABASE_URL')
    
    # Debug: Print what we're getting
    print(f"DATABASE_URL from env: {database_url}")
    
    if database_url:
        # Ensure it's using the correct driver
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Fallback for local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:272902@localhost:5432/inventory'
    #app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize database tables - MUST BE HERE, AFTER app is created
with app.app_context():
    try:
        print("Checking/creating database tables...")
        db.create_all()
        print("Database setup completed!")
    except Exception as e:
        print(f"Database initialization error: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        # Validate password strength
        is_valid, message = User.validate_password_strength(password)
        if not is_valid:
            flash(f'Password too weak: {message}', 'error')
            return render_template('signup.html')
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()
        
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if existing_email:
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        try:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_drugs = Drug.query.count()
    expired_drugs = Drug.query.filter(Drug.expiry_date < datetime.now().date()).count()
    low_stock = Drug.query.filter(Drug.quantity < 10).count()
    
    # Get recent messages
    recent_messages = Message.query.order_by(Message.timestamp.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         total_drugs=total_drugs,
                         expired_drugs=expired_drugs,
                         low_stock=low_stock,
                         recent_messages=recent_messages)

@app.route('/drugs')
@login_required
def drugs():
    drug_list = Drug.query.order_by(Drug.name).all()
    return render_template('drugs.html', drugs=drug_list)

@app.route('/add_drug', methods=['GET', 'POST'])
@login_required
def add_drug():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            quantity = request.form.get('quantity')
            price = request.form.get('price')
            expiry_date = request.form.get('expiry_date')
            batch_number = request.form.get('batch_number')
            supplier = request.form.get('supplier')
            
            # Convert date string to date object
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            
            drug = Drug(
                name=name,
                description=description,
                quantity=int(quantity),
                price=float(price) if price else None,
                expiry_date=expiry_date,
                batch_number=batch_number,
                supplier=supplier,
                added_by_id=current_user.id
            )
            
            db.session.add(drug)
            db.session.commit()
            
            flash('Drug added successfully!', 'success')
            return redirect(url_for('drugs'))
        except Exception as e:
            flash(f'Error adding drug: {str(e)}', 'error')
    
    return render_template('add_drug.html')

@app.route('/edit_drug/<int:drug_id>', methods=['GET', 'POST'])
@login_required
def edit_drug(drug_id):
    drug = Drug.query.get_or_404(drug_id)
    
    if request.method == 'POST':
        try:
            drug.name = request.form.get('name')
            drug.description = request.form.get('description')
            drug.quantity = int(request.form.get('quantity'))
            drug.price = float(request.form.get('price')) if request.form.get('price') else None
            drug.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
            drug.batch_number = request.form.get('batch_number')
            drug.supplier = request.form.get('supplier')
            
            db.session.commit()
            flash('Drug updated successfully!', 'success')
            return redirect(url_for('drugs'))
        except Exception as e:
            flash(f'Error updating drug: {str(e)}', 'error')
    
    return render_template('edit_drug.html', drug=drug)

@app.route('/delete_drug/<int:drug_id>')
@login_required
def delete_drug(drug_id):
    try:
        drug = Drug.query.get_or_404(drug_id)
        db.session.delete(drug)
        db.session.commit()
        flash('Drug deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting drug: {str(e)}', 'error')
    
    return redirect(url_for('drugs'))

@app.route('/messages')
@login_required
def messages():
    message_list = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', messages=message_list)

@app.route('/add_message', methods=['GET', 'POST'])
@login_required
def add_message():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            is_urgent = 'is_urgent' in request.form
            
            message = Message(
                title=title,
                content=content,
                is_urgent=is_urgent,
                sender_id=current_user.id
            )
            
            db.session.add(message)
            db.session.commit()
            
            flash('Message sent successfully!', 'success')
            return redirect(url_for('messages'))
        except Exception as e:
            flash(f'Error sending message: {str(e)}', 'error')
    
    return render_template('add_message.html')

@app.route('/delete_message/<int:message_id>')
@login_required
def delete_message(message_id):
    try:
        message = Message.query.get_or_404(message_id)
        
        if not message.can_delete(current_user):
            flash('You are not authorized to delete this message', 'error')
            return redirect(url_for('messages'))
        
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting message: {str(e)}', 'error')
    
    return redirect(url_for('messages'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# API endpoint for drug expiry alerts
@app.route('/api/expiry_alerts')
@login_required
def expiry_alerts():
    # Drugs expiring in next 30 days
    thirty_days_from_now = datetime.now().date()
    alert_drugs = Drug.query.filter(
        Drug.expiry_date <= thirty_days_from_now
    ).order_by(Drug.expiry_date).all()
    
    alerts = [{
        'id': drug.id,
        'name': drug.name,
        'expiry_date': drug.expiry_date.strftime('%Y-%m-%d'),
        'days_until_expiry': (drug.expiry_date - datetime.now().date()).days,
        'batch_number': drug.batch_number
    } for drug in alert_drugs]
    
    return jsonify(alerts)


    # Make sure these are available for import
# At the bottom of app.py, replace the if __name__ == '__main__' block with:

if __name__ == '__main__':
    # No need to create tables here since we do it above
    app.run(host='0.0.0.0', port=5000, debug=True)  # Changed debug=True for local testing