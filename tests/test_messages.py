import pytest, os
os.environ['TESTING'] = '1'
from models import Message, User, db

def test_messages_page_requires_login(client, init_database):
    """Test that messages page requires authentication."""
    response = client.get('/messages', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.location

def test_messages_page_authenticated(client, init_database):
    """Test accessing messages page when authenticated."""
    # First login
    client.post('/login', data={
        'username': 'doctor1',
        'password': 'Doctor123!'
    })
    
    response = client.get('/messages')
    assert response.status_code == 200
    assert b'Messages' in response.data
    assert b'Urgent: Low Stock' in response.data

def test_add_message_success(client, init_database):
    """Test successfully adding a new message."""
    # First login
    client.post('/login', data={
        'username': 'doctor1',
        'password': 'Doctor123!'
    })
    
    response = client.post('/add_message', data={
        'title': 'Test Message',
        'content': 'This is a test message content',
        'is_urgent': True
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Message sent successfully' in response.data
    
    # Verify message was created
    message = Message.query.filter_by(title='Test Message').first()
    assert message is not None
    assert message.content == 'This is a test message content'
    assert message.is_urgent == True

def test_message_can_delete_logic(client, init_database):
    """Test the can_delete logic for messages."""
    message = Message.query.filter_by(title='Urgent: Low Stock').first()
    sender = User.query.get(message.sender_id)
    pharmacist = User.query.filter_by(role='pharmacist').first()
    other_user = User.query.filter_by(role='nurse').first()
    
    # Sender should be able to delete
    assert message.can_delete(sender) == True
    
    # Pharmacist should be able to delete any message
    assert message.can_delete(pharmacist) == True
    
    # Other users should not be able to delete
    assert message.can_delete(other_user) == False