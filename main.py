# -*- coding: utf-8 -*-
"""
鼠标定位器 Mouse Locator v2.3 beta
按 F2 在鼠标位置显示橙色脉冲准星，帮助快速找到光标。

功能：
  - F2 全局热键触发准星动画
  - 300ms 防抖，连按不卡顿
  - 全屏模式开关
  - 单实例运行
  - 最小化到系统托盘
  - 可选开机自启动
  - iOS 风格液态玻璃 UI

仅支持 Windows。
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes

# ============================================================
# 常量
# ============================================================
APP_NAME = "鼠标定位器"
APP_VERSION = "v2.3 beta"
HOTKEY_ID = 9001
VK_F2 = 0x71
MOD_NONE = 0

# 动画参数
ANIM_FRAMES = 40          # 总帧数
ANIM_INTERVAL = 40        # 每帧间隔 ms
PULSE_FRAMES = 12         # 脉冲阶段帧数
RADIUS_START = 25         # 起始半径
RADIUS_END = 102          # 结束半径
COLOR_RING = "#FF8C00"    # 橙色
COLOR_FILL = "#FFA500"    # 浅橙填充

DEBOUNCE_MS = 300         # F2 防抖间隔

# 高 DPI 感知
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ============================================================
# 单实例检测
# ============================================================
def ensure_single_instance():
    """通过命名互斥体确保只有一个实例运行"""
    mutex_name = "Global\\MouseLocator_SingleInstance_Mutex"
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        ctypes.windll.kernel32.CloseHandle(handle)
        return False
    return True


# ============================================================
# 开机自启动
# ============================================================
def get_autostart():
    """读取开机自启动状态"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_READ)
        try:
            val, _ = winreg.QueryValueEx(key, "MouseLocator")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


def set_autostart(enable):
    """设置/取消开机自启动"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        if enable:
            exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            winreg.SetValueEx(key, "MouseLocator", 0, winreg.REG_SZ, exe)
        else:
            try:
                winreg.DeleteValue(key, "MouseLocator")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


# ============================================================
# 全局热键监听线程
# ============================================================
class HotkeyListener(threading.Thread):
    """在独立线程中监听 F2 全局热键"""

    def __init__(self, on_trigger):
        super().__init__(daemon=True)
        self.on_trigger = on_trigger
        self._running = True
        self._last_trigger = 0

    def run(self):
        hwnd = ctypes.windll.user32.FindWindowW(None, APP_NAME)
        # 注册全局热键 F2
        if not ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, MOD_NONE, VK_F2):
            return

        msg = wintypes.MSG()
        while self._running:
            # 等待消息，100ms 超时以便检查 _running
            ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == 786:  # WM_HOTKEY
                now = time.time() * 1000
                if now - self._last_trigger >= DEBOUNCE_MS:
                    self._last_trigger = now
                    self.on_trigger()
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)

    def stop(self):
        self._running = False


# ============================================================
# 准星动画窗口
# ============================================================
class CrosshairWindow:
    """全屏透明窗口，在鼠标位置绘制脉冲准星"""

    def __init__(self, root, fullscreen=False):
        self.root = root
        self.fullscreen = fullscreen
        self.win = None
        self.canvas = None
        self._anim_id = None
        self._frame = 0
        self._cx = 0
        self._cy = 0

    def _get_cursor_pos(self):
        """获取鼠标当前位置"""
        point = wintypes.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return point.x, point.y

    def _get_screen_size(self):
        """获取主屏尺寸"""
        user32 = ctypes.windll.user32
        if self.fullscreen:
            w = user32.GetSystemMetrics(0)   # SM_CXSCREEN
            h = user32.GetSystemMetrics(1)   # SM_CYSCREEN
        else:
            w = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
            h = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        return w, h

    def show(self):
        """在鼠标位置显示准星动画"""
        self._cx, self._cy = self._get_cursor_pos()
        sw, sh = self._get_screen_size()

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.9)
        self.win.geometry(f"{sw}x{sh}+0+0")
        self.win.config(bg="black")
        # 让窗口透明（黑色背景变透明）
        try:
            self.win.attributes("-transparentcolor", "black")
        except Exception:
            pass

        self.canvas = tk.Canvas(self.win, bg="black", highlightthickness=0,
                                 width=sw, height=sh)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._frame = 0
        self._animate()

    def _animate(self):
        """逐帧绘制脉冲圆"""
        if self.canvas is None or self._frame >= ANIM_FRAMES:
            self._destroy()
            return

        t = self._frame / ANIM_FRAMES
        # 半径从大变小（先扩散后收缩）
        if t < 0.3:
            # 扩散阶段
            progress = t / 0.3
            radius = RADIUS_START + (RADIUS_END - RADIUS_START) * progress
            alpha = 0.9 - 0.3 * progress
        else:
            # 收缩阶段
            progress = (t - 0.3) / 0.7
            radius = RADIUS_END - (RADIUS_END - RADIUS_START) * progress
            alpha = 0.6 - 0.6 * progress

        self.canvas.delete("ring")
        x, y = self._cx, self._cy
        # 外圈
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline=COLOR_RING, width=3, tags="ring"
        )
        # 内圈填充
        inner_r = radius * 0.5
        self.canvas.create_oval(
            x - inner_r, y - inner_r, x + inner_r, y + inner_r,
            fill=COLOR_FILL, outline="", tags="ring"
        )
        # 十字线
        cross = 8
        self.canvas.create_line(x - radius - cross, y, x - radius + cross, y,
                                fill=COLOR_RING, width=2, tags="ring")
        self.canvas.create_line(x + radius - cross, y, x + radius + cross, y,
                                fill=COLOR_RING, width=2, tags="ring")
        self.canvas.create_line(x, y - radius - cross, x, y - radius + cross,
                                fill=COLOR_RING, width=2, tags="ring")
        self.canvas.create_line(x, y + radius - cross, x, y + radius + cross,
                                fill=COLOR_RING, width=2, tags="ring")

        self._frame += 1
        self._anim_id = self.win.after(ANIM_INTERVAL, self._animate)

    def _destroy(self):
        """销毁准星窗口"""
        if self._anim_id:
            try:
                self.win.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None
        if self.win:
            try:
                self.win.destroy()
            except Exception:
                pass
            self.win = None
        self.canvas = None


# ============================================================
# 主应用
# ============================================================
class MouseLocatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("380x320")
        self.root.resizable(False, False)

        # 窗口居中
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 380) // 2
        y = (sh - 320) // 2
        self.root.geometry(f"380x320+{x}+{y}")

        # 液态玻璃风格背景
        self.root.config(bg="#F2F2F7")

        self.fullscreen_var = tk.BooleanVar(value=False)
        self.autostart_var = tk.BooleanVar(value=get_autostart())
        self.crosshair = CrosshairWindow(self.root, fullscreen=False)
        self.hotkey_listener = None
        self.tray_icon = None
        self._running = True

        self._build_ui()
        self._start_hotkey()
        self._build_tray()

        # 关闭窗口 → 最小化到托盘
        self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------
    def _build_ui(self):
        # 标题
        title_frame = tk.Frame(self.root, bg="#F2F2F7")
        title_frame.pack(fill=tk.X, pady=(24, 8))

        tk.Label(title_frame, text=APP_NAME,
                 font=("Microsoft YaHei UI", 20, "bold"),
                 bg="#F2F2F7", fg="#1C1C1E").pack()
        tk.Label(title_frame, text=APP_VERSION,
                 font=("Microsoft YaHei UI", 11),
                 bg="#F2F2F7", fg="#8E8E93").pack()

        # 卡片区域（液态玻璃卡片）
        card = tk.Frame(self.root, bg="#FFFFFF", bd=0,
                        highlightthickness=1, highlightbackground="#E5E5EA")
        card.pack(fill=tk.X, padx=24, pady=12)

        # F2 提示
        tk.Label(card, text="按 F2 在鼠标位置显示准星",
                 font=("Microsoft YaHei UI", 12),
                 bg="#FFFFFF", fg="#3C3C43").pack(anchor="w", padx=16, pady=(16, 4))

        tk.Label(card, text="按下 F2 即可在光标位置显示橙色脉冲圆圈",
                 font=("Microsoft YaHei UI", 10),
                 bg="#FFFFFF", fg="#8E8E93").pack(anchor="w", padx=16, pady=(0, 12))

        # 选项
        opts = tk.Frame(card, bg="#FFFFFF")
        opts.pack(fill=tk.X, padx=16, pady=(0, 16))

        tk.Checkbutton(opts, text="全屏模式",
                       variable=self.fullscreen_var,
                       command=self._on_toggle_fullscreen,
                       font=("Microsoft YaHei UI", 11),
                       bg="#FFFFFF", fg="#3C3C43",
                       activebackground="#FFFFFF").pack(anchor="w", pady=2)

        tk.Checkbutton(opts, text="开机自动启动",
                       variable=self.autostart_var,
                       command=self._on_toggle_autostart,
                       font=("Microsoft YaHei UI", 11),
                       bg="#FFFFFF", fg="#3C3C43",
                       activebackground="#FFFFFF").pack(anchor="w", pady=2)

        # 测试按钮
        btn_frame = tk.Frame(self.root, bg="#F2F2F7")
        btn_frame.pack(fill=tk.X, padx=24, pady=8)

        tk.Button(btn_frame, text="测试准星",
                  command=self._test_crosshair,
                  font=("Microsoft YaHei UI", 11),
                  bg="#007AFF", fg="white", bd=0,
                  activebackground="#0056CC",
                  padx=20, pady=6, cursor="hand2").pack(side=tk.LEFT)

        tk.Button(btn_frame, text="退出",
                  command=self._quit,
                  font=("Microsoft YaHei UI", 11),
                  bg="#FF3B30", fg="white", bd=0,
                  activebackground="#CC2F26",
                  padx=20, pady=6, cursor="hand2").pack(side=tk.RIGHT)

    # --------------------------------------------------------
    # 托盘
    # --------------------------------------------------------
    def _build_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw

            # 生成托盘图标（橙色圆圈）
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill=(255, 140, 0, 255),
                         outline=(255, 255, 255, 200), width=3)

            menu = pystray.Menu(
                pystray.MenuItem("显示主界面", self._show_window, default=True),
                pystray.MenuItem("测试准星", self._test_crosshair),
                pystray.MenuItem("退出", self._quit),
            )
            self.tray_icon = pystray.Icon("MouseLocator", img,
                                          "鼠标定位器", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print("托盘初始化失败:", e)

    def _show_window(self, *_):
        self.root.after(0, lambda: (self.root.deiconify(),
                                    self.root.lift(),
                                    self.root.focus_force()))

    # --------------------------------------------------------
    # 热键
    # --------------------------------------------------------
    def _start_hotkey(self):
        self.hotkey_listener = HotkeyListener(self._on_hotkey)
        self.hotkey_listener.start()

    def _on_hotkey(self):
        """热键触发，在主线程中执行"""
        self.root.after(0, self._show_crosshair)

    def _show_crosshair(self):
        self.crosshair.show()

    def _test_crosshair(self):
        self.crosshair.show()

    # --------------------------------------------------------
    # 选项回调
    # --------------------------------------------------------
    def _on_toggle_fullscreen(self):
        self.crosshair.fullscreen = self.fullscreen_var.get()

    def _on_toggle_autostart(self):
        set_autostart(self.autostart_var.get())

    # --------------------------------------------------------
    # 窗口行为
    # --------------------------------------------------------
    def _minimize_to_tray(self):
        self.root.withdraw()

    def _quit(self):
        self._running = False
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


# ============================================================
# 入口
# ============================================================
def main():
    if not ensure_single_instance():
        # 已有实例运行，不重复启动
        ctypes.windll.user32.MessageBoxW(
            None, "鼠标定位器已经在运行了", APP_NAME, 0x40)
        return

    app = MouseLocatorApp()
    app.run()


if __name__ == "__main__":
    main()
