import requests
import logging

def send_prompt_to_google_sheet(prompt: str) -> bool:
    """
    Sends the prompt text to a Google Form, which appends it to a linked Google Sheet.
    """
    form_url = "https://docs.google.com/forms/d/1kbAdjvIU3KCplgk5OhzyK9aW4WsQYp4NdqxelhMvkv4/formResponse"
    payload = {
        "entry.1235837381": prompt,
        "fvv": "1"
    }
    try:
        response = requests.post(form_url, data=payload)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to send prompt to Google Form: {str(e)}")
        return False 