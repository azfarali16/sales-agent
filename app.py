from flask import Flask, render_template, request, jsonify
import uuid
import os
from datetime import datetime
from agentSession import AgentSession
from leadsAgent import root_agent
from google.genai import types

import threading
active_sessions = {}

# Initialize Flask app
app = Flask(__name__)

LOGS_FOLDER = 'sessionLogs'
if not os.path.exists(LOGS_FOLDER):
    os.makedirs(LOGS_FOLDER)

def get_agent_response(user_message):
    # This is a placeholder for your agent's response logic.
    # You can replace this with your own AI model or chatbot function.
    return f"Agent Response to: {user_message}"

# Route for the home page with the form
@app.route('/')
def index():
    return render_template('lead_form.html')

# Route for handling form submission and starting the conversation
@app.route('/submit_form', methods=['POST'])
def submit_form():
    data = request.json
    
    # Generate unique ID
    lead_id = str(uuid.uuid4())
    full_name = data.get('fullName')
    email = data.get('email')
    company_name = data.get('companyName', '')

    # Create AgentSession
    initial_state = {
        "LeadID": lead_id,
        "LeadName": full_name,
    }

    agent_session = AgentSession(initial_state=initial_state, agent=root_agent, timeout=10)
    active_sessions[lead_id] = agent_session

    # Start the session with the welcome message (non-blocking)
    threading.Thread(target=agent_session._process_message, args=(None,)).start()

    return jsonify({'leadId': lead_id, 'message': 'Lead created successfully'})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    lead_id = data.get('leadId')
    user_message = data.get('message')

    agent_session = active_sessions.get(lead_id)
    if not agent_session:
        return jsonify({'error': 'Session not found'}), 404

    # Process the user message
    message = types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    )
    agent_session._process_message(message)

    # Extract last model message
    session = agent_session.session_service.get_session(
        app_name=agent_session.app_name,
        user_id=agent_session.user_id,
        session_id=agent_session.session_id,
    )
    last_model_msg = None
    for event in reversed(session.events):
        if event.source == "model" and event.content and event.content.parts:
            last_model_msg = event.content.parts[0].text
            break

    if not last_model_msg:
        last_model_msg = "Thanks! I'll get back to you shortly."

    return jsonify({'leadId': lead_id, 'agentResponse': last_model_msg})



if __name__ == '__main__':
    app.run(debug=True)
