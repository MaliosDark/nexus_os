import base64
import requests
import json

class VisionModule:
    def __init__(self, config, logger):
        """
        Initializes the VisionModule with model configuration and logger.
        """
        self.config = config
        self.logger = logger
        self.model_name = config["vision_model"]["name"]
        self.model_host = config["vision_model"]["host"]

    def analyze_image(self, image_path):
        """
        Sends the image to the local Ollama API for analysis using the Bakllava model.
        """
        try:
            # Read and encode the image in Base64 format
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

            # Formulate the payload
            prompt = "Analyze this image and provide button locations for interaction."
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_base64],
                "max_tokens": 500,
                "temperature": 0.7,
            }

            # Send the request to the Ollama API
            api_url = f"{self.model_host}/api/generate"
            self.logger.info(f"Sending image analysis request to {api_url}...")
            response = requests.post(api_url, json=payload)

            # Check if the response is successful
            response.raise_for_status()

            # Parse and validate the response JSON
            try:
                response_data = response.json()
                self.logger.debug(f"Vision analysis result: {response_data}")

                # Validate response format
                if isinstance(response_data, dict) and "buttons" in response_data:
                    return response_data["buttons"]
                else:
                    self.logger.error("Response does not contain 'buttons' field or is not in the expected format.")
                    return []

            except json.JSONDecodeError as e:
                self.logger.error(f"JSONDecodeError during vision analysis: {e}")
                self.logger.error(f"Raw response: {response.text}")
                return []

        except requests.RequestException as e:
            self.logger.error(f"RequestException during vision analysis: {e}")
        except Exception as e:
            self.logger.error(f"Exception during vision analysis: {e}")
        return []
