from flask import Flask, render_template, request, jsonify
from agentSession import AgentSession
from leadsAgent import root_agent
from agent_session_store import agent_sessions  # A dict to store active sessions
import uuid
import os

app = Flask(__name__)

LOGS_FOLDER = "sessionLogs"
os.makedirs(LOGS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template("lead_form.html")

@app.route('/submit_form', methods=['POST'])
def submit_form():
    data = request.json
    full_name = data.get("fullName")
    email = data.get("email")
    company = data.get("companyName", "")
    
    lead_id = str(uuid.uuid4())

    session = AgentSession(lead_id, full_name, agent=root_agent,timeout=30)
    agent_sessions[lead_id] = session

    log_file = os.path.join(LOGS_FOLDER, f"session_{lead_id}.log")
    with open(log_file, 'w') as f:
        f.write(f"Lead ID: {lead_id}\n")
        f.write(f"Full Name: {full_name}\n")
        f.write(f"Email: {email}\n")
        f.write(f"Company: {company}\n")

    return jsonify({"leadId": lead_id, "message": "Session started."})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    lead_id = data.get("leadId")
    message = data.get("message")
    
    session = agent_sessions.get(lead_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    response = session.handle_user_message(message)

    log_file = os.path.join(LOGS_FOLDER, f"session_{lead_id}.log")
    with open(log_file, 'a') as f:
        f.write(f"User: {message}\n")
        f.write(f"Agent: {response}\n")

    return jsonify({"agentResponse": response})


if __name__ == '__main__':
    app.run(debug=True)
