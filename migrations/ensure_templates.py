import os
import shutil

# Directories to ensure exist
template_dirs = [
    'app/templates/auth',
]

# Template content
templates = {
    'app/templates/auth/register.html': '''{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h1 class="h3 mb-0">Register</h1>
                </div>
                <div class="card-body">
                    <form method="POST" action="{{ url_for('auth.register') }}">
                        {{ form.hidden_tag() }}

                        <div class="mb-3">
                            {{ form.first_name.label(class="form-label") }}
                            {{ form.first_name(class="form-control") }}
                            {% for error in form.first_name.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.last_name.label(class="form-label") }}
                            {{ form.last_name(class="form-control") }}
                            {% for error in form.last_name.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.email.label(class="form-label") }}
                            {{ form.email(class="form-control") }}
                            {% for error in form.email.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.username.label(class="form-label") }}
                            {{ form.username(class="form-control") }}
                            {% for error in form.username.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.password.label(class="form-label") }}
                            {{ form.password(class="form-control") }}
                            {% for error in form.password.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.password2.label(class="form-label") }}
                            {{ form.password2(class="form-control") }}
                            {% for error in form.password2.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.role.label(class="form-label") }}
                            {{ form.role(class="form-select") }}
                            {% for error in form.role.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="d-grid">
                            {{ form.submit(class="btn btn-primary") }}
                        </div>
                    </form>
                </div>
                <div class="card-footer text-center">
                    <p class="mb-0">Already have an account? <a href="{{ url_for('auth.login') }}">Login</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',
    'app/templates/auth/login.html': '''{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h1 class="h3 mb-0">Login</h1>
                </div>
                <div class="card-body">
                    {% with messages = get_flashed_messages() %}
                    {% if messages %}
                    <div class="alert alert-info">
                        <ul class="mb-0">
                            {% for message in messages %}
                            <li>{{ message }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                    {% endwith %}

                    <form method="POST" action="{{ url_for('auth.login') }}">
                        {{ form.hidden_tag() }}

                        <div class="mb-3">
                            {{ form.email.label(class="form-label") }}
                            {{ form.email(class="form-control") }}
                            {% for error in form.email.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3">
                            {{ form.password.label(class="form-label") }}
                            {{ form.password(class="form-control") }}
                            {% for error in form.password.errors %}
                            <div class="text-danger">{{ error }}</div>
                            {% endfor %}
                        </div>

                        <div class="mb-3 form-check">
                            {{ form.remember_me(class="form-check-input") }}
                            {{ form.remember_me.label(class="form-check-label") }}
                        </div>

                        <div class="d-grid">
                            {{ form.submit(class="btn btn-primary") }}
                        </div>

                        <div class="text-center mt-3">
                            <a href="{{ url_for('auth.reset_password_request') }}">Forgot your password?</a>
                        </div>
                    </form>
                </div>
                <div class="card-footer text-center">
                    <p class="mb-0">Don't have an account? <a href="{{ url_for('auth.register') }}">Register</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',
}

def ensure_templates():
    """Ensure all necessary template directories and files exist"""
    print("Checking for missing template files...")

    # Ensure directories exist
    for dir_path in template_dirs:
        if not os.path.exists(dir_path):
            print(f"Creating directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)

    # Ensure template files exist
    for target_file, content in templates.items():
        if not os.path.exists(target_file):
            print(f"Creating template file: {target_file}")
            with open(target_file, 'w') as f:
                f.write(content)
            print(f"Template file created: {target_file}")
        else:
            print(f"Template file already exists: {target_file}")

if __name__ == "__main__":
    ensure_templates()