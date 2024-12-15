import pyautogui

def capture_screen(filename="screenshot.png"):
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    print(f"Screenshot saved as {filename}")
