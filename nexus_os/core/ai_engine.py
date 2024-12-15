import asyncio
from nexus_os.modules.nlp.chat import ChatModule
from nexus_os.modules.vision.analyze import VisionModule
from nexus_os.modules.system_control import terminal


class AICore:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.chat_module = ChatModule(config, logger)
        self.vision_module = VisionModule(config, logger)

    async def run(self):
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Shutting down Nexus OS.")
                    self.logger.info("Nexus OS shutdown by user.")
                    break

                # Await the asynchronous ChatModule response
                self.logger.debug("Sending user input to ChatModule...")
                response = await self.chat_module.process_input(user_input)
                print(f"AI: {response}")
                self.logger.info(f"User input: {user_input} | AI response: {response}")
            except Exception as e:
                self.logger.error(f"An error occurred during processing: {e}")
                print("An error occurred. Please try again.")
