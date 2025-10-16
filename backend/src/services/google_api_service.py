"""
Google API Service for AQ data retrieval.
"""
import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class GoogleAPIService:
    """
    Service for interacting with the Google API.
    """
    def __init__(self):
        """
        Initializes the GoogleAPIService with the API key.
        """
        self.api_key = os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file.")

        # Endpoint for current conditions
        self.endpoint = "https://airquality.googleapis.com/v1/currentConditions:lookup"



    def get_current_conditions(
        self,
        latitude: float,
        longitude: float

    ):
        """
        Fetch current air quality conditions for given coordinates.
        """
        payload = {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            }
        }
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Error fetching data from Google API: {e}")
            return None
