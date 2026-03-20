import os
import requests
from dotenv import load_dotenv

load_dotenv()

class TrioClient:
    def __init__(self):
        self.base_url = os.getenv("TRIO_BASE_URL")
        self.api_key = os.getenv("TRIO_API_KEY")
        self.project_id = os.getenv("TRIO_PROJECT_ID")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def log_time_entry(self, date: str, hours: float, summary: str, user_email: str = None):
        """
        POST a time entry to Trio.
        Adjust the payload keys to match your Trio API's schema.
        """
        payload = {
            "project_id": self.project_id,
            "date": date,           # e.g., "2026-03-19"
            "hours": hours,
            "description": summary,
        }
        if user_email:
            payload["user_email"] = user_email

        response = requests.post(
            f"{self.base_url}/time-entries",  # ← Update to your actual Trio endpoint
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()
