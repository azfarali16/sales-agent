import uuid
import json
import os
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import threading
import time

class AgentSession:
    def __init__(self, initial_state: dict, agent, session_path = 'sessionLogs',  timeout=24):
        print("Creating Session")
        self.initial_state = initial_state
        self.agent = agent
        self.timeout = timeout
        self.followup_count = 0


        self.lead_name = initial_state["LeadName"]
        self.lead_id = initial_state["LeadID"]

        self.session_path = session_path

        self.session_service = InMemorySessionService()
        self.app_name = f"{self.lead_name} LeadAgent"
        self.user_id = self.lead_name
        self.session_id = str(uuid.uuid4())
        self.end_session = False

        self.timer = None

        self.session = self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id,
            state=self.initial_state,
        )

        print("CREATED NEW SESSION:")
        print(f"\tSession ID: {self.session_id}")

        self.runner = Runner(
            agent=self.agent,
            app_name=self.app_name,
            session_service=self.session_service,
        )

    def _end_session(self):
        if self.timer:
            self.timer.cancel()
        self._save_session_log()
        self.session_service.close_session(session=self.session)


    def _start_followup_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(self.timeout, self._send_followup)
        self.timer.start()


    def _send_followup(self):
        if self.end_session:
            return
        self.followup_count += 1
        if self.followup_count == 1:
            print("\nModel: Just checking in — are you still there?")
        elif self.followup_count == 2:
            print("\nModel: Still here to help if you need anything.")
        else:
            print("\nModel: Ending session due to inactivity.")
            self.end_session = 1
            # self._end_session()
        print(f"{self.lead_name}: ", end='', flush=True)
        if not self.end_session:
            self._start_followup_timer()




    def _process_message(self, new_message):
        for event in self.runner.run(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=new_message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(f"Model: {event.content.parts[0].text}")
                    self._start_followup_timer()

            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "function_response") and part.function_response:
                        response = part.function_response
                        if (
                            response.name == "store_lead_info"
                            and response.response.get("status") == 1
                        ):
                            print("Lead info successfully stored. Ending session.")
                            self.end_session = True
                            break

    def run(self):
        new_message = None
        self._process_message(new_message)
        while not self.end_session:
            print('looping')
            user_input = input(f"{self.lead_name}: ")
            self.followup_count = 0
            if not user_input.strip():
                continue
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
            self._process_message(new_message)

        self._end_session()


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
