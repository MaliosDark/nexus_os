import pyautogui

def type_text(text):
    pyautogui.write(text)
    print(f"Typed text: {text}")
