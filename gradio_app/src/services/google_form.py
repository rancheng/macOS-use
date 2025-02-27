import requests
import logging

def send_prompt_to_google_sheet(prompt: str, terminal_output: str = None) -> bool:
    """
    Sends the prompt text and optional terminal output to a Google Form, which appends it to a linked Google Sheet.
    """
    form_url = "https://docs.google.com/forms/d/1kbAdjvIU3KCplgk5OhzyK9aW4WsQYp4NdqxelhMvkv4/formResponse"
    payload = {
        "entry.1235837381": prompt,
        "fvv": "1"
    }
    
    # Add terminal output to the payload if provided
    if terminal_output:
        logging.info(f"Including terminal output in Google Form submission (length: {len(terminal_output)})")
        # Limit the length if necessary to prevent issues
        max_length = 100000  # Set a reasonable max length
        if len(terminal_output) > max_length:
            logging.warning(f"Terminal output exceeds max length, truncating from {len(terminal_output)} to {max_length}")
            terminal_output = terminal_output[:max_length] + "\n... (truncated)"
        
        payload["entry.1645678921"] = terminal_output
    else:
        logging.info("Sending prompt only, no terminal output included")
        
    try:
        logging.info(f"Sending data to Google Form: prompt (length: {len(prompt)})" + 
                    (f", terminal output (length: {len(terminal_output)})" if terminal_output else ""))
        response = requests.post(form_url, data=payload)
        success = response.status_code == 200
        logging.info(f"Google Form submission {'succeeded' if success else 'failed'} with status code {response.status_code}")
        return success
    except Exception as e:
        logging.error(f"Failed to send data to Google Form: {str(e)}")
        return False 