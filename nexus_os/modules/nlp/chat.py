import asyncio
import re
import subprocess
import pyautogui
import time
import requests
import base64
import sqlite3
from PIL import ImageGrab
from langchain_ollama import OllamaLLM
from nexus_os.modules.nlp.process import parse_command
from nexus_os.modules.nlp.internal_mind import analyze_conversation
from nexus_os.modules.nlp.image_generator import generate_image_and_ascii_base64
import json
import logging
import sys

class ChatModule:
    def __init__(self, config, logger):
        """
        Initializes the ChatModule with AI model, configuration, and SQLite database.
        """
        self.config = config
        self.logger = logger
        self.model_name = config["ai_model"]["name"]
        self.model_host = config["ai_model"]["host"]
        self.bakllava_model = config["vision_model"]["name"]
        self.bakllava_host = config["vision_model"]["host"]
        self.max_tokens = config["ai_model"]["max_tokens"]
        self.temperature = config["ai_model"]["temperature"]

        # Initialize the Ollama LLM for natural language processing
        self.llm = OllamaLLM(
            model=self.model_name,
            max_tokens=self.max_tokens,
            host=self.model_host,
            temperature=self.temperature,
        )

        # Initialize SQLite database
        self.db_connection = sqlite3.connect('chat_module.db', check_same_thread=False)
        self.db_cursor = self.db_connection.cursor()
        self.setup_database()

        # Auto-interaction control flag and queue
        self.stop_auto_interact = False
        self.awaiting_user_input = False
        self.interaction_queue = []

    def setup_database(self):
        """
        Sets up the SQLite database with necessary tables.
        """
        try:
            self.db_cursor.execute('''
                CREATE TABLE IF NOT EXISTS context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_input TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.db_connection.commit()
            self.logger.info("SQLite database initialized and tables are set up.")
        except sqlite3.Error as e:
            self.logger.error(f"Error setting up SQLite database: {e}")

    def enqueue_interaction(self, interaction):
        """
        Adds an interaction to the queue.
        """
        self.interaction_queue.append(interaction)
        self.logger.info(f"Interaction added to queue: {interaction}")

    def start_auto_interaction(self):
        """
        Enables the auto-interaction mode.
        """
        self.stop_auto_interact = False
        self.awaiting_user_input = False
        self.logger.info("Auto-interaction mode started.")

    def stop_auto_interaction(self):
        """
        Disables the auto-interaction mode.
        """
        self.stop_auto_interact = True
        self.logger.info("Auto-interaction mode stopped.")

    def store_context(self, user_input, ai_response):
        """
        Stores the user input and AI response in the SQLite database.
        """
        try:
            self.db_cursor.execute('''
                INSERT INTO context (user_input, ai_response)
                VALUES (?, ?)
            ''', (user_input, ai_response))
            self.db_connection.commit()
            self.logger.info("Context stored in SQLite database.")
        except sqlite3.Error as e:
            self.logger.error(f"Error storing context in SQLite database: {e}")

    def retrieve_context(self, limit=5):
        """
        Retrieves the latest context from the SQLite database.
        """
        try:
            self.db_cursor.execute('''
                SELECT user_input, ai_response, timestamp
                FROM context
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = self.db_cursor.fetchall()
            context = [{"user_input": row[0], "ai_response": row[1], "timestamp": row[2]} for row in rows]
            self.logger.info("Context retrieved from SQLite database.")
            return context
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving context from SQLite database: {e}")
            return []

    async def execute_direct_command(self, command):
        action = command["action"]
        params = command.get("parameters", {})

        if action == "generate_image":
            # Use the prompt to generate the image
            prompt = params.get("prompt")
            if not prompt:
                return "No prompt provided for image generation."

            try:
                # Generate the image and ASCII art
                result = generate_image_and_ascii_base64(prompt)

                # Log the paths of the generated files
                self.logger.info(f"Generated image and ASCII files: {result}")

                # Return the paths to the user
                return f"Image and ASCII art generated:\n" \
                    f"Original Image: {result['original_image']}\n" \
                    f"Watermarked Image: {result['watermarked_image']}\n" \
                    f"Twitter Image: {result['twitter_image']}\n" \
                    f"ASCII Art: {result['ascii_image']}\n" \
                    f"Watermarked ASCII: {result['watermarked_ascii_image']}"
            except Exception as e:
                self.logger.error(f"Error generating image: {e}")
                return f"Error generating image: {str(e)}"

        def manipulate_window(window_title, width, height, x, y):
            """
            Resize and reposition a window using wmctrl on Linux.
            """
            try:
                # Wait for the window to appear
                time.sleep(2)

                # Find the window using wmctrl
                window_list = subprocess.check_output(["wmctrl", "-l"]).decode()
                window_line = next((line for line in window_list.splitlines() if window_title in line), None)

                if window_line:
                    # Extract the window ID
                    window_id = window_line.split()[0]

                    # Resize and move the window
                    subprocess.run(["wmctrl", "-ir", window_id, "-e", f"0,{x},{y},{width},{height}"])
                    self.logger.info(f"Window '{window_title}' resized and moved to ({x}, {y}) with size ({width}x{height}).")
                else:
                    self.logger.warning(f"Window with title '{window_title}' not found.")
            except Exception as e:
                self.logger.error(f"Error manipulating window: {e}")

        if action == "open_browser":
            url = params.get("url")
            if url:
                if not url.startswith("http"):
                    url = "http://" + url

                self.logger.info(f"Opening browser with URL: {url}")

                # Open the browser with URL
                try:
                    browser_process = subprocess.Popen(["firefox", "--new-window", url])
                except FileNotFoundError:
                    self.logger.error("Firefox browser not found.")
                    return "Firefox browser not found."

                # Wait for the browser to open
                time.sleep(5)

                # Resize and reposition the browser window
                manipulate_window("Mozilla Firefox", 1280, 720, 0, 0)

                # Capture the screen
                screenshot_path = "screenshot.png"
                self.capture_screen(screenshot_path)

                # Analyze the screenshot
                button_data = self.send_to_bakllava(screenshot_path)

                # Perform interactions
                self.perform_clicks(button_data)

                return f"Browser opened with URL: {url} and interactions completed."
            else:
                self.logger.error("No URL provided for the browser.")
                return "No URL provided for the browser."

        elif action == "explore_folder":
            # Opens a folder using the system's file explorer
            path = params.get("path")
            if path:
                self.logger.info(f"Opening folder: {path}")
                try:
                    subprocess.Popen(["xdg-open", path])
                except FileNotFoundError:
                    self.logger.error(f"File explorer not found for path: {path}")
                    return f"File explorer not found for path: {path}"
                return f"Opened folder: {path}"
            self.logger.error("No folder path provided.")
            return "No folder path provided."

        elif action == "open_program":
            # Starts a specified program
            program = params.get("program")
            if program:
                try:
                    self.logger.info(f"Opening program: {program}")
                    subprocess.Popen([program])
                    return f"Program {program} started successfully."
                except FileNotFoundError:
                    self.logger.error(f"Program {program} not found.")
                    return f"Program {program} not found."
                except Exception as e:
                    self.logger.error(f"Error starting program {program}: {e}")
                    return f"Error starting program {program}: {e}"
            self.logger.error("No program specified to open.")
            return "No program specified to open."

        else:
            # Unknown command handling
            self.logger.warning(f"Unknown direct command: {action}")
            return "Unknown command."

    def capture_screen(self, save_path):
        """
        Captures the current screen and saves it to a file.
        """
        self.logger.info("Capturing the screen...")
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(save_path)
            self.logger.info(f"Screenshot saved to {save_path}")
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")

    def send_to_bakllava(self, image_path):
        """
        Sends the screenshot to Bakllava for button detection.
        Processes the response to extract buttons with coordinates.
        """
        try:
            with open(image_path, "rb") as image_file:
                # Encode the image in Base64
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

            prompt = (
                "Analyze this screenshot and return a list of buttons with their labels and exact coordinates in JSON format: "
                "[{\"label\": \"Button Label\", \"x\": X-coordinate, \"y\": Y-coordinate, \"width\": Button Width, \"height\": Button Height}]. "
            )
            payload = {
                "model": self.bakllava_model,
                "prompt": prompt,
                "images": [image_base64],
                "max_tokens": 500,
                "temperature": 0.7,
            }

            self.logger.info(f"Sending screenshot to Vision at {self.bakllava_host}...")
            response = requests.post(f"{self.bakllava_host}/api/generate", json=payload, stream=True)
            response.raise_for_status()

            # Parse the response
            full_response = ""
            for line in response.iter_lines():
                if line:  # Skip empty lines
                    try:
                        json_data = json.loads(line)
                        self.logger.debug(f"Processed chunk: {json_data}")

                        # Append 'response' part to the full response
                        if "response" in json_data:
                            full_response += json_data["response"]
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Error processing JSON chunk: {line}. Error: {e}")
                    except Exception as e:
                        self.logger.warning(f"Unexpected error processing chunk: {e}")

            self.logger.info(f"Full response received: {full_response}")

            # Extraer el bloque JSON usando una expresión regular
            json_pattern = re.compile(r'\[.*?\]', re.DOTALL)
            json_match = json_pattern.search(full_response)

            if not json_match:
                self.logger.error("Failed to find JSON in the response.")
                return {"buttons": []}

            json_content = json_match.group(0)
            try:
                button_list = json.loads(json_content)  # Parse the JSON content
                if isinstance(button_list, list):  # Ensure it's a list of button dictionaries
                    button_data = {"buttons": button_list}
                    self.logger.info(f"Extracted button data: {button_data}")
                    return button_data
                else:
                    self.logger.warning("Response is not a valid list of buttons.")
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse extracted JSON: {e}")

            return {"buttons": []}

        except requests.RequestException as e:
            self.logger.error(f"Error sending image to Bakllava: {e}")
            return {"buttons": []}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {"buttons": []}

    def extract_buttons_from_response(self, full_response):
        """
        Extracts button labels and their positions (x, y) from the model's JSON response.
        """
        button_data = {"buttons": []}
        try:
            # Parse the JSON response directly
            buttons = json.loads(full_response)
            
            if isinstance(buttons, list):  # Ensure it's a list of button dictionaries
                for button in buttons:
                    label = button.get("label", "").strip()
                    x = button.get("x")
                    y = button.get("y")
                    width = button.get("width")
                    height = button.get("height")

                    # Ensure all required fields are present
                    if label and x is not None and y is not None:
                        button_data["buttons"].append({
                            "label": label,
                            "x": int(x),
                            "y": int(y),
                            "width": int(width) if width is not None else 0,
                            "height": int(height) if height is not None else 0,
                        })

            if not button_data["buttons"]:
                self.logger.warning("No buttons found in response.")

            self.logger.info(f"Extracted button data: {button_data}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Error extracting button data: {e}")
        return button_data

    def extract_coordinates(self, text):
        """
        Extracts coordinates (x, y) from a given text.
        """
        try:
            match = re.search(r"\((\d+),\s*(\d+)\)", text)
            if match:
                x, y = int(match.group(1)), int(match.group(2))
                # Validate coordinates to ensure they are within screen bounds
                screen_width, screen_height = pyautogui.size()
                if 0 <= x <= screen_width and 0 <= y <= screen_height:
                    return x, y
            return None
        except Exception as e:
            self.logger.error(f"Error extracting coordinates: {e}")
            return None

    def perform_clicks(self, button_data):
        """
        Uses PyAutoGUI to perform clicks on detected buttons intelligently.
        Waits for user input if awaiting_user_input is True.
        """
        if self.awaiting_user_input:
            self.logger.info("Waiting for user input before continuing.")
            return

        self.logger.info("Performing clicks on detected buttons...")
        clicked_positions = set()  # Track clicked positions to avoid repeats

        for button in button_data.get("buttons", []):
            if self.stop_auto_interact:
                self.logger.info("Auto-interaction mode stopped. Exiting clicks.")
                break

            x, y = button.get("x"), button.get("y")
            label = button.get("label", "").lower()

            if x is None or y is None:
                self.logger.warning(f"Skipping button '{label}' due to missing coordinates.")
                continue

            # Ensure coordinates are within bounds
            screen_width, screen_height = pyautogui.size()
            if 0 <= x < screen_width and 0 <= y < screen_height and (x, y) not in clicked_positions:
                self.logger.info(f"Clicking on: {label} at ({x}, {y})")

                try:
                    # Ensure fail-safe is temporarily disabled during clicks
                    pyautogui.FAILSAFE = False

                    # Perform the click
                    pyautogui.moveTo(x, y, duration=0.5)
                    pyautogui.click()
                    clicked_positions.add((x, y))  # Mark as clicked

                    # Capture a new screenshot after each click to analyze changes
                    screenshot_path = "screenshot_after_click.png"
                    self.capture_screen(screenshot_path)

                    # Re-analyze the new screenshot to decide the next action
                    new_button_data = self.send_to_bakllava(screenshot_path)

                    # Inform the user of the next interaction
                    self.logger.info(f"Detected next button to click: {new_button_data}")
                    self.awaiting_user_input = True
                    self.enqueue_interaction(new_button_data)
                    print(f"Detected a new button to click: {new_button_data}. Please confirm to continue.")
                    return  # Exit the loop to wait for user confirmation
                except pyautogui.FailSafeException:
                    self.logger.error(f"Fail-safe triggered while clicking on '{label}' at ({x}, {y}).")
                except Exception as e:
                    self.logger.error(f"Error performing click on '{label}': {e}")
                finally:
                    # Re-enable fail-safe after clicks
                    pyautogui.FAILSAFE = True
            else:
                self.logger.warning(f"Button '{label}' at ({x}, {y}) is out of bounds or already clicked.")

    async def call_ai_model(self, prompt):
        """
        Calls the AI model using LangChain's OllamaLLM to generate a response.
        Incorporates context from the SQLite database and internal mind analysis.
        """
        try:
            # Retrieve context from the database
            context = self.retrieve_context()
            memory = [entry['user_input'] for entry in context]

            # Generate internal thought
            self.logger.info("Generating internal thought...")
            internal_thought = await analyze_conversation(prompt, memory)
            self.logger.info(f"Internal thought generated: {internal_thought}")

            # Format context for the AI model
            context_text = "\n".join([f"User: {entry['user_input']}\nAI: {entry['ai_response']}" for entry in context])

            # Combine internal thought and context with the new prompt
            full_prompt = f"{context_text}\nInternal Thought: {internal_thought}\nUser: {prompt}\nAI:"

            self.logger.info("Calling AI model with context and internal thought...")
            loop = asyncio.get_event_loop()
            ai_response = await loop.run_in_executor(None, self.llm.invoke, [{"role": "user", "content": full_prompt}])

            if not ai_response:
                self.logger.warning("AI model returned an empty response.")
                return "No response generated. Try again."

            # Produce a concise output by trimming the AI response
            concise_response = ai_response.strip().split('\n')[0]
            self.logger.info(f"Concise AI response: {concise_response}")

            # Store the interaction in the database
            self.store_context(user_input=prompt, ai_response=concise_response)

            return concise_response
        except Exception as e:
            self.logger.error(f"Error while calling AI model: {e}")
            return "An error occurred while processing your request."

    async def process_input(self, user_input):
        """
        Processes the user input. Resumes interaction if awaiting_user_input is True.
        """
        self.logger.info(f"Processing user input: {user_input}")

        # Check if waiting for user input to resume interaction
        if self.awaiting_user_input:
            self.logger.info("User input detected, resuming interaction.")
            self.awaiting_user_input = False

            if self.interaction_queue:
                next_interaction = self.interaction_queue.pop(0)
                self.perform_clicks(next_interaction)
                return f"Resuming interaction with detected buttons: {next_interaction}"

            return "No pending interactions in the queue."

        # Detect specific commands, e.g., "generate image"
        if user_input.startswith("generate image"):
            prompt = user_input[len("generate image"):].strip()
            if not prompt:
                return "Please provide a prompt for image generation."
            
            try:
                # Generate Base64-encoded image
                base64_image = generate_image_and_ascii_base64(prompt)
                return base64_image  # Send the Base64 string directly to the GUI
            except Exception as e:
                self.logger.error(f"Error generating image: {e}")
                return f"Error generating image: {str(e)}"
            
        # Parse input for other commands
        command = await parse_command(user_input)

        if command and command.get("action") and command["action"] != "unknown":
            # Execute recognized direct commands
            return await self.execute_direct_command(command)
        else:
            # No direct command found, use the AI model for response
            self.logger.info("No direct command found, using AI model to generate response.")
            ai_response = await self.call_ai_model(user_input)
            print(f"AI Response: {ai_response}")  # Explicitly communicate response to the user
            return ai_response

    def close(self):
        """
        Closes the SQLite database connection.
        """
        try:
            self.db_connection.close()
            self.logger.info("SQLite database connection closed.")
        except sqlite3.Error as e:
            self.logger.error(f"Error closing SQLite database connection: {e}")