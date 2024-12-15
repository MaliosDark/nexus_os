import logging

logger = logging.getLogger("CommandParser")

async def parse_command(command_text):
    command_text = command_text.lower().strip()

    try:
        if "open browser" in command_text:
            url = command_text.split("and go to")[-1].strip() if "and go to" in command_text else "https://aswss.com"
            logger.info(f"Browser command detected with URL: {url}")
            return {"action": "open_browser", "parameters": {"url": url}}

        if any(cmd in command_text for cmd in ["explore folder", "open directory", "open folder"]):
            path = command_text.split("folder")[-1].strip() if "folder" in command_text else command_text.split("directory")[-1].strip()
            logger.info(f"Folder command detected with path: {path}")
            return {"action": "explore_folder", "parameters": {"path": path}}

        if "open program" in command_text:
            program = command_text.split("open program")[-1].strip()
            logger.info(f"Program command detected with program: {program}")
            return {"action": "open_program", "parameters": {"program": program}}

        logger.warning("Unknown command detected.")
        return {"action": "unknown"}

    except Exception as e:
        logger.error(f"Error parsing command: {e}")
        return {"action": "unknown", "error": "Parsing error occurred."}
