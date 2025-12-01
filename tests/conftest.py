# tests/conftest.py
import os

# MUST set this before importing app
os.environ['TESTING'] = '1'
import pytest

import tempfile
from datetime import datetime, timedelta
# Must set TESTING before importing app

# Import your app and models
from app import app as flask_app
from app import db
from models import User, Drug, Message

@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary database
    
    db_fd, db_path = tempfile.mkstemp()
    
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'DEBUG': True
    })

    with flask_app.app_context():
        db.create_all()

    yield flask_app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def init_database(app):
    """Initialize the database with test data."""
    with app.app_context():
        # Clear any existing data
        db.drop_all()
        db.create_all()
        
        # Create test users
        doctor = User(username='doctor1', email='doctor@test.com', role='doctor')
        doctor.set_password('Doctor123!')
        
        nurse = User(username='nurse1', email='nurse@test.com', role='nurse')
        nurse.set_password('Nurse123!')
        
        pharmacist = User(username='pharmacist1', email='pharmacist@test.com', role='pharmacist')
        pharmacist.set_password('Pharmacist123!')
        
        db.session.add(doctor)
        db.session.add(nurse)
        db.session.add(pharmacist)
        db.session.commit()
        
        # Create test drugs
        drug1 = Drug(
            name='Paracetamol',
            description='Pain reliever',
            quantity=100,
            price=5.99,
            expiry_date=datetime.now().date() + timedelta(days=365),
            batch_number='BATCH001',
            supplier='Pharma Corp',
            added_by_id=doctor.id
        )
        
        drug2 = Drug(
            name='Amoxicillin',
            description='Antibiotic',
            quantity=5,  # Low stock
            price=12.50,
            expiry_date=datetime.now().date() - timedelta(days=1),  # Expired
            batch_number='BATCH002',
            supplier='Medi Supplies',
            added_by_id=pharmacist.id
        )
        
        db.session.add(drug1)
        db.session.add(drug2)
        db.session.commit()
        
        # Create test messages
        message1 = Message(
            title='Urgent: Low Stock',
            content='We are running low on Amoxicillin',
            is_urgent=True,
            sender_id=doctor.id
        )
        
        message2 = Message(
            title='Meeting Reminder',
            content='Monthly staff meeting tomorrow',
            is_urgent=False,
            sender_id=nurse.id
        )
        
        db.session.add(message1)
        db.session.add(message2)
        db.session.commit()
    
    yield
    
    # Cleanup
    with app.app_context():
        db.drop_all()