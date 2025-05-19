from agentSession import AgentSession
from leadsAgent import root_agent


initial_state = {
    "LeadID": "00972",
    "LeadName": "Fajju",
}

session = AgentSession(initial_state,root_agent,timeout=3)
session.run()