"""
Test utilities for the application
"""

def login(client, email, password):
    """Helper function to log in a user for testing"""
    return client.post('/auth/login', data={
        'email': email,
        'password': password,
        'remember_me': False
    }, follow_redirects=True)


def logout(client):
    """Helper function to log out a user for testing"""
    return client.get('/auth/logout', follow_redirects=True)