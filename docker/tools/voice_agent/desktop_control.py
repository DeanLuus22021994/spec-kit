#!/usr/bin/env python3
"""
Desktop Control Plugin for Voice Agent
========================================

Provides Windows desktop automation capabilities:
- Mouse control (move, click, drag, scroll)
- Keyboard control (type, hotkeys, press keys)
- Window management (focus, move, resize, minimize, maximize)
- Screen capture and OCR
- Application launching

Uses pyautogui for cross-platform automation with Windows-specific enhancements.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from typing import Any

try:
    import pyautogui  # type: ignore[import-untyped,import-not-found]

    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1  # Small pause between actions
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    pyautogui = None  # type: ignore[assignment]

try:
    import win32con  # type: ignore[import-untyped,import-not-found]
    import win32gui  # type: ignore[import-untyped,import-not-found]

    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    win32gui = None  # type: ignore[assignment]
    win32con = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@dataclass
class ScreenInfo:
    """Screen information."""

    width: int
    height: int
    mouse_x: int
    mouse_y: int


@dataclass
class WindowInfo:
    """Window information."""

    hwnd: int
    title: str
    x: int
    y: int
    width: int
    height: int
    is_visible: bool


class DesktopControlPlugin:
    """
    Desktop control plugin providing mouse, keyboard, and window control.

    This plugin gives an AI agent the ability to control the Windows desktop,
    enabling automation tasks, application control, and UI interaction.
    """

    def __init__(self) -> None:
        """Initialize the desktop control plugin."""
        if not HAS_PYAUTOGUI:
            logger.warning("pyautogui not installed. Desktop control limited. " "Run: pip install pyautogui")

    # =========================================================================
    # SCREEN INFO
    # =========================================================================

    def get_screen_info(self) -> ScreenInfo:
        """Get current screen and mouse information.

        Returns:
            ScreenInfo with screen dimensions and mouse position
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return ScreenInfo(width=1920, height=1080, mouse_x=0, mouse_y=0)

        size = pyautogui.size()  # type: ignore[union-attr]
        pos = pyautogui.position()  # type: ignore[union-attr]
        return ScreenInfo(
            width=size.width,
            height=size.height,
            mouse_x=pos.x,
            mouse_y=pos.y,
        )

    def screenshot(
        self,
        filepath: str | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> str:
        """Take a screenshot of the screen.

        Args:
            filepath: Optional path to save screenshot. If None, saves to temp.
            region: Optional (x, y, width, height) to capture specific region.

        Returns:
            Path to saved screenshot
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        if filepath is None:
            filepath = os.path.join(os.environ.get("TEMP", "/tmp"), f"screenshot_{int(time.time())}.png")

        if region:
            img = pyautogui.screenshot(region=region)  # type: ignore[union-attr]
        else:
            img = pyautogui.screenshot()  # type: ignore[union-attr]

        img.save(filepath)
        return filepath

    # =========================================================================
    # MOUSE CONTROL
    # =========================================================================

    def mouse_move(self, x: int, y: int, duration: float = 0.25) -> str:
        """Move the mouse to specific coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Time to take for the move (smooth movement)

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.moveTo(x, y, duration=duration)  # type: ignore[union-attr]
        return f"Mouse moved to ({x}, {y})"

    def mouse_click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        clicks: int = 1,
    ) -> str:
        """Click the mouse at current or specified position.

        Args:
            x: Optional X coordinate (current position if None)
            y: Optional Y coordinate (current position if None)
            button: 'left', 'right', or 'middle'
            clicks: Number of clicks (2 for double-click)

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)  # type: ignore[union-attr]
            return f"Clicked {button} button {clicks}x at ({x}, {y})"
        pyautogui.click(clicks=clicks, button=button)  # type: ignore[union-attr]
        pos = pyautogui.position()  # type: ignore[union-attr]
        return f"Clicked {button} button {clicks}x at current position ({pos.x}, {pos.y})"

    def mouse_double_click(self, x: int | None = None, y: int | None = None) -> str:
        """Double-click at current or specified position."""
        return self.mouse_click(x, y, clicks=2)

    def mouse_right_click(self, x: int | None = None, y: int | None = None) -> str:
        """Right-click at current or specified position."""
        return self.mouse_click(x, y, button="right")

    def mouse_drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: str = "left",
    ) -> str:
        """Drag the mouse from one position to another.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            duration: Time to take for the drag
            button: Mouse button to hold during drag

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.moveTo(start_x, start_y)  # type: ignore[union-attr]
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration, button=button)  # type: ignore[union-attr]
        return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"

    def mouse_scroll(self, clicks: int, x: int | None = None, y: int | None = None) -> str:
        """Scroll the mouse wheel.

        Args:
            clicks: Number of scroll clicks (positive = up, negative = down)
            x: Optional X coordinate
            y: Optional Y coordinate

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        if x is not None and y is not None:
            pyautogui.scroll(clicks, x, y)  # type: ignore[union-attr]
        else:
            pyautogui.scroll(clicks)  # type: ignore[union-attr]

        direction = "up" if clicks > 0 else "down"
        return f"Scrolled {abs(clicks)} clicks {direction}"

    # =========================================================================
    # KEYBOARD CONTROL
    # =========================================================================

    def type_text(self, text: str, interval: float = 0.02) -> str:
        """Type text using the keyboard.

        Args:
            text: Text to type
            interval: Time between keypresses

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.write(text, interval=interval)  # type: ignore[union-attr]
        return f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"

    def press_key(self, key: str, presses: int = 1) -> str:
        """Press a single key.

        Args:
            key: Key to press (e.g., 'enter', 'tab', 'escape', 'f1', 'a')
            presses: Number of times to press

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.press(key, presses=presses)  # type: ignore[union-attr]
        return f"Pressed key '{key}' {presses}x"

    def hotkey(self, *keys: str) -> str:
        """Press a keyboard hotkey combination.

        Args:
            keys: Keys to press together (e.g., 'ctrl', 'c' for Ctrl+C)

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.hotkey(*keys)  # type: ignore[union-attr]
        return f"Pressed hotkey: {'+'.join(keys)}"

    def key_down(self, key: str) -> str:
        """Hold down a key."""
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.keyDown(key)  # type: ignore[union-attr]
        return f"Key down: {key}"

    def key_up(self, key: str) -> str:
        """Release a key."""
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        pyautogui.keyUp(key)  # type: ignore[union-attr]
        return f"Key up: {key}"

    # =========================================================================
    # WINDOW MANAGEMENT
    # =========================================================================

    def get_active_window(self) -> WindowInfo | None:
        """Get information about the currently active window."""
        if not HAS_WIN32 or win32gui is None:
            return None

        hwnd = win32gui.GetForegroundWindow()  # type: ignore[union-attr]
        if not hwnd:
            return None

        return self._get_window_info(hwnd)

    def get_all_windows(self) -> list[WindowInfo]:
        """Get list of all visible windows."""
        if not HAS_WIN32 or win32gui is None:
            return []

        result: list[WindowInfo] = []

        def callback(hwnd: int, _: Any) -> bool:
            if win32gui is not None and win32gui.IsWindowVisible(hwnd):  # type: ignore[union-attr]
                window_info = self._get_window_info(hwnd)
                if window_info and window_info.title:
                    result.append(window_info)
            return True

        win32gui.EnumWindows(callback, None)  # type: ignore[union-attr]
        return result

    def _get_window_info(self, hwnd: int) -> WindowInfo | None:
        """Get info for a specific window handle."""
        if not HAS_WIN32 or win32gui is None:
            return None

        try:
            title = win32gui.GetWindowText(hwnd)  # type: ignore[union-attr]
            rect = win32gui.GetWindowRect(hwnd)  # type: ignore[union-attr]

            return WindowInfo(
                hwnd=hwnd,
                title=title,
                x=rect[0],
                y=rect[1],
                width=rect[2] - rect[0],
                height=rect[3] - rect[1],
                is_visible=bool(win32gui.IsWindowVisible(hwnd)),  # type: ignore[union-attr]
            )
        except (AttributeError, OSError) as e:
            logger.debug("Error getting window info: %s", e)
            return None

    def find_window(self, title_contains: str) -> WindowInfo | None:
        """Find a window by partial title match.

        Args:
            title_contains: Substring to search for in window titles

        Returns:
            WindowInfo if found, None otherwise
        """
        windows = self.get_all_windows()
        for window in windows:
            if title_contains.lower() in window.title.lower():
                return window
        return None

    def focus_window(self, title_contains: str) -> str:
        """Bring a window to the foreground by title.

        Args:
            title_contains: Substring to search for in window titles

        Returns:
            Status message
        """
        if not HAS_WIN32 or win32gui is None:
            return "Error: win32gui not installed"

        window = self.find_window(title_contains)
        if not window:
            return f"Window not found: {title_contains}"

        try:
            win32gui.SetForegroundWindow(window.hwnd)  # type: ignore[union-attr]
            return f"Focused window: {window.title}"
        except (AttributeError, OSError) as e:
            return f"Error focusing window: {e}"

    def minimize_window(self, title_contains: str | None = None) -> str:
        """Minimize a window (current if no title specified)."""
        if not HAS_WIN32 or win32gui is None or win32con is None:
            return "Error: win32gui not installed"

        if title_contains:
            window = self.find_window(title_contains)
            if not window:
                return f"Window not found: {title_contains}"
            hwnd = window.hwnd
        else:
            hwnd = win32gui.GetForegroundWindow()  # type: ignore[union-attr]

        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)  # type: ignore[union-attr]
        return "Window minimized"

    def maximize_window(self, title_contains: str | None = None) -> str:
        """Maximize a window (current if no title specified)."""
        if not HAS_WIN32 or win32gui is None or win32con is None:
            return "Error: win32gui not installed"

        if title_contains:
            window = self.find_window(title_contains)
            if not window:
                return f"Window not found: {title_contains}"
            hwnd = window.hwnd
        else:
            hwnd = win32gui.GetForegroundWindow()  # type: ignore[union-attr]

        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)  # type: ignore[union-attr]
        return "Window maximized"

    def close_window(self, title_contains: str | None = None) -> str:
        """Close a window (current if no title specified)."""
        if not HAS_WIN32 or win32gui is None or win32con is None:
            return "Error: win32gui not installed"

        if title_contains:
            window = self.find_window(title_contains)
            if not window:
                return f"Window not found: {title_contains}"
            hwnd = window.hwnd
        else:
            hwnd = win32gui.GetForegroundWindow()  # type: ignore[union-attr]

        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)  # type: ignore[union-attr]
        return "Window close requested"

    # =========================================================================
    # APPLICATION LAUNCHING
    # =========================================================================

    def launch_application(self, path_or_name: str, args: list[str] | None = None) -> str:
        """Launch an application.

        Args:
            path_or_name: Full path or common app name (e.g., 'notepad', 'chrome')
            args: Optional command line arguments

        Returns:
            Status message
        """
        # Common application mappings
        app_map = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "code": "code",
            "vscode": "code",
        }

        app_path = app_map.get(path_or_name.lower(), path_or_name)
        cmd = [app_path] + (args or [])

        try:
            subprocess.Popen(cmd, shell=False)
            return f"Launched: {path_or_name}"
        except FileNotFoundError:
            return f"Application not found: {path_or_name}"
        except OSError as e:
            return f"Error launching application: {e}"

    def open_url(self, url: str) -> str:
        """Open a URL in the default browser.

        Args:
            url: URL to open

        Returns:
            Status message
        """
        try:
            webbrowser.open(url)
            return f"Opened URL: {url}"
        except (OSError, RuntimeError) as e:
            return f"Error opening URL: {e}"

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def wait(self, seconds: float) -> str:
        """Wait for a specified number of seconds.

        Args:
            seconds: Time to wait

        Returns:
            Status message
        """
        time.sleep(seconds)
        return f"Waited {seconds} seconds"

    def alert(self, message: str, title: str = "Alert") -> str:
        """Show an alert dialog.

        Args:
            message: Message to display
            title: Dialog title

        Returns:
            Status message
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return "Error: pyautogui not installed"

        try:
            pyautogui.alert(message, title)  # type: ignore[attr-defined]
            return f"Alert shown: {message}"
        except (AttributeError, OSError):
            return "Error: alert not available"

    def confirm(self, message: str, title: str = "Confirm") -> bool:
        """Show a confirmation dialog.

        Args:
            message: Message to display
            title: Dialog title

        Returns:
            True if OK clicked, False if Cancel clicked
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return False

        try:
            result = pyautogui.confirm(message, title)  # type: ignore[attr-defined]
            return bool(result == "OK")
        except (AttributeError, OSError):
            return False

    def prompt(self, message: str, title: str = "Input", default: str = "") -> str | None:
        """Show an input dialog.

        Args:
            message: Message to display
            title: Dialog title
            default: Default input value

        Returns:
            User input or None if cancelled
        """
        if not HAS_PYAUTOGUI or pyautogui is None:
            return None

        try:
            result = pyautogui.prompt(message, title, default)  # type: ignore[attr-defined]
            return result if isinstance(result, str) else None
        except (AttributeError, OSError):
            return None


# Semantic Kernel function decorators for the plugin
def create_sk_plugin() -> dict[str, Any]:
    """Create a Semantic Kernel compatible plugin from DesktopControlPlugin.

    Returns a dict of function metadata for SK registration.
    """
    desktop_plugin = DesktopControlPlugin()

    return {
        "name": "DesktopControl",
        "description": "Control the Windows desktop - mouse, keyboard, windows, and applications",
        "functions": {
            "get_screen_info": {
                "description": "Get screen dimensions and current mouse position",
                "function": desktop_plugin.get_screen_info,
            },
            "screenshot": {
                "description": "Take a screenshot of the screen",
                "function": desktop_plugin.screenshot,
            },
            "mouse_move": {
                "description": "Move the mouse to specific coordinates",
                "function": desktop_plugin.mouse_move,
            },
            "mouse_click": {
                "description": "Click the mouse at current or specified position",
                "function": desktop_plugin.mouse_click,
            },
            "mouse_double_click": {
                "description": "Double-click at current or specified position",
                "function": desktop_plugin.mouse_double_click,
            },
            "mouse_right_click": {
                "description": "Right-click at current or specified position",
                "function": desktop_plugin.mouse_right_click,
            },
            "mouse_drag": {
                "description": "Drag the mouse from one position to another",
                "function": desktop_plugin.mouse_drag,
            },
            "mouse_scroll": {
                "description": "Scroll the mouse wheel up or down",
                "function": desktop_plugin.mouse_scroll,
            },
            "type_text": {
                "description": "Type text using the keyboard",
                "function": desktop_plugin.type_text,
            },
            "press_key": {
                "description": "Press a single key (enter, tab, escape, f1, etc.)",
                "function": desktop_plugin.press_key,
            },
            "hotkey": {
                "description": "Press a keyboard hotkey combination (e.g., ctrl+c)",
                "function": desktop_plugin.hotkey,
            },
            "get_all_windows": {
                "description": "Get list of all visible windows",
                "function": desktop_plugin.get_all_windows,
            },
            "focus_window": {
                "description": "Bring a window to the foreground by title",
                "function": desktop_plugin.focus_window,
            },
            "minimize_window": {
                "description": "Minimize a window",
                "function": desktop_plugin.minimize_window,
            },
            "maximize_window": {
                "description": "Maximize a window",
                "function": desktop_plugin.maximize_window,
            },
            "close_window": {
                "description": "Close a window",
                "function": desktop_plugin.close_window,
            },
            "launch_application": {
                "description": "Launch an application by name or path",
                "function": desktop_plugin.launch_application,
            },
            "open_url": {
                "description": "Open a URL in the default browser",
                "function": desktop_plugin.open_url,
            },
            "wait": {
                "description": "Wait for a specified number of seconds",
                "function": desktop_plugin.wait,
            },
        },
    }


if __name__ == "__main__":
    # Test the plugin
    test_plugin = DesktopControlPlugin()

    print("Desktop Control Plugin Test")
    print("=" * 40)

    # Screen info
    screen_info = test_plugin.get_screen_info()
    print(f"Screen: {screen_info.width}x{screen_info.height}")
    print(f"Mouse: ({screen_info.mouse_x}, {screen_info.mouse_y})")

    # List windows
    if HAS_WIN32:
        all_windows = test_plugin.get_all_windows()
        print(f"\nVisible Windows ({len(all_windows)}):")
        for w in all_windows[:5]:
            print(f"  - {w.title[:50]}")
