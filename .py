##首先：
pip install pyautogui
##或：
pip install pyautogui keyboard
##接着：
import pyautogui
import tkinter as tk
from tkinter import ttk

# 创建透明置顶窗口，画高亮圆圈
class CursorHighlighter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def show_circle(self):
        x, y = pyautogui.position()
        r = 60  # 圆圈半径，可以修改
        self.canvas.delete("all")
        # 画圆形高亮圈
        self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#00ffff", width=4)
        self.root.after(1200, self.clear) # 1.2秒自动消失
        self.root.mainloop()

    def clear(self):
        self.canvas.delete("all")
        self.root.destroy()

if __name__ == "__main__":
    print("按下回车，高亮鼠标位置")
    input()
    h = CursorHighlighter()
    h.show_circle()
##或：
import pyautogui
import keyboard
import tkinter as tk

def show_highlight():
    x, y = pyautogui.position()
    r = 70
    win = tk.Toplevel()
    win.attributes("-fullscreen", True)
    win.attributes("-alpha",0.35)
    win.attributes("-topmost",True)
    win.overrideredirect(True)
    c = tk.Canvas(win,bg="black",highlightthickness=0)
    c.pack(fill=tk.BOTH,expand=True)
    c.create_oval(x-r,y-r,x+r,y+r,outline="#00ffff",width=5)
    win.after(1300, win.destroy)
    win.mainloop()

print("✅ 鼠标定位器已启动！按【F1】高亮光标，按ESC退出程序")
# 注册热键
keyboard.add_hotkey("f1", show_highlight)
keyboard.wait("esc")


