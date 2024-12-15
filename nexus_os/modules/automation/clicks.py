import pyautogui

def click(x=None, y=None):
    if x is not None and y is not None:
        pyautogui.click(x, y)
    else:
        pyautogui.click()
    print("Mouse click performed.")
