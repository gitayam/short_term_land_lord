"""
Speech Memorization Web Application
A web app for practicing and memorizing speeches with AI assistance
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'speech-memorization-key')

# In-memory storage for demo (replace with database in production)
speeches = []
practice_sessions = []

@app.route('/')
def home():
    """Main dashboard showing speech collection"""
    return render_template('speech_dashboard.html', speeches=speeches)

@app.route('/speech/new', methods=['GET', 'POST'])
def new_speech():
    """Create a new speech to memorize"""
    if request.method == 'POST':
        data = request.get_json()
        speech = {
            'id': len(speeches) + 1,
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'difficulty': data.get('difficulty', 'medium'),
            'created_at': data.get('created_at', ''),
            'memorization_progress': 0
        }
        speeches.append(speech)
        return jsonify({'success': True, 'speech_id': speech['id']})
    
    return render_template('new_speech.html')

@app.route('/speech/<int:speech_id>')
def view_speech(speech_id):
    """View and practice a specific speech"""
    speech = next((s for s in speeches if s['id'] == speech_id), None)
    if not speech:
        return redirect(url_for('home'))
    
    return render_template('speech_practice.html', speech=speech)

@app.route('/speech/<int:speech_id>/practice', methods=['POST'])
def practice_speech(speech_id):
    """Record a practice session"""
    data = request.get_json()
    session = {
        'speech_id': speech_id,
        'accuracy': data.get('accuracy', 0),
        'time_taken': data.get('time_taken', 0),
        'mistakes': data.get('mistakes', []),
        'timestamp': data.get('timestamp', '')
    }
    practice_sessions.append(session)
    
    # Update speech progress
    speech = next((s for s in speeches if s['id'] == speech_id), None)
    if speech:
        speech['memorization_progress'] = min(100, speech['memorization_progress'] + 10)
    
    return jsonify({'success': True, 'progress': speech['memorization_progress'] if speech else 0})

@app.route('/analytics')
def analytics():
    """Show memorization analytics and progress"""
    return render_template('analytics.html', 
                         speeches=speeches, 
                         practice_sessions=practice_sessions)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'service': 'speech-memorization',
        'version': '1.0.0',
        'features': [
            'Speech Text Input',
            'Practice Mode',
            'Progress Tracking',
            'Analytics Dashboard',
            'AI Feedback (Coming Soon)'
        ]
    }

@app.route('/api/speeches')
def api_speeches():
    """API endpoint to get all speeches"""
    return jsonify({'speeches': speeches})

@app.route('/api/speech/<int:speech_id>/progress')
def api_speech_progress(speech_id):
    """API endpoint to get speech progress"""
    speech = next((s for s in speeches if s['id'] == speech_id), None)
    if not speech:
        return jsonify({'error': 'Speech not found'}), 404
    
    speech_sessions = [s for s in practice_sessions if s['speech_id'] == speech_id]
    return jsonify({
        'speech_id': speech_id,
        'progress': speech['memorization_progress'],
        'total_sessions': len(speech_sessions),
        'recent_sessions': speech_sessions[-5:] if speech_sessions else []
    })

if __name__ == '__main__':
    # Add some sample data for testing
    speeches.append({
        'id': 1,
        'title': 'Sample Speech: The Power of Words',
        'content': 'Words have power. They can inspire nations, comfort the grieving, and change the world. When we memorize great speeches, we internalize the wisdom of great minds and learn to communicate with impact.',
        'difficulty': 'easy',
        'created_at': '2025-01-15',
        'memorization_progress': 25
    })
    
    app.run(host='127.0.0.1', port=8080, debug=True)