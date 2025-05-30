# Lead Sales Agent

A smart lead generation bot that simulates a sales agent using Google ADK and Gemini 2.0 (LLM).  
It collects basic information through an HTTP form, interacts with the user via natural language, and stores responses securely in CSV format.

---

## Features

- Powered by Gemini 2.0 LLM for natural, context-aware interactions
- Integrated with Google ADK for smart agent orchestration
- Simple HTTP form triggers the interaction
- Asks 3 lead-qualifying questions:
  1. What is your age?
  2. Which country are you from?
  3. What are your interests?
- Saves all responses in a structured CSV file
- Includes a timeout mechanism:
  - Reminds users 3 times if inactive
  - Automatically ends the session if unanswered

---

## Technologies Used

- Python  
- Google ADK  
- Gemini 2.0 (LLM)  
- Flask (or any basic HTTP server)  
- CSV for data storage

---
