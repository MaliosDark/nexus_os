import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QScrollArea, QLabel, QLineEdit, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QByteArray
from PySide6.QtWidgets import QLabel
from nexus_os.core.ai_engine import AICore
from nexus_os.core.logger import setup_logger
import yaml
import asyncio


# Append the root directory of the project to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)


class WorkerThread(QThread):
    result_ready = Signal(str)

    def __init__(self, ai_core, user_input):
        super().__init__()
        self.ai_core = ai_core
        self.user_input = user_input

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.ai_core.chat_module.process_input(self.user_input))
            self.result_ready.emit(result)
        except Exception as e:
            self.result_ready.emit(f"Error: {str(e)}")


class NexusOSGUI(QMainWindow):
    def __init__(self, ai_core):
        super().__init__()

        # AI Core Integration
        self.ai_core = ai_core

        # Main Window
        self.setWindowTitle("Nexus OS")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)

        # UI Setup
        self.central_widget = QWidget(self)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        self.set_stylesheet()
        self.setup_ui()

    def setup_ui(self):
        # Chat Scroll Area
        self.chat_scroll = QScrollArea(self)
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setObjectName("chatScroll")

        # Chat Area with transparent overlay
        self.chat_area_widget = QWidget(self)
        self.chat_layout = QVBoxLayout(self.chat_area_widget)
        self.chat_layout.setAlignment(Qt.AlignBottom)  # Align messages at the bottom
        self.chat_area_widget.setLayout(self.chat_layout)

        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-image: url('./nexus_os/bgchat/Background.jpg'); 
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed; 
            }
            QScrollArea > QWidget {
                background: rgba(0, 0, 0, 0.5); 
            }
        """)

        self.chat_scroll.setWidget(self.chat_area_widget)
        self.central_layout.addWidget(self.chat_scroll)

        # User Input
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your command or chat here...")
        self.input_field.setObjectName("inputField")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setObjectName("sendButton")
        input_layout.addWidget(send_button)

        self.central_layout.addLayout(input_layout)

        # Action Buttons
        button_layout = QHBoxLayout()

        open_browser_btn = QPushButton("Open Browser")
        open_browser_btn.clicked.connect(lambda: self.process_command("open browser"))
        open_browser_btn.setObjectName("actionButton")
        button_layout.addWidget(open_browser_btn)

        capture_screen_btn = QPushButton("Capture Screen")
        capture_screen_btn.clicked.connect(lambda: self.process_command("capture screen"))
        capture_screen_btn.setObjectName("actionButton")
        button_layout.addWidget(capture_screen_btn)

        clear_chat_btn = QPushButton("Clear Chat")
        clear_chat_btn.clicked.connect(self.clear_chat)
        clear_chat_btn.setObjectName("actionButton")
        button_layout.addWidget(clear_chat_btn)

        self.central_layout.addLayout(button_layout)

    def send_message(self):
        user_input = self.input_field.text()
        if user_input.strip():
            self.add_message_bubble(user_input, "user")
            self.input_field.clear()

            # Add temporary "thinking" animation
            self.add_message_bubble("Thinking...", "loading")

            self.worker_thread = WorkerThread(self.ai_core, user_input)
            self.worker_thread.result_ready.connect(self.display_response)
            self.worker_thread.start()

    def add_message_bubble(self, message, sender):
        """
        Adds a styled message bubble to the chat area and ensures the chat scrolls down.
        Detects Base64 image strings and renders them as images within styled bubbles.
        """
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(0)

        # Create the bubble container
        bubble_container = QWidget()
        bubble_layout = QVBoxLayout(bubble_container)
        bubble_layout.setContentsMargins(10, 10, 10, 10)
        bubble_layout.setSpacing(5)

        # Check if the message contains an image in Base64 format
        if isinstance(message, str) and message.startswith("data:image/png;base64,"):
            try:
                # Extract the Base64 data and convert it to an image
                base64_data = message.split(",", 1)[1]
                byte_data = QByteArray.fromBase64(base64_data.encode("utf-8"))
                pixmap = QPixmap()
                if not pixmap.loadFromData(byte_data):  # Validate pixmap loading
                    raise ValueError("Failed to load image from Base64 data.")

                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                image_label.setMaximumSize(400, 400)  # Limit displayed image size

                bubble_layout.addWidget(image_label)  # Add the image to the bubble layout
            except Exception as e:
                # Handle invalid Base64 data or image errors
                error_label = QLabel(f"Error loading image: {str(e)}")
                error_label.setWordWrap(True)
                error_label.setFont(QFont("Arial", 10))
                error_label.setStyleSheet("""
                    QLabel {
                        background-color: #E74C3C;
                        color: white;
                        border-radius: 10px;
                        padding: 8px;
                    }
                """)
                bubble_layout.addWidget(error_label)
        else:
            # If it's a plain text message
            text_label = QLabel(message)
            text_label.setWordWrap(True)
            text_label.setFont(QFont("Arial", 10))
            bubble_layout.addWidget(text_label)

        # Apply styling based on the sender
        if sender == "user":
            bubble_container.setStyleSheet("""
                QWidget {
                    background-color: #2E86C1;
                    color: white;
                    border-radius: 10px;
                    padding: 8px;
                }
            """)
            container_layout.addWidget(QWidget(), 1)  # Add spacer on the left
            container_layout.addWidget(bubble_container, 0)  # Add the bubble on the right
        elif sender == "ai":
            bubble_container.setStyleSheet("""
                QWidget {
                    background-color: #27AE60;
                    color: white;
                    border-radius: 10px;
                    padding: 8px;
                }
            """)
            container_layout.addWidget(bubble_container, 0)  # Add the bubble on the left
            container_layout.addWidget(QWidget(), 1)  # Add spacer on the right
        elif sender == "loading":
            bubble_container.setStyleSheet("""
                QWidget {
                    background-color: #F39C12;
                    color: white;
                    border-radius: 10px;
                    padding: 8px;
                    font-style: italic;
                }
            """)
            container_layout.addWidget(QWidget(), 1)
            container_layout.addWidget(bubble_container, 0)

        # Add the bubble container to the chat layout
        self.chat_layout.addWidget(container)
        self.scroll_to_bottom()



    def scroll_to_bottom(self):
        """
        Ensures the scroll area is always at the bottom after new messages are added.
        """
        QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def display_response(self, response):
        """
        Displays the AI's response and removes the "thinking" bubble.
        """
        # Remove the "thinking" bubble
        if self.chat_layout.count() > 0:
            last_widget = self.chat_layout.itemAt(self.chat_layout.count() - 1).widget()
            if last_widget and isinstance(last_widget, QWidget):
                last_widget.deleteLater()

        # Handle the response as either an image or text
        if isinstance(response, str) and response.startswith("data:image/png;base64,"):
            self.add_message_bubble(response, "ai")  # Image response
        else:
            self.add_message_bubble(response, "ai")  # Text response


    def clear_chat(self):
        """
        Clears the chat area.
        """
        for i in reversed(range(self.chat_layout.count())):
            layout_item = self.chat_layout.itemAt(i)
            if layout_item.widget():
                layout_item.widget().deleteLater()
            else:
                layout_item.layout().deleteLater()

    def process_command(self, command):
        """
        Processes predefined commands.
        """
        self.add_message_bubble(f"Executing: {command}", "user")
        self.worker_thread = WorkerThread(self.ai_core, command)
        self.worker_thread.result_ready.connect(self.display_response)
        self.worker_thread.start()

    def set_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background: transparent; /* Asegura transparencia */
                color: white;
                font-family: Arial;
            }
            QScrollArea {
                border: none;
                background: rgba(0, 0, 0, 0.7); /* Solo capa oscura */
                border-radius: 10px;
            }
            QLineEdit {
                background: rgba(50, 50, 50, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background: rgba(70, 70, 70, 0.9);
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:hover {
                background: rgba(100, 100, 100, 0.9);
            }
        """)


def main():
    with open("nexus_os/core/config.yaml", "r") as file:
        config = yaml.safe_load(file)

    logger = setup_logger(config["system"]["log_level"])

    ai_core = AICore(config, logger)

    app = QApplication(sys.argv)
    window = NexusOSGUI(ai_core)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
