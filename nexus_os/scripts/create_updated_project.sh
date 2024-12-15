#!/bin/bash

# Create directories
mkdir -p nexus_os/{core,modules/{vision,system_control,automation/scripts,nlp/models},data/history,drivers,scripts}

# Create files in core/
touch nexus_os/core/{main.py,config.yaml,logger.py,ai_engine.py}

# Create files in modules/vision/
touch nexus_os/modules/vision/{capture.py,analyze.py}

# Create files in modules/system_control/
touch nexus_os/modules/system_control/{terminal.py,hardware.py,process.py}

# Create files in modules/automation/
touch nexus_os/modules/automation/{clicks.py,scheduler.py}
touch nexus_os/modules/automation/scripts/browser.py

# Create files in modules/nlp/
touch nexus_os/modules/nlp/{process.py,chat.py}
touch nexus_os/modules/nlp/models/placeholder.txt

# Create files in data/history/
touch nexus_os/data/history/{commands.log,actions.log}

# Create files in data/
touch nexus_os/data/{user_prefs.yaml,memory.db}

# Create files in drivers/
touch nexus_os/drivers/{mouse.py,keyboard.py,audio.py}

# Create files in scripts/
touch nexus_os/scripts/{install_dependencies.sh,configure_kernel.sh,start_ai.sh}

# Create README.md
touch nexus_os/README.md

echo "Nexus OS project structure created successfully."
