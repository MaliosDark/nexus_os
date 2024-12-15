import pyautogui

def move_mouse(x, y):
    pyautogui.moveTo(x, y)
    print(f"Mouse moved to ({x}, {y})")
