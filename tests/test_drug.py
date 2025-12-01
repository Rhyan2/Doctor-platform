import pytest
from datetime import datetime, timedelta
from app import db
from models import Drug

def test_drugs_page_requires_login(client, init_database):
    """Test that drugs page requires authentication."""
    response = client.get('/drugs', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_drugs_page_authenticated(client, init_database):
    """Test accessing drugs page when authenticated."""
    # First login
    client.post('/login', data={
        'username': 'doctor1',
        'password': 'Doctor123!'
    })
    
    response = client.get('/drugs')
    assert response.status_code == 200
    assert b'Drug Inventory' in response.data
    assert b'Paracetamol' in response.data

def test_add_drug_success(client, app, init_database):
    """Test successfully adding a new drug."""
    # First login
    client.post('/login', data={
        'username': 'doctor1',
        'password': 'Doctor123!'
    })
    
    response = client.post('/add_drug', data={
        'name': 'Ibuprofen',
        'description': 'Anti-inflammatory',
        'quantity': 50,
        'price': 8.75,
        'expiry_date': (datetime.now().date() + timedelta(days=180)).strftime('%Y-%m-%d'),
        'batch_number': 'BATCH003',
        'supplier': 'Health Plus'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Drug added successfully' in response.data
    
    # Verify drug was created
    with app.app_context():
        drug = Drug.query.filter_by(name='Ibuprofen').first()
        assert drug is not None
        assert drug.quantity == 50

def test_drug_expiry_detection(app, init_database):
    """Test drug expiry detection logic."""
    with app.app_context():
        expired_drug = Drug.query.filter_by(name='Amoxicillin').first()
        non_expired_drug = Drug.query.filter_by(name='Paracetamol').first()
        
        assert expired_drug.is_expired() == True
        assert non_expired_drug.is_expired() == False

def test_drug_low_stock_detection(app, init_database):
    """Test low stock detection logic."""
    with app.app_context():
        low_stock_drug = Drug.query.filter_by(name='Amoxicillin').first()
        adequate_stock_drug = Drug.query.filter_by(name='Paracetamol').first()
        
        # Amoxicillin has quantity 5, which is low stock
        assert low_stock_drug.quantity < 10
        assert adequate_stock_drug.quantity >= 10