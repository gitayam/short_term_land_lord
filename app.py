from app import create_app, db
from app.models import User, PasswordReset, UserRoles

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'PasswordReset': PasswordReset,
        'UserRoles': UserRoles
    }

if __name__ == '__main__':
    import sys
    port = 5001
    if len(sys.argv) > 1 and sys.argv[1].startswith('--port'):
        if '=' in sys.argv[1]:
            port = int(sys.argv[1].split('=')[1])
        elif len(sys.argv) > 2:
            port = int(sys.argv[2])
    app.run(host='0.0.0.0', port=port, debug=True)