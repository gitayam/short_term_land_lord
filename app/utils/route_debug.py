from flask import current_app

def list_routes():
    """List all registered routes in the application."""
    output = []
    for rule in current_app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = f"{rule.endpoint:50s} {methods:20s} {rule}"
        output.append(line)
    return '\n'.join(sorted(output))
