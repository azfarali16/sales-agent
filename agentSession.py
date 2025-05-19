import uuid
import json
import os
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import threading
import time

class AgentSession:
    def __init__(self, lead_id, lead_name, agent, session_path="sessionLogs",timeout=24):
        self.lead_id = lead_id
        self.lead_name = lead_name
        self.agent = agent
        self.session_path = session_path

        self.session_service = InMemorySessionService()
        self.app_name = f"{lead_name} LeadAgent"
        self.user_id = lead_name
        self.session_id = str(uuid.uuid4())
        self.end_session = False

        self.session = self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id,
            state={"LeadID": lead_id, "LeadName": lead_name},
        )

        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

        # Start with system message to trigger first model output
        self.initial_prompt = None
        self._process_message(self.initial_prompt)


    def _end_session(self):
        # if self.timer:
        #     self.timer.cancel()
        self.end_session = True
        self._save_session_log()
        self.session_service.close_session(session=self.session)

    # def _start_followup_timer(self):
    #     if self.timer:
    #         self.timer.cancel()
    #     self.timer = threading.Timer(self.timeout, self._send_followup)
    #     self.timer.start()

    # def _send_followup(self):
    #     if self.end_session:
    #         return
    #     self.followup_count += 1
    #     if self.followup_count == 1:
    #         print("\nModel: Just checking in — are you still there?")
    #     elif self.followup_count == 2:
    #         print("\nModel: Still here to help if you need anything.")
    #     else:
    #         print("\nModel: Ending session due to inactivity.")
    #         self.end_session = 1
    #         # self._end_session()
    #     print(f"{self.lead_name}: ", end='', flush=True)
    #     if not self.end_session:
    #         self._start_followup_timer()


    def _process_message(self, new_message):
        response_text = None
        for event in self.runner.run(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=new_message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text

            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "function_response") and part.function_response:
                        response = part.function_response
                        if (
                            response.name == "store_lead_info"
                            and response.response.get("status") == 1
                        ):
                            self._end_session()
                            return "Thank you for taking participating."
        return response_text

    def handle_user_message(self, text):
        if self.end_session:
            return "Session has already ended."

        user_msg = types.Content(role="user", parts=[types.Part(text=text)])
        return self._process_message(user_msg)


    def _save_session_log(self):
        session = self.session_service.get_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id,
        )

        logs = []
        for event in session.events:
            log_entry = {
                "source": getattr(event, "source", "unknown"),
                "role": getattr(event.content, "role", None),
                "text": None
            }
            if event.content and event.content.parts:
                log_entry["text"] = event.content.parts[0].text
            logs.append(log_entry)

        filename = f"session_log_{self.session_id}.json"
        os.makedirs(self.session_path, exist_ok=True)
        output_path = f"{self.session_path}/{filename}"

        with open(output_path, "w") as f:
            json.dump(logs, f, indent=2)

        print(f"Session log saved to {output_path}")