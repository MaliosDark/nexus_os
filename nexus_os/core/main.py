import asyncio
from core.ai_engine import AICore
from core.logger import setup_logger
import yaml

# Load configuration
with open("nexus_os/core/config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Setup logging
logger = setup_logger(config["system"]["log_level"])

# Initialize AI Core
ai = AICore(config, logger)

async def main():
    logger.info("Starting Nexus OS")
    await ai.run()

if __name__ == "__main__":
    asyncio.run(main())
