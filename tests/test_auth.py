import pytest
from models import User,db

def test_user_creation(client, init_database):
    """Test user creation and password hashing."""
    user = User.query.filter_by(username='doctor1').first()
    assert user is not None
    assert user.email == 'doctor@test.com'
    assert user.role == 'doctor'
    assert user.check_password('Doctor123!')
    assert not user.check_password('wrongpassword')

def test_user_registration(client, init_database):
    """Test user registration via form."""
    response = client.post('/signup', data={
        'username': 'newuser',
        'email': 'newuser@test.com',
        'password': 'Newpass123!',
        'confirm_password': 'Newpass123!',
        'role': 'nurse'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Registration successful' in response.data
    
    # Check user was created in database
    user = User.query.filter_by(username='newuser').first()
    assert user is not None
    assert user.email == 'newuser@test.com'

def test_user_login_success(client, init_database):
    """Test successful user login."""
    response = client.post('/login', data={
        'username': 'doctor1',
        'password': 'Doctor123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Login successful' in response.data

def test_user_login_invalid_credentials(client, init_database):
    """Test login with invalid credentials."""
    response = client.post('/login', data={
        'username': 'doctor1',
        'password': 'WrongPassword!'
    }, follow_redirects=True)
    
    assert b'Invalid username or password' in response.data

def test_password_validation():
    """Test password strength validation."""
    # Test valid password
    is_valid, message = User.validate_password_strength('Test123!')
    assert is_valid == True
    
    # Test short password
    is_valid, message = User.validate_password_strength('Test1!')
    assert is_valid == False
    assert '8 characters' in message