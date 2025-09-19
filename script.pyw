import threading
import keyboard
#!/usr/bin/env python3
"""
Popsicle CS2 External Overlay Application

A comprehensive external overlay for Counter-Strike 2 featuring:
- ESP (Extra Sensory Perception) rendering
- Aimbot functionality  
- Triggerbot automation
- Configurable GUI interface

This is a cleaned up and reorganized version with proper structure.
"""

# Standard library imports
import os
import sys
import json
import time

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Startup configuration - set to False to disable startup delays and graphics restart
STARTUP_ENABLED = True
import random
import threading
import multiprocessing
import ctypes
import colorsys
import math

# Third-party imports
import requests
import pymem
import pymem.process
from pynput.mouse import Controller, Button

# PySide6 imports
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import QFileSystemWatcher, QCoreApplication, QTimer
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

# Import qt_material after PySide6 to avoid warnings
try:
    from qt_material import apply_stylesheet
except ImportError:
    # Fallback if qt_material is not available
    def apply_stylesheet(app, theme=None):
        pass

# Windows API imports
import win32api
import win32con
import win32gui


# ============================================================================
# GLOBAL UTILITY FUNCTIONS
# ============================================================================

def is_keybind_on_global_cooldown(settings_key):
    """Check if a keybind is on cooldown across all processes"""
    try:
        cooldown_file = KEYBIND_COOLDOWNS_FILE
        if not os.path.exists(cooldown_file):
            return False
            
        with open(cooldown_file, 'r') as f:
            cooldown_data = json.load(f)
            
        cooldown_until = cooldown_data.get(settings_key, 0)
        return time.time() < cooldown_until
    except Exception:
        return False

def trigger_graphics_restart():
    """Send Ctrl+Shift+Windows+B to restart graphics driver"""
    try:
        # Press keys: Ctrl + Shift + Windows + B
        win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl down
        win32api.keybd_event(0x10, 0, 0, 0)  # Shift down  
        win32api.keybd_event(0x5B, 0, 0, 0)  # Left Windows key down
        win32api.keybd_event(0x42, 0, 0, 0)  # B down
        
        # Release keys in reverse order
        win32api.keybd_event(0x42, 0, win32con.KEYEVENTF_KEYUP, 0)  # B up
        win32api.keybd_event(0x5B, 0, win32con.KEYEVENTF_KEYUP, 0)  # Left Windows key up
        win32api.keybd_event(0x10, 0, win32con.KEYEVENTF_KEYUP, 0)  # Shift up
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
    except Exception:
        pass


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# File paths
CONFIG_DIR = os.getcwd()
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
TERMINATE_SIGNAL_FILE = os.path.join(CONFIG_DIR, 'terminate_now.signal')
LOCK_FILE = os.path.join(CONFIG_DIR, 'script_running.lock')
KEYBIND_COOLDOWNS_FILE = os.path.join(CONFIG_DIR, 'keybind_cooldowns.json')

# Global state variables
RAINBOW_HUE = 0.0
TARGET_POSITIONS = {}  # Global dictionary to track target positions for dynamic smoothness
TARGET_POSITION_TIMESTAMPS = {}  # Track timestamps for position updates
BombPlantedTime = 0
BombDefusedTime = 0

# Aim lock state
aim_lock_state = {
    'locked_entity': None,
    'aim_was_pressed': False,
}

# Available themes
THEMES = [
    'dark_red.xml', 'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml',
    'dark_lightgreen.xml', 'dark_pink.xml', 'dark_purple.xml', 'dark_teal.xml',
    'dark_yellow.xml', 'light_amber.xml', 'light_blue.xml', 'light_cyan.xml',
    'light_cyan_500.xml', 'light_lightgreen.xml', 'light_pink.xml',
    'light_purple.xml', 'light_red.xml', 'light_teal.xml', 'light_yellow.xml'
]


# ============================================================================
# INSTANCE MANAGEMENT
# ============================================================================

def is_script_already_running():
    """Check if another instance of the script is already running."""
    return os.path.exists(LOCK_FILE)

def create_lock_file():
    """Create a lock file to indicate this instance is running."""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return False

def remove_lock_file():
    """Remove the lock file when shutting down."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass

def terminate_existing_instance():
    """Signal existing instance to terminate and wait for it to close."""
    try:
        # Create terminate signal
        with open(TERMINATE_SIGNAL_FILE, 'w') as f:
            f.write('terminate')
        
        # Wait for existing instance to close (check lock file)
        timeout = 10  # 10 seconds timeout
        start_time = time.time()
        while os.path.exists(LOCK_FILE) and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        # Clean up terminate signal
        if os.path.exists(TERMINATE_SIGNAL_FILE):
            os.remove(TERMINATE_SIGNAL_FILE)
            
        return not os.path.exists(LOCK_FILE)
    except Exception:
        return False

def handle_instance_check():
    """Check for existing instance and handle user choice."""
    if not is_script_already_running():
        return True  # No existing instance, proceed
    
    # Constants for message box
    MB_OKCANCEL = 0x00000001
    MB_SETFOREGROUND = 0x00010000
    MB_TOPMOST = 0x00040000
    MB_ICONQUESTION = 0x00000020
    IDOK = 1
    
    # Show override dialog
    result = ctypes.windll.user32.MessageBoxW(
        0, 
        "Script already running. Press OK to override and close the existing instance, or Cancel to exit.",
        "Popsicle CS2 - Already Running", 
        MB_OKCANCEL | MB_SETFOREGROUND | MB_TOPMOST | MB_ICONQUESTION
    )
    
    if result == IDOK:
        # User chose to override
        if terminate_existing_instance():
            return True  # Successfully terminated existing instance
        else:
            # Failed to terminate existing instance
            ctypes.windll.user32.MessageBoxW(
                0,
                "Failed to terminate existing instance. Please close it manually and try again.",
                "Popsicle CS2 - Error",
                0x00000010 | MB_SETFOREGROUND | MB_TOPMOST  # MB_ICONERROR
            )
            return False
    else:
        # User chose to cancel
        return False


# ============================================================================
# DEFAULT SETTINGS
# ============================================================================

# Default configuration settings
DEFAULT_SETTINGS = {
    # ESP Settings
    "esp_rendering": 1,
    "esp_mode": 0,
    "line_rendering": 1,
    "hp_bar_rendering": 1,
    "head_hitbox_rendering": 1,
    "box_rendering": 1,
    "Bones": 1,
    "nickname": 1,
    "weapon": 1,
    "bomb_esp": 1,
    "show_visibility": 1,
    "ESPToggleKey": "NONE",
    "center_dot": 0,
    "center_dot_size": 3,
    
    # Radar Settings
    "radar_enabled": 0,
    "radar_size": 200,
    "radar_scale": 5.0,
    "radar_position": "Top Right",
    "radar_position_x": 50,
    "radar_position_y": 50,
    "radar_opacity": 180,
    
    # Aim Settings
    "aim_active": 0,
    "aim_circle_visible": 1,
    "aim_mode": 2,
    "aim_mode_distance": 0,
    "aim_smoothness": 0,
    "aim_lock_target": 0,
    "aim_visibility_check": 0,
    "aim_disable_when_crosshair_on_enemy": 0,
    "radius": 50,
    "AimKey": "C",
    "circle_opacity": 127,
    "circle_thickness": 2,
    
    # Trigger Bot Settings
    "trigger_bot_active": 0,
    "TriggerKey": "X", 
    "triggerbot_delay": 30,
    "triggerbot_first_shot_delay": 0,
    
    # Bhop Settings
    "bhop_enabled": 0,
    "BhopKey": "SPACE",
    
    # UI Settings
    "topmost": 1,
    "MenuToggleKey": "F8",
    "theme": "dark_red.xml",
    "team_color": "#47A76A",
    "enemy_color": "#C41E3A",
    "aim_circle_color": "#FF0000",
    "center_dot_color": "#FFFFFF",
    "rainbow_fov": 0,
    "rainbow_center_dot": 0,
    "low_cpu": 0,
    "fps_limit": 60,
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def key_str_to_vk(key_str):
    """Convert key string to virtual key code."""
    if not key_str: 
        return 0
    ks = str(key_str).strip()
    
    if len(ks) == 1:
        try:
            vk = win32api.VkKeyScan(ks)
            return vk & 0xFF
        except Exception:
            return ord(ks.upper())
            
    if ks.startswith('F') and ks[1:].isdigit():
        try:
            n = int(ks[1:])
            if 1 <= n <= 24:
                return 0x70 + (n - 1)
        except Exception:
            pass
            
    key_map = {
        # Mouse buttons
        'LMB': 0x01, 'LEFTMOUSE': 0x01, 'MOUSE1': 0x01, 'LEFTCLICK': 0x01,
        'RMB': 0x02, 'RIGHTMOUSE': 0x02, 'MOUSE2': 0x02, 'RIGHTCLICK': 0x02,
        'MMB': 0x04, 'MIDDLEMOUSE': 0x04, 'MOUSE3': 0x04, 'MIDDLECLICK': 0x04,
        'MOUSE4': 0x05, 'X1': 0x05, 'XBUTTON1': 0x05,
        'MOUSE5': 0x06, 'X2': 0x06, 'XBUTTON2': 0x06,
        
        # Common keys
        'SPACE': win32con.VK_SPACE, 'ENTER': win32con.VK_RETURN, 'RETURN': win32con.VK_RETURN,
        'SHIFT': win32con.VK_SHIFT, 'CTRL': win32con.VK_CONTROL, 'CONTROL': win32con.VK_CONTROL,
        'ALT': win32con.VK_MENU, 'TAB': win32con.VK_TAB,
        'ESC': win32con.VK_ESCAPE, 'ESCAPE': win32con.VK_ESCAPE,
        
        # Arrow keys
        'UP': win32con.VK_UP, 'DOWN': win32con.VK_DOWN, 
        'LEFT': win32con.VK_LEFT, 'RIGHT': win32con.VK_RIGHT,
        'UPARROW': win32con.VK_UP, 'DOWNARROW': win32con.VK_DOWN,
        'LEFTARROW': win32con.VK_LEFT, 'RIGHTARROW': win32con.VK_RIGHT,
        
        # Modifier keys
        'LSHIFT': getattr(win32con, 'VK_LSHIFT', 0xA0),
        'RSHIFT': getattr(win32con, 'VK_RSHIFT', 0xA1),
        'LCTRL': getattr(win32con, 'VK_LCONTROL', 0xA2),
        'RCTRL': getattr(win32con, 'VK_RCONTROL', 0xA3),
        'LALT': getattr(win32con, 'VK_LMENU', 0xA4),
        'RALT': getattr(win32con, 'VK_RMENU', 0xA5),
        'RIGHTALT': getattr(win32con, 'VK_RMENU', 0xA5),
        
        # Other keys
        'CAPS': getattr(win32con, 'VK_CAPITAL', 0x14), 
        'CAPSLOCK': getattr(win32con, 'VK_CAPITAL', 0x14),
        'BACK': getattr(win32con, 'VK_BACK', 0x08),
        'BACKSPACE': getattr(win32con, 'VK_BACK', 0x08),
        'DELETE': getattr(win32con, 'VK_DELETE', 0x2E),
        'INSERT': getattr(win32con, 'VK_INSERT', 0x2D),
        'HOME': getattr(win32con, 'VK_HOME', 0x24),
        'END': getattr(win32con, 'VK_END', 0x23),
        'PAGEUP': getattr(win32con, 'VK_PRIOR', 0x21),
        'PAGEDOWN': getattr(win32con, 'VK_NEXT', 0x22),
        'PGUP': getattr(win32con, 'VK_PRIOR', 0x21),
        'PGDN': getattr(win32con, 'VK_NEXT', 0x22),
        
        # Numpad keys
        'NUMPAD0': getattr(win32con, 'VK_NUMPAD0', 0x60),
        'NUMPAD1': getattr(win32con, 'VK_NUMPAD1', 0x61),
        'NUMPAD2': getattr(win32con, 'VK_NUMPAD2', 0x62),
        'NUMPAD3': getattr(win32con, 'VK_NUMPAD3', 0x63),
        'NUMPAD4': getattr(win32con, 'VK_NUMPAD4', 0x64),
        'NUMPAD5': getattr(win32con, 'VK_NUMPAD5', 0x65),
        'NUMPAD6': getattr(win32con, 'VK_NUMPAD6', 0x66),
        'NUMPAD7': getattr(win32con, 'VK_NUMPAD7', 0x67),
        'NUMPAD8': getattr(win32con, 'VK_NUMPAD8', 0x68),
        'NUMPAD9': getattr(win32con, 'VK_NUMPAD9', 0x69),
        'MULTIPLY': getattr(win32con, 'VK_MULTIPLY', 0x6A),
        'ADD': getattr(win32con, 'VK_ADD', 0x6B),
        'SUBTRACT': getattr(win32con, 'VK_SUBTRACT', 0x6D),
        'DECIMAL': getattr(win32con, 'VK_DECIMAL', 0x6E),
        'DIVIDE': getattr(win32con, 'VK_DIVIDE', 0x6F),
        
        # Special keys
        'PRINTSCREEN': getattr(win32con, 'VK_SNAPSHOT', 0x2C),
        'PRTSC': getattr(win32con, 'VK_SNAPSHOT', 0x2C),
        'SCROLLLOCK': getattr(win32con, 'VK_SCROLL', 0x91),
        'PAUSE': getattr(win32con, 'VK_PAUSE', 0x13),
        'NUMLOCK': getattr(win32con, 'VK_NUMLOCK', 0x90),
        
        # Windows keys
        'LWIN': getattr(win32con, 'VK_LWIN', 0x5B),
        'RWIN': getattr(win32con, 'VK_RWIN', 0x5C),
        'APPS': getattr(win32con, 'VK_APPS', 0x5D),
        'MENU': getattr(win32con, 'VK_APPS', 0x5D),
        
        # Symbols (common ones)
        'SEMICOLON': getattr(win32con, 'VK_OEM_1', 0xBA),  # ';' key
        'EQUALS': getattr(win32con, 'VK_OEM_PLUS', 0xBB),  # '=' key
        'COMMA': getattr(win32con, 'VK_OEM_COMMA', 0xBC),  # ',' key
        'MINUS': getattr(win32con, 'VK_OEM_MINUS', 0xBD),  # '-' key
        'PERIOD': getattr(win32con, 'VK_OEM_PERIOD', 0xBE),  # '.' key
        'SLASH': getattr(win32con, 'VK_OEM_2', 0xBF),  # '/' key
        'GRAVE': getattr(win32con, 'VK_OEM_3', 0xC0),  # '`' key
        'TILDE': getattr(win32con, 'VK_OEM_3', 0xC0),  # '~' key
        'LBRACKET': getattr(win32con, 'VK_OEM_4', 0xDB),  # '[' key
        'BACKSLASH': getattr(win32con, 'VK_OEM_5', 0xDC),  # '\' key
        'RBRACKET': getattr(win32con, 'VK_OEM_6', 0xDD),  # ']' key
        'QUOTE': getattr(win32con, 'VK_OEM_7', 0xDE),  # ''' key
        'APOSTROPHE': getattr(win32con, 'VK_OEM_7', 0xDE),  # ''' key
        
        'NONE': 0
    }
    
    ks = ks.replace(' ', '')
    if ks.startswith('VK_'):
        try:
            return int(ks[3:], 0)
        except Exception:
            pass
    if ks in key_map:
        return key_map[ks]
    return ord(ks[0]) if ks else 0


def get_window_size(window_name: str):
    """Return (width, height) of the top-level window with exact title `window_name`.
    
    Returns (None, None) if the window cannot be found or on error.
    """
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            return None, None
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return right - left, bottom - top
    except Exception:
        return None, None


def get_window_rect(window_name: str):
    """Return (x, y, width, height) of the top-level window with exact title `window_name`.
    
    Returns (None, None, None, None) if the window cannot be found or on error.
    """
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            return None, None, None, None
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return left, top, right - left, bottom - top
    except Exception:
        return None, None, None, None


def get_window_client_rect(window_name: str):
    """Return (x, y, width, height) of the client area (game content area) of the window.
    
    This excludes title bars, borders, and other window decorations.
    Returns (None, None, None, None) if the window cannot be found or on error.
    """
    try:
        hwnd = win32gui.FindWindow(None, window_name)
        if not hwnd:
            return None, None, None, None
        
        # Get window rectangle (includes title bar and borders)
        window_left, window_top, window_right, window_bottom = win32gui.GetWindowRect(hwnd)
        
        # Get client rectangle (content area only, relative to window)
        client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
        
        # Convert client coordinates to screen coordinates
        client_point = win32gui.ClientToScreen(hwnd, (0, 0))
        client_screen_x, client_screen_y = client_point
        
        # Calculate client area dimensions
        client_width = client_right - client_left
        client_height = client_bottom - client_top
        
        return client_screen_x, client_screen_y, client_width, client_height
    except Exception:
        return None, None, None, None


def is_cs2_running():
    """Check if CS2 process is currently running"""
    try:
        pymem.Pymem("cs2.exe")
        return True
    except Exception:
        return False


def get_offsets_and_client_dll():
    """Fetch offsets and client_dll JSON from the remote repo.
    
    Returns a tuple (offsets, client_dll). On failure returns ({}, {}).
    """
    try:
        offsets = requests.get(
            'https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json'
        ).json()
        client_dll = requests.get(
            'https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json'
        ).json()
        return offsets, client_dll
    except Exception:
        return {}, {}


def w2s(view_matrix, x, y, z, width, height):
    """Minimal world-to-screen projection that tolerates different view_matrix shapes.
    
    Returns (screen_x, screen_y) or (-999, -999) if projection fails.
    """
    try:
        if not view_matrix or width is None or height is None:
            return -999, -999
            
        # Accept view_matrix as flat list/tuple of 16 floats or nested rows.
        if hasattr(view_matrix, '__len__') and len(view_matrix) >= 16:
            m = view_matrix
            # try common ordering: row-major 4x4
            clip_x = m[0]*x + m[1]*y + m[2]*z + m[3]
            clip_y = m[4]*x + m[5]*y + m[6]*z + m[7]
            clip_w = m[12]*x + m[13]*y + m[14]*z + m[15]
        else:
            return -999, -999
            
        if clip_w < 1e-6:
            return -999, -999
            
        ndc_x = clip_x / clip_w
        ndc_y = clip_y / clip_w
        screen_x = int((width / 2.0) * (1.0 + ndc_x))
        screen_y = int((height / 2.0) * (1.0 - ndc_y))
        return screen_x, screen_y
    except Exception:
        return -999, -999


def get_weapon_name_by_index(index):
    """Get weapon name by index."""
    weapon_names = {
        32: "P2000", 61: "USP-S", 4: "Glock", 2: "Dual Berettas", 36: "P250",
        30: "Tec-9", 63: "CZ75-Auto", 1: "Desert Eagle", 3: "Five-SeveN", 64: "R8",
        35: "Nova", 25: "XM1014", 27: "MAG-7", 29: "Sawed-Off", 14: "M249", 28: "Negev",
        17: "MAC-10", 23: "MP5-SD", 24: "UMP-45", 19: "P90", 26: "Bizon", 34: "MP9",
        33: "MP7", 10: "FAMAS", 16: "M4A4", 60: "M4A1-S", 8: "AUG", 43: "Galil",
        7: "AK-47", 39: "SG 553", 40: "SSG 08", 9: "AWP", 38: "SCAR-20", 11: "G3SG1",
        43: "Flashbang", 44: "Hegrenade", 45: "Smoke", 46: "Molotov", 47: "Decoy",
        48: "Incgrenage", 49: "C4", 31: "Taser", 42: "Knife", 41: "Knife Gold",
        59: "Knife", 80: "Knife Ghost", 500: "Knife Bayonet", 505: "Knife Flip",
        506: "Knife Gut", 507: "Knife Karambit", 508: "Knife M9", 509: "Knife Tactica",
        512: "Knife Falchion", 514: "Knife Survival Bowie", 515: "Knife Butterfly",
        516: "Knife Rush", 519: "Knife Ursus", 520: "Knife Gypsy Jackknife",
        522: "Knife Stiletto", 523: "Knife Widowmaker"
    }
    return weapon_names.get(index, 'Unknown')


def load_settings():
    """Load settings from config file."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict):
    """Save settings to config file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass


# ============================================================================
# CONFIGURATION WINDOW CLASS
# ============================================================================

class ConfigWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.drag_start_position = None
        self.is_dragging = False
        self.menu_toggle_pressed = False
        self.esp_toggle_pressed = False
        self._manually_hidden = False  # Track if user manually hid the window
        self.setStyleSheet("background-color: #020203;")
        self.initUI()

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        self.setWindowTitle("Popsicle CS2 Config")  # Set window title for identification

        
        header_label = QtWidgets.QLabel("Rert is a nigger")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setMinimumHeight(28)
        header_font = QtGui.QFont('DejaVu Sans Mono', 17, QtGui.QFont.Bold)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: white;")

        
        esp_container = self.create_esp_container()
        aim_container = self.create_aim_container()
        trigger_container = self.create_trigger_container()
        colors_container = self.create_colors_container()
        misc_container = self.create_misc_container()

        
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(esp_container, "ESP")
        tabs.addTab(aim_container, "Aim")
        tabs.addTab(trigger_container, "Trigger")
        tabs.addTab(colors_container, "Colors")
        tabs.addTab(misc_container, "Config")
        tabs.setTabPosition(QtWidgets.QTabWidget.North)
        tabs.setMovable(False)

        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(header_label)
        main_layout.addWidget(tabs)

        self.setLayout(main_layout)

        # Update all slider labels
        self.update_radius_label()
        self.update_triggerbot_delay_label()
        self.update_center_dot_size_label()
        self.update_opacity_label()
        self.update_thickness_label()
        self.update_smooth_label()

        # Initialize FPS slider state based on low CPU mode
        self.initialize_fps_slider_state()

        
        self._menu_toggle_timer = QtCore.QTimer(self)
        self._menu_toggle_timer.timeout.connect(self.check_menu_toggle)
        self._menu_toggle_timer.start(50)

        
        try:
            self._menu_toggle_ignore_until = time.time() + 0.5
        except Exception:
            self._menu_toggle_ignore_until = 0

        
        try:
            self._escape_hold_start = 0
            self._escape_hold_timer = QtCore.QTimer(self)
            self._escape_hold_timer.timeout.connect(self._check_escape_hold)
            
            self._escape_hold_timer.start(200)
        except Exception:
            
            try:
                self._escape_hold_start = 0
            except Exception:
                pass

        # Set fixed width - no horizontal scaling (do this AFTER layout is set)
        self.setFixedWidth(400)

        # Initialize keybind cooldown tracking
        self.keybind_cooldowns = {}  # Track when each keybind was last set

        # Add CS2 window monitoring for visibility control
        self._window_monitor_timer = QtCore.QTimer(self)
        self._window_monitor_timer.timeout.connect(self._check_cs2_window_active)
        self._window_monitor_timer.start(100)  # Check every 100ms
        self._was_visible = True  # Track visibility state
        self._drag_end_time = 0  # Track when dragging ended
        
        # Set initial visibility based on CS2 window state
        if not self.is_game_window_active():
            self._was_visible = False

    def is_game_window_active(self):
        """Check if CS2 or ESP overlay is the currently active window"""
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            if not foreground_hwnd:
                return False
            
            # Check if CS2 is active
            cs2_hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
            if cs2_hwnd and cs2_hwnd == foreground_hwnd:
                return True
            
            # Check if ESP overlay is active (has "ESP Overlay" in title)
            try:
                window_title = win32gui.GetWindowText(foreground_hwnd)
                if "ESP Overlay" in window_title:
                    return True
                
                # Check if it's our own config window
                if "Popsicle CS2 Config" in window_title:
                    return True
            except Exception:
                pass
            
            return False
        except Exception:
            return False

    def _check_cs2_window_active(self):
        """Monitor CS2 window activity and show/hide config window accordingly"""
        try:
            # Don't hide the window while user is dragging it
            if self.is_dragging:
                return
            
            # Don't hide the window immediately after dragging (give 500ms grace period)
            import time
            if hasattr(self, '_drag_end_time') and time.time() - self._drag_end_time < 0.5:
                return
                
            is_cs2_active = self.is_game_window_active()
            
            if is_cs2_active and not self._was_visible:
                # CS2 became active, show the window (only if not manually hidden)
                if not self._manually_hidden:
                    self.show()
                    self._was_visible = True
            elif not is_cs2_active and self._was_visible:
                # CS2 became inactive, hide the window and reset manual state
                self.hide()
                self._was_visible = False
                self._manually_hidden = False  # Reset manual state when tabbing out
        except Exception:
            pass

    def constrain_to_cs2_window(self, pos):
        """Constrain the config window position to stay within CS2 window boundaries"""
        try:
            # Get CS2 window dimensions
            cs2_rect = get_window_rect("Counter-Strike 2")
            if cs2_rect == (None, None, None, None):
                # If CS2 window not found, return original position
                return pos
            
            cs2_x, cs2_y, cs2_width, cs2_height = cs2_rect
            
            # Get config window size
            config_width = self.width()
            config_height = self.height()
            
            # Calculate constraints
            min_x = cs2_x
            max_x = cs2_x + cs2_width - config_width
            min_y = cs2_y
            max_y = cs2_y + cs2_height - config_height
            
            # Apply constraints
            constrained_x = max(min_x, min(pos.x(), max_x))
            constrained_y = max(min_y, min(pos.y(), max_y))
            
            return QtCore.QPoint(constrained_x, constrained_y)
        except Exception:
            # If anything goes wrong, return original position
            return pos

    def is_keybind_on_cooldown(self, settings_key):
        """Check if a keybind is on cooldown (within 1 second of being set)"""
        try:
            cooldown_until = self.keybind_cooldowns.get(settings_key, 0)
            return time.time() < cooldown_until
        except Exception:
            return False

    def set_keybind_cooldown(self, settings_key):
        """Set a 1-second cooldown for a keybind and save to file for other processes"""
        try:
            cooldown_time = time.time() + 1.0
            self.keybind_cooldowns[settings_key] = cooldown_time
            
            # Also save to a file that other processes can read
            cooldown_file = KEYBIND_COOLDOWNS_FILE
            cooldown_data = {}
            try:
                if os.path.exists(cooldown_file):
                    with open(cooldown_file, 'r') as f:
                        cooldown_data = json.load(f)
            except:
                pass
            
            cooldown_data[settings_key] = cooldown_time
            
            with open(cooldown_file, 'w') as f:
                json.dump(cooldown_data, f)
        except Exception:
            pass

    

    def create_esp_container(self):
        esp_container = QtWidgets.QWidget()
        esp_layout = QtWidgets.QVBoxLayout()
        esp_layout.setSpacing(6)
        esp_layout.setContentsMargins(6, 6, 6, 6)
        esp_layout.setAlignment(QtCore.Qt.AlignTop)

        esp_label = QtWidgets.QLabel("ESP Settings")
        esp_label.setAlignment(QtCore.Qt.AlignCenter)
        esp_label.setMinimumHeight(20)
        esp_layout.addWidget(esp_label)

        self.esp_rendering_cb = QtWidgets.QCheckBox("Enable ESP")
        self.esp_rendering_cb.setChecked(self.settings.get("esp_rendering", 1) == 1)
        self.esp_rendering_cb.stateChanged.connect(self.save_settings)
        self.esp_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_rendering_cb)

        self.esp_mode_cb = QtWidgets.QComboBox()
        self.esp_mode_cb.addItems(["Enemies Only", "All Players"])
        self.esp_mode_cb.setCurrentIndex(self.settings.get("esp_mode", 1))
        self.esp_mode_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.esp_mode_cb.currentIndexChanged.connect(self.save_settings)
        self.esp_mode_cb.setMinimumHeight(22)
        self.esp_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_mode_cb)

        self.line_rendering_cb = QtWidgets.QCheckBox("Draw Lines")
        self.line_rendering_cb.setChecked(self.settings.get("line_rendering", 1) == 1)
        self.line_rendering_cb.stateChanged.connect(self.save_settings)
        self.line_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.line_rendering_cb)

        self.hp_bar_rendering_cb = QtWidgets.QCheckBox("Draw HP Bars")
        self.hp_bar_rendering_cb.setChecked(self.settings.get("hp_bar_rendering", 1) == 1)
        self.hp_bar_rendering_cb.stateChanged.connect(self.save_settings)
        self.hp_bar_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.hp_bar_rendering_cb)

        self.head_hitbox_rendering_cb = QtWidgets.QCheckBox("Draw Head Hitbox")
        self.head_hitbox_rendering_cb.setChecked(self.settings.get("head_hitbox_rendering", 1) == 1)
        self.head_hitbox_rendering_cb.stateChanged.connect(self.save_settings)
        self.head_hitbox_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.head_hitbox_rendering_cb)

        
        self.box_rendering_cb = QtWidgets.QCheckBox("Draw Boxes")
        self.box_rendering_cb.setChecked(self.settings.get("box_rendering", 1) == 1)
        self.box_rendering_cb.stateChanged.connect(self.save_settings)
        self.box_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.box_rendering_cb)

        self.Bones_cb = QtWidgets.QCheckBox("Draw Bones")
        self.Bones_cb.setChecked(self.settings.get("Bones", 1) == 1)
        self.Bones_cb.stateChanged.connect(self.save_settings)
        self.Bones_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.Bones_cb)

        self.nickname_cb = QtWidgets.QCheckBox("Show Nickname")
        self.nickname_cb.setChecked(self.settings.get("nickname", 1) == 1)
        self.nickname_cb.stateChanged.connect(self.save_settings)
        self.nickname_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.nickname_cb)

        
        self.show_visibility_cb = QtWidgets.QCheckBox("Show Spotted Status")
        self.show_visibility_cb.setChecked(self.settings.get("show_visibility", 1) == 1)
        self.show_visibility_cb.stateChanged.connect(self.save_settings)
        self.show_visibility_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.show_visibility_cb)

        self.weapon_cb = QtWidgets.QCheckBox("Show Weapon")
        self.weapon_cb.setChecked(self.settings.get("weapon", 1) == 1)
        self.weapon_cb.stateChanged.connect(self.save_settings)
        self.weapon_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.weapon_cb)

        self.bomb_esp_cb = QtWidgets.QCheckBox("Bomb ESP")
        self.bomb_esp_cb.setChecked(self.settings.get("bomb_esp", 1) == 1)
        self.bomb_esp_cb.stateChanged.connect(self.save_settings)
        self.bomb_esp_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.bomb_esp_cb)

        # Radar settings
        self.radar_cb = QtWidgets.QCheckBox("Radar")
        self.radar_cb.setChecked(self.settings.get("radar_enabled", 0) == 1)
        self.radar_cb.stateChanged.connect(self.save_settings)
        self.radar_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.radar_cb)

        # Radar size slider
        self.lbl_radar_size = QtWidgets.QLabel(f"Radar Size: ({self.settings.get('radar_size', 200)})")
        esp_layout.addWidget(self.lbl_radar_size)
        self.radar_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radar_size_slider.setRange(100, 400)
        self.radar_size_slider.setValue(self.settings.get('radar_size', 200))
        self.radar_size_slider.valueChanged.connect(self.update_radar_size_label)
        esp_layout.addWidget(self.radar_size_slider)

        # Radar scale slider
        self.lbl_radar_scale = QtWidgets.QLabel(f"Radar Scale: ({self.settings.get('radar_scale', 5.0):.1f})")
        esp_layout.addWidget(self.lbl_radar_scale)
        self.radar_scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radar_scale_slider.setRange(10, 500)  # 1.0 to 50.0 scale
        self.radar_scale_slider.setValue(int(self.settings.get('radar_scale', 5.0) * 10))
        self.radar_scale_slider.valueChanged.connect(self.update_radar_scale_label)
        esp_layout.addWidget(self.radar_scale_slider)

        # Radar Position dropdown
        self.lbl_radar_position = QtWidgets.QLabel("Radar Position:")
        esp_layout.addWidget(self.lbl_radar_position)
        self.radar_position_combo = QtWidgets.QComboBox()
        self.radar_position_combo.addItems([
            "Top Right",
            "Top Left", 
            "Bottom Right",
            "Bottom Left",
            "Bottom Middle",
            "Center Right",
            "Center Left"
        ])
        # Set current position based on settings
        current_position = self.settings.get('radar_position', 'Top Right')
        index = self.radar_position_combo.findText(current_position)
        if index >= 0:
            self.radar_position_combo.setCurrentIndex(index)
        self.radar_position_combo.currentTextChanged.connect(self.on_radar_position_changed)
        self.radar_position_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.radar_position_combo)

        # Center Dot settings
        self.center_dot_cb = QtWidgets.QCheckBox("Draw Center Dot")
        self.center_dot_cb.setChecked(self.settings.get("center_dot", 0) == 1)
        self.center_dot_cb.stateChanged.connect(self.save_settings)
        self.center_dot_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.center_dot_cb)

        # Center Dot Size slider
        self.center_dot_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.center_dot_size_slider.setMinimum(1)
        self.center_dot_size_slider.setMaximum(20)
        self.center_dot_size_slider.setValue(self.settings.get('center_dot_size', 3))
        self.center_dot_size_slider.valueChanged.connect(self.update_center_dot_size_label)
        self.lbl_center_dot_size = QtWidgets.QLabel(f"Center Dot Size: ({self.settings.get('center_dot_size', 3)})")
        self.lbl_center_dot_size.setMinimumHeight(16)
        esp_layout.addWidget(self.lbl_center_dot_size)
        self.center_dot_size_slider.setMinimumHeight(18)
        self.center_dot_size_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.center_dot_size_slider)

        # ESP Toggle Key button moved here
        self.esp_toggle_key_btn = QtWidgets.QPushButton(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")
        self.esp_toggle_key_btn.clicked.connect(lambda: self.record_key('ESPToggleKey', self.esp_toggle_key_btn))
        self.esp_toggle_key_btn.setMinimumHeight(22)
        self.esp_toggle_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_toggle_key_btn)
        self.esp_toggle_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'ESPToggleKey', self.esp_toggle_key_btn)

        esp_container.setLayout(esp_layout)
        esp_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return esp_container

    def create_trigger_container(self):
        trigger_container = QtWidgets.QWidget()
        trigger_layout = QtWidgets.QVBoxLayout()
        trigger_layout.setSpacing(6)
        trigger_layout.setContentsMargins(6, 6, 6, 6)
        trigger_layout.setAlignment(QtCore.Qt.AlignTop)

        trigger_label = QtWidgets.QLabel("Trigger Bot Settings")
        trigger_label.setAlignment(QtCore.Qt.AlignCenter)
        trigger_label.setMinimumHeight(18)
        trigger_layout.addWidget(trigger_label)

        self.trigger_bot_active_cb = QtWidgets.QCheckBox("Enable Trigger Bot")
        self.trigger_bot_active_cb.setChecked(self.settings["trigger_bot_active"] == 1)
        self.trigger_bot_active_cb.stateChanged.connect(self.save_settings)
        self.trigger_bot_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_bot_active_cb)

        
        self.triggerbot_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.triggerbot_delay_slider.setMinimum(0)
        self.triggerbot_delay_slider.setMaximum(1000)
        self.triggerbot_delay_slider.setValue(self.settings.get("triggerbot_delay", 30))
        self.triggerbot_delay_slider.valueChanged.connect(self.update_triggerbot_delay_label)
        self.lbl_delay = QtWidgets.QLabel(f"Triggerbot Delay (ms): ({self.settings.get('triggerbot_delay', 30)})")
        self.lbl_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_delay)
        self.triggerbot_delay_slider.setMinimumHeight(18)
        self.triggerbot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_delay_slider)

        # First Shot Delay Slider
        self.triggerbot_first_shot_delay_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.triggerbot_first_shot_delay_slider.setMinimum(0)
        self.triggerbot_first_shot_delay_slider.setMaximum(1000)
        self.triggerbot_first_shot_delay_slider.setValue(self.settings.get("triggerbot_first_shot_delay", 0))
        self.triggerbot_first_shot_delay_slider.valueChanged.connect(self.update_triggerbot_first_shot_delay_label)
        self.triggerbot_first_shot_delay_slider.setToolTip("Delay before the first shot when trigger key is pressed. Set to 0 for instant shooting, higher values add reaction time delay.")
        self.lbl_first_shot_delay = QtWidgets.QLabel(f"First Shot Delay (ms): ({self.settings.get('triggerbot_first_shot_delay', 0)})")
        self.lbl_first_shot_delay.setMinimumHeight(16)
        trigger_layout.addWidget(self.lbl_first_shot_delay)
        self.triggerbot_first_shot_delay_slider.setMinimumHeight(18)
        self.triggerbot_first_shot_delay_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.triggerbot_first_shot_delay_slider)

        
        self.trigger_key_btn = QtWidgets.QPushButton(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
        self.trigger_key_btn.clicked.connect(lambda: self.record_key('TriggerKey', self.trigger_key_btn))
        self.trigger_key_btn.setMinimumHeight(22)
        self.trigger_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_key_btn)
        self.trigger_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'TriggerKey', self.trigger_key_btn)

        trigger_container.setLayout(trigger_layout)
        trigger_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return trigger_container

    def create_aim_container(self):
        aim_container = QtWidgets.QWidget()
        aim_layout = QtWidgets.QVBoxLayout()
        aim_layout.setSpacing(6)
        aim_layout.setContentsMargins(6, 6, 6, 6)
        aim_layout.setAlignment(QtCore.Qt.AlignTop)

        aim_label = QtWidgets.QLabel("Aim Settings")
        aim_label.setAlignment(QtCore.Qt.AlignCenter)
        aim_label.setMinimumHeight(18)
        aim_layout.addWidget(aim_label)

        self.aim_active_cb = QtWidgets.QCheckBox("Enable Aimbot")
        self.aim_active_cb.setChecked(self.settings.get("aim_active", 0) == 1)
        self.aim_active_cb.stateChanged.connect(self.save_settings)
        self.aim_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_active_cb)

        
        self.radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radius_slider.setMinimum(0)
        self.radius_slider.setMaximum(100)
        self.radius_slider.setValue(self.settings.get("radius", 50))
        self.radius_slider.valueChanged.connect(self.update_radius_label)
        self.lbl_radius = QtWidgets.QLabel(f"Aim Radius: ({self.settings.get('radius', 50)})")
        self.lbl_radius.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_radius)
        self.radius_slider.setMinimumHeight(18)
        self.radius_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.radius_slider)

        # Circle Opacity slider moved here
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(255)
        self.opacity_slider.setValue(self.settings.get("circle_opacity", 16))
        self.opacity_slider.valueChanged.connect(self.update_opacity_label)
        self.lbl_opacity = QtWidgets.QLabel(f"Circle Opacity: ({self.settings.get('circle_opacity', 16)})")
        self.lbl_opacity.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_opacity)
        self.opacity_slider.setMinimumHeight(18)
        self.opacity_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.opacity_slider)

        # Circle Thickness slider
        self.thickness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.thickness_slider.setMinimum(1)
        self.thickness_slider.setMaximum(10)
        self.thickness_slider.setValue(self.settings.get("circle_thickness", 2))
        self.thickness_slider.valueChanged.connect(self.update_thickness_label)
        self.lbl_thickness = QtWidgets.QLabel(f"Circle Thickness: ({self.settings.get('circle_thickness', 2)})")
        self.lbl_thickness.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_thickness)
        self.thickness_slider.setMinimumHeight(18)
        self.thickness_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.thickness_slider)

        # Aim Smoothness slider moved here
        self.smooth_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(500000)
        self.smooth_slider.setValue(self.settings.get("aim_smoothness", 50))
        self.smooth_slider.valueChanged.connect(self.update_smooth_label)
        self.lbl_smooth = QtWidgets.QLabel(f"Aim Smoothness: ({self.settings.get('aim_smoothness', 50)})")
        self.lbl_smooth.setMinimumHeight(16)
        aim_layout.addWidget(self.lbl_smooth)
        self.smooth_slider.setMinimumHeight(18)
        self.smooth_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.smooth_slider)

        # Aim Circle Visibility toggle
        self.aim_circle_visible_cb = QtWidgets.QCheckBox("Show Aim Circle")
        self.aim_circle_visible_cb.setChecked(self.settings.get("aim_circle_visible", 1) == 1)
        self.aim_circle_visible_cb.stateChanged.connect(self.save_settings)
        self.aim_circle_visible_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_circle_visible_cb)

        self.aim_key_btn = QtWidgets.QPushButton(f"AimKey: {self.settings.get('AimKey', 'C')}")
        self.aim_key_btn.clicked.connect(lambda: self.record_key('AimKey', self.aim_key_btn))
        self.aim_key_btn.setMinimumHeight(22)
        self.aim_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_key_btn)
        self.aim_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'AimKey', self.aim_key_btn)

        self.aim_mode_cb = QtWidgets.QComboBox()
        self.aim_mode_cb.addItems(["Body", "Neck", "Head"])
        self.aim_mode_cb.setCurrentIndex(self.settings.get("aim_mode", 2))
        self.aim_mode_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.aim_mode_cb.currentIndexChanged.connect(self.save_settings)
        lbl_aimmode = QtWidgets.QLabel("Aim Mode:")
        lbl_aimmode.setMinimumHeight(16)
        aim_layout.addWidget(lbl_aimmode)
        self.aim_mode_cb.setMinimumHeight(22)
        self.aim_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_mode_cb)

        self.aim_mode_distance_cb = QtWidgets.QComboBox()
        self.aim_mode_distance_cb.addItems(["Closest to Crosshair", "Closest in 3D"])
        self.aim_mode_distance_cb.setCurrentIndex(self.settings.get("aim_mode_distance", 1))
        self.aim_mode_distance_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.aim_mode_distance_cb.currentIndexChanged.connect(self.save_settings)
        lbl_aimdist = QtWidgets.QLabel("Aim Distance Mode:")
        lbl_aimdist.setMinimumHeight(16)
        aim_layout.addWidget(lbl_aimdist)
        self.aim_mode_distance_cb.setMinimumHeight(22)
        self.aim_mode_distance_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_mode_distance_cb)

        try:
            globals()['smooth_slider_max'] = self.smooth_slider.maximum()
        except Exception:
            pass

        
        self.aim_visibility_cb = QtWidgets.QCheckBox("Spotted Check")
        self.aim_visibility_cb.setChecked(self.settings.get("aim_visibility_check", 0) == 1)
        self.aim_visibility_cb.stateChanged.connect(self.save_settings)
        self.aim_visibility_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_visibility_cb)

        
        self.lock_target_cb = QtWidgets.QCheckBox("Lock Target")
        self.lock_target_cb.setChecked(self.settings.get("aim_lock_target", 0) == 1)
        self.lock_target_cb.stateChanged.connect(self.save_settings)
        self.lock_target_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.lock_target_cb)

        # Disable aim when crosshair is on enemy
        self.disable_crosshair_cb = QtWidgets.QCheckBox("Disable Aim When Crosshair on Enemy")
        self.disable_crosshair_cb.setChecked(self.settings.get("aim_disable_when_crosshair_on_enemy", 0) == 1)
        self.disable_crosshair_cb.stateChanged.connect(self.save_settings)
        self.disable_crosshair_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.disable_crosshair_cb)

        aim_container.setLayout(aim_layout)
        aim_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return aim_container

    def create_colors_container(self):
        colors_container = QtWidgets.QWidget()
        colors_layout = QtWidgets.QVBoxLayout()
        colors_layout.setSpacing(6)
        colors_layout.setContentsMargins(6, 6, 6, 6)
        colors_layout.setAlignment(QtCore.Qt.AlignTop)

        colors_label = QtWidgets.QLabel("Color Settings")
        colors_label.setAlignment(QtCore.Qt.AlignCenter)
        colors_label.setMinimumHeight(18)
        colors_layout.addWidget(colors_label)

        # Team Color button
        self.team_color_btn = QtWidgets.QPushButton('Team Color')
        team_hex = self.settings.get('team_color', '#47A76A')
        self.team_color_btn.setStyleSheet(f'background-color: {team_hex}; color: white;')
        self.team_color_btn.clicked.connect(lambda: self.pick_color('team_color', self.team_color_btn))
        self.team_color_btn.setMinimumHeight(28)
        self.team_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.team_color_btn)

        # Enemy Color button
        self.enemy_color_btn = QtWidgets.QPushButton('Enemy Color')
        enemy_hex = self.settings.get('enemy_color', '#C41E3A')
        self.enemy_color_btn.setStyleSheet(f'background-color: {enemy_hex}; color: white;')
        self.enemy_color_btn.clicked.connect(lambda: self.pick_color('enemy_color', self.enemy_color_btn))
        self.enemy_color_btn.setMinimumHeight(28)
        self.enemy_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.enemy_color_btn)

        # Aim Circle Color button
        self.aim_circle_color_btn = QtWidgets.QPushButton('Aim Circle Color')
        aim_hex = self.settings.get('aim_circle_color', '#FF0000')
        self.aim_circle_color_btn.setStyleSheet(f'background-color: {aim_hex}; color: white;')
        self.aim_circle_color_btn.clicked.connect(lambda: self.pick_color('aim_circle_color', self.aim_circle_color_btn))
        self.aim_circle_color_btn.setMinimumHeight(28)
        self.aim_circle_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.aim_circle_color_btn)

        # Center Dot Color button
        self.center_dot_color_btn = QtWidgets.QPushButton('Center Dot Color')
        center_dot_hex = self.settings.get('center_dot_color', '#FFFFFF')
        self.center_dot_color_btn.setStyleSheet(f'background-color: {center_dot_hex}; color: black;')
        self.center_dot_color_btn.clicked.connect(lambda: self.pick_color('center_dot_color', self.center_dot_color_btn))
        self.center_dot_color_btn.setMinimumHeight(28)
        self.center_dot_color_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.center_dot_color_btn)

        # Rainbow FOV Circle toggle
        self.rainbow_fov_cb = QtWidgets.QCheckBox("Rainbow FOV Circle")
        self.rainbow_fov_cb.setChecked(self.settings.get('rainbow_fov', 0) == 1)
        self.rainbow_fov_cb.stateChanged.connect(self.save_settings)
        self.rainbow_fov_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.rainbow_fov_cb)

        # Rainbow Center Dot toggle
        self.rainbow_center_dot_cb = QtWidgets.QCheckBox("Rainbow Center Dot")
        self.rainbow_center_dot_cb.setChecked(self.settings.get('rainbow_center_dot', 0) == 1)
        self.rainbow_center_dot_cb.stateChanged.connect(self.save_settings)
        self.rainbow_center_dot_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.rainbow_center_dot_cb)

        # Theme dropdown
        self.theme_combo = QtWidgets.QComboBox()
        for theme in THEMES:
            self.theme_combo.addItem(theme, theme)
        current_theme = self.settings.get("theme", "dark_red.xml")
        theme_idx = 0
        for i in range(self.theme_combo.count()):
            if str(self.theme_combo.itemData(i)) == str(current_theme):
                theme_idx = i
                break
        self.theme_combo.setCurrentIndex(theme_idx)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)

        lbl_theme = QtWidgets.QLabel("Theme:")
        lbl_theme.setMinimumHeight(16)
        colors_layout.addWidget(lbl_theme)
        self.theme_combo.setMinimumHeight(22)
        self.theme_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        colors_layout.addWidget(self.theme_combo)

        colors_container.setLayout(colors_layout)
        colors_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return colors_container

    def create_misc_container(self):
        misc_container = QtWidgets.QWidget()
        misc_layout = QtWidgets.QVBoxLayout()
        misc_layout.setSpacing(6)
        misc_layout.setContentsMargins(6, 6, 6, 6)
        misc_layout.setAlignment(QtCore.Qt.AlignTop)

        misc_label = QtWidgets.QLabel("Miscellaneous")
        misc_label.setAlignment(QtCore.Qt.AlignCenter)
        misc_label.setMinimumHeight(18)
        misc_layout.addWidget(misc_label)

        # Menu toggle key button
        self.menu_key_btn = QtWidgets.QPushButton(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'M')}")
        self.menu_key_btn.clicked.connect(lambda: self.record_key('MenuToggleKey', self.menu_key_btn))
        self.menu_key_btn.setMinimumHeight(22)
        self.menu_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.menu_key_btn)
        self.menu_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'MenuToggleKey', self.menu_key_btn)

        self.low_cpu_cb = QtWidgets.QCheckBox("Low CPU Mode (Performance Mode)")
        self.low_cpu_cb.setChecked(self.settings.get('low_cpu', 0) == 1)
        self.low_cpu_cb.stateChanged.connect(self.on_low_cpu_changed)
        self.low_cpu_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.low_cpu_cb)

        # FPS Limit slider
        self.lbl_fps_limit = QtWidgets.QLabel(f"FPS Limit: ({self.settings.get('fps_limit', 60)})")
        self.lbl_fps_limit.setMinimumHeight(16)
        misc_layout.addWidget(self.lbl_fps_limit)
        
        self.fps_limit_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.fps_limit_slider.setMinimum(10)
        self.fps_limit_slider.setMaximum(100)
        self.fps_limit_slider.setValue(self.settings.get('fps_limit', 60))
        self.fps_limit_slider.valueChanged.connect(self.update_fps_limit_label)
        self.fps_limit_slider.setMinimumHeight(18)
        self.fps_limit_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.fps_limit_slider)

        # Bhop toggle checkbox
        self.bhop_cb = QtWidgets.QCheckBox("Bhop")
        self.bhop_cb.setChecked(self.settings.get("bhop_enabled", 0) == 1)
        self.bhop_cb.stateChanged.connect(self.on_bhop_changed)
        self.bhop_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.bhop_cb)

        # Bhop key button
        self.bhop_key_btn = QtWidgets.QPushButton(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")
        self.bhop_key_btn.clicked.connect(lambda: self.record_key('BhopKey', self.bhop_key_btn))
        self.bhop_key_btn.setMinimumHeight(22)
        self.bhop_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.bhop_key_btn)
        self.bhop_key_btn.mousePressEvent = lambda event: self.handle_keybind_mouse_event(event, 'BhopKey', self.bhop_key_btn)

        self.terminate_btn = QtWidgets.QPushButton("Exit Script (Hold ESC or click here)")
        self.terminate_btn.setToolTip("Close Script")
        self.terminate_btn.clicked.connect(self.on_terminate_clicked)
        self.terminate_btn.setMinimumHeight(22)
        self.terminate_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.reset_btn = QtWidgets.QPushButton("Reset Config")
        self.reset_btn.setToolTip("Restore configuration to default values")
        self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.reset_btn.setMinimumHeight(22)
        self.reset_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.reset_btn)

        misc_layout.addWidget(self.terminate_btn)

        misc_container.setLayout(misc_layout)
        misc_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return misc_container

    def on_bhop_changed(self):
        """Handle bhop toggle change"""
        try:
            self.settings["bhop_enabled"] = 1 if self.bhop_cb.isChecked() else 0
            save_settings(self.settings)
        except Exception:
            pass

    def handle_keybind_mouse_event(self, event, key_name, btn):
        if event.button() == QtCore.Qt.RightButton:
            # Right click sets to NONE
            self.settings[key_name] = 'NONE'
            btn.setText(f"{btn.text().split(':')[0]}: NONE")
            self.save_settings()
        else:
            # For left clicks, let the normal button behavior handle it
            QtWidgets.QPushButton.mousePressEvent(btn, event)

    def on_low_cpu_changed(self):
        """Handle low CPU mode toggle and lock/unlock FPS slider accordingly"""
        try:
            low_cpu_enabled = self.low_cpu_cb.isChecked()
            self.settings["low_cpu"] = 1 if low_cpu_enabled else 0
            
            if low_cpu_enabled:
                # Lock FPS slider at 10 FPS when low CPU mode is enabled
                self.fps_limit_slider.setValue(10)
                self.fps_limit_slider.setEnabled(False)
                self.settings["fps_limit"] = 10
                self.lbl_fps_limit.setText("FPS Limit: (10) - Locked by Low CPU Mode")
            else:
                # Unlock FPS slider when low CPU mode is disabled
                self.fps_limit_slider.setEnabled(True)
                current_fps = self.settings.get('fps_limit', 60)
                self.lbl_fps_limit.setText(f"FPS Limit: ({current_fps})")
            
            save_settings(self.settings)
        except Exception:
            pass

    def initialize_fps_slider_state(self):
        """Initialize FPS slider state based on current low CPU mode setting"""
        try:
            low_cpu_enabled = self.settings.get('low_cpu', 0) == 1
            
            if low_cpu_enabled:
                # Lock FPS slider at 10 FPS if low CPU mode is already enabled
                self.fps_limit_slider.setValue(10)
                self.fps_limit_slider.setEnabled(False)
                self.settings["fps_limit"] = 10
                self.lbl_fps_limit.setText("FPS Limit: (10) - Locked by Low CPU Mode")
                save_settings(self.settings)
            else:
                # Ensure FPS slider is enabled if low CPU mode is disabled
                self.fps_limit_slider.setEnabled(True)
                current_fps = self.settings.get('fps_limit', 60)
                self.lbl_fps_limit.setText(f"FPS Limit: ({current_fps})")
        except Exception:
            pass

    def apply_topmost(self):
        """Always apply topmost flag to keep window on top"""
        flags = self.windowFlags()
        flags |= QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def on_theme_changed(self):
        
        try:
            sel = self.theme_combo.itemData(self.theme_combo.currentIndex())
            if sel:
                self.settings["theme"] = sel
                save_settings(self.settings)
                app = QtWidgets.QApplication.instance()
                if app is not None:
                    try:
                        apply_stylesheet(app, theme=sel)
                    except Exception:
                        pass
        except Exception:
            pass

    
    def on_terminate_clicked(self):
        try:
            
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('terminate')
        except Exception:
            pass
        try:
            # Clean up keybind cooldowns file
            if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                os.remove(KEYBIND_COOLDOWNS_FILE)
        except Exception:
            pass
        try:
            
            app = QtWidgets.QApplication.instance()
            if app is not None:
                app.quit()
            else:
                self.close()
        except Exception:
            pass

    def on_reset_clicked(self):
        """Restore DEFAULT_SETTINGS and update every configurable UI element in one atomic operation.

        This blocks widget signals while values are applied to avoid incremental saves
        or partial state, persists the new config once, applies the theme and topmost
        setting, then unblocks signals and persists again as a final confirmation.
        """
        
        widget_names = [
            'esp_rendering_cb', 'esp_mode_cb', 'line_rendering_cb', 'hp_bar_rendering_cb',
            'head_hitbox_rendering_cb', 'box_rendering_cb', 'Bones_cb', 'nickname_cb', 'show_visibility_cb', 'weapon_cb', 'bomb_esp_cb',
            'center_dot_cb', 'trigger_bot_active_cb', 'aim_active_cb', 'aim_circle_visible_cb', 'radius_slider', 'opacity_slider', 'thickness_slider',
            'smooth_slider', 'center_dot_size_slider',
            'aim_visibility_cb', 'lock_target_cb', 'aim_key_btn', 'trigger_key_btn', 'menu_key_btn', 'bhop_key_btn', 'theme_combo',
            'team_color_btn', 'enemy_color_btn', 'aim_circle_color_btn', 'center_dot_color_btn', 'rainbow_fov_cb', 'rainbow_center_dot_cb',
            'low_cpu_cb', 'fps_limit_slider', 'radar_position_combo'
        ]
        widgets = [getattr(self, name, None) for name in widget_names]

        try:
            
            self.settings = DEFAULT_SETTINGS.copy()
            save_settings(self.settings)

            
            for w in widgets:
                try:
                    if w is not None:
                        w.blockSignals(True)
                except Exception:
                    pass

            
            try:
                if getattr(self, 'esp_rendering_cb', None) is not None:
                    self.esp_rendering_cb.setChecked(self.settings.get('esp_rendering', 1) == 1)
                if getattr(self, 'esp_mode_cb', None) is not None:
                    self.esp_mode_cb.setCurrentIndex(self.settings.get('esp_mode', 1))

                
                mapping = {
                    'line_rendering_cb': 'line_rendering',
                    'hp_bar_rendering_cb': 'hp_bar_rendering',
                    'head_hitbox_rendering_cb': 'head_hitbox_rendering',
                    'box_rendering_cb': 'box_rendering',
                    'Bones_cb': 'Bones',
                    'nickname_cb': 'nickname',
                    'show_visibility_cb': 'show_visibility',
                    'aim_visibility_cb': 'aim_visibility_check',
                    'lock_target_cb': 'aim_lock_target',
                    'weapon_cb': 'weapon',
                    'bomb_esp_cb': 'bomb_esp',
                    'radar_cb': 'radar_enabled',
                    'trigger_bot_active_cb': 'trigger_bot_active',
                    'aim_active_cb': 'aim_active',
                    'aim_circle_visible_cb': 'aim_circle_visible',
                    'rainbow_fov_cb': 'rainbow_fov', 'low_cpu_cb': 'low_cpu'
                }
                for cb_name, key in mapping.items():
                    cb = getattr(self, cb_name, None)
                    if cb is not None:
                        cb.setChecked(self.settings.get(key, 0) == 1)

                
                if getattr(self, 'radius_slider', None) is not None:
                    self.radius_slider.setValue(self.settings.get('radius', 50))
                if getattr(self, 'opacity_slider', None) is not None:
                    self.opacity_slider.setValue(self.settings.get('circle_opacity', 16))
                if getattr(self, 'thickness_slider', None) is not None:
                    self.thickness_slider.setValue(self.settings.get('circle_thickness', 2))
                if getattr(self, 'smooth_slider', None) is not None:
                    self.smooth_slider.setValue(self.settings.get('aim_smoothness', 50))
                if getattr(self, 'triggerbot_delay_slider', None) is not None:
                    self.triggerbot_delay_slider.setValue(self.settings.get('triggerbot_delay', 30))
                
                # Radar sliders
                if getattr(self, 'radar_size_slider', None) is not None:
                    self.radar_size_slider.setValue(self.settings.get('radar_size', 200))
                if getattr(self, 'radar_scale_slider', None) is not None:
                    self.radar_scale_slider.setValue(int(self.settings.get('radar_scale', 5.0) * 10))
                if getattr(self, 'radar_position_combo', None) is not None:
                    position = self.settings.get('radar_position', 'Top Right')
                    index = self.radar_position_combo.findText(position)
                    if index >= 0:
                        self.radar_position_combo.setCurrentIndex(index)
                if getattr(self, 'triggerbot_first_shot_delay_slider', None) is not None:
                    self.triggerbot_first_shot_delay_slider.setValue(self.settings.get('triggerbot_first_shot_delay', 0))
                if getattr(self, 'center_dot_size_slider', None) is not None:
                    self.center_dot_size_slider.setValue(self.settings.get('center_dot_size', 3))

                # Update all slider labels after setting values
                try:
                    if hasattr(self, 'update_radius_label'):
                        self.update_radius_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_opacity_label'):
                        self.update_opacity_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_thickness_label'):
                        self.update_thickness_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_smooth_label'):
                        self.update_smooth_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_triggerbot_delay_label'):
                        self.update_triggerbot_delay_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_triggerbot_first_shot_delay_label'):
                        self.update_triggerbot_first_shot_delay_label()
                except Exception:
                    pass
                try:
                    if hasattr(self, 'update_center_dot_size_label'):
                        self.update_center_dot_size_label()
                except Exception:
                    pass

                
                if getattr(self, 'aim_key_btn', None) is not None:
                    self.aim_key_btn.setText(f"AimKey: {self.settings.get('AimKey', 'C')}")
                if getattr(self, 'trigger_key_btn', None) is not None:
                    self.trigger_key_btn.setText(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
                if getattr(self, 'menu_key_btn', None) is not None:
                    self.menu_key_btn.setText(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'F8')}")
                if getattr(self, 'bhop_key_btn', None) is not None:
                    self.bhop_key_btn.setText(f"BhopKey: {self.settings.get('BhopKey', 'SPACE')}")

                if getattr(self, 'esp_toggle_key_btn', None) is not None:
                    self.esp_toggle_key_btn.setText(f"ESP Toggle: {self.settings.get('ESPToggleKey', 'NONE')}")

                
                if getattr(self, 'theme_combo', None) is not None:
                    theme = self.settings.get('theme', DEFAULT_SETTINGS.get('theme'))
                    for i in range(self.theme_combo.count()):
                        if str(self.theme_combo.itemData(i)) == str(theme):
                            self.theme_combo.setCurrentIndex(i)
                            break

                
                try:
                    if getattr(self, 'team_color_btn', None) is not None:
                        team_hex = self.settings.get('team_color', DEFAULT_SETTINGS.get('team_color'))
                        self.team_color_btn.setStyleSheet(f'background-color: {team_hex}; color: white;')
                    if getattr(self, 'enemy_color_btn', None) is not None:
                        enemy_hex = self.settings.get('enemy_color', DEFAULT_SETTINGS.get('enemy_color'))
                        self.enemy_color_btn.setStyleSheet(f'background-color: {enemy_hex}; color: white;')
                    if getattr(self, 'aim_circle_color_btn', None) is not None:
                        aim_hex = self.settings.get('aim_circle_color', DEFAULT_SETTINGS.get('aim_circle_color'))
                        self.aim_circle_color_btn.setStyleSheet(f'background-color: {aim_hex}; color: white;')
                except Exception:
                    pass

                
                try:
                    app = QtWidgets.QApplication.instance()
                    if app is not None:
                        try:
                            apply_stylesheet(app, theme=self.settings.get('theme', DEFAULT_SETTINGS.get('theme')))
                        except Exception:
                            pass
                except Exception:
                    pass

                # Always apply topmost (no longer user-configurable)
                try:
                    self.apply_topmost()
                except Exception:
                    pass

            except Exception as e:
                pass
        finally:
            
            for w in widgets:
                try:
                    if w is not None:
                        w.blockSignals(False)
                except Exception:
                    pass
            try:
                # Initialize FPS slider state after reset
                self.initialize_fps_slider_state()
                save_settings(self.settings)
            except Exception:
                pass

    def save_settings(self):
        
        self.settings["esp_rendering"] = 1 if self.esp_rendering_cb.isChecked() else 0
        self.settings["esp_mode"] = self.esp_mode_cb.currentIndex()
        self.settings["line_rendering"] = 1 if self.line_rendering_cb.isChecked() else 0
        self.settings["hp_bar_rendering"] = 1 if self.hp_bar_rendering_cb.isChecked() else 0
        self.settings["head_hitbox_rendering"] = 1 if self.head_hitbox_rendering_cb.isChecked() else 0
        self.settings["Bones"] = 1 if self.Bones_cb.isChecked() else 0
        
        try:
            self.settings["box_rendering"] = 1 if getattr(self, 'box_rendering_cb', None) and self.box_rendering_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["rainbow_fov"] = 1 if getattr(self, 'rainbow_fov_cb', None) and self.rainbow_fov_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["center_dot"] = 1 if getattr(self, 'center_dot_cb', None) and self.center_dot_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["rainbow_center_dot"] = 1 if getattr(self, 'rainbow_center_dot_cb', None) and self.rainbow_center_dot_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["low_cpu"] = 1 if getattr(self, 'low_cpu_cb', None) and self.low_cpu_cb.isChecked() else 0
        except Exception:
            pass
        self.settings["nickname"] = 1 if self.nickname_cb.isChecked() else 0
        
        try:
            self.settings["show_visibility"] = 1 if getattr(self, 'show_visibility_cb', None) and self.show_visibility_cb.isChecked() else 0
        except Exception:
            self.settings["show_visibility"] = self.settings.get("show_visibility", 1)
        self.settings["weapon"] = 1 if self.weapon_cb.isChecked() else 0
        self.settings["bomb_esp"] = 1 if self.bomb_esp_cb.isChecked() else 0
        self.settings["radar_enabled"] = 1 if self.radar_cb.isChecked() else 0
        self.settings["aim_active"] = 1 if self.aim_active_cb.isChecked() else 0
        
        # Aim circle visibility setting
        try:
            self.settings["aim_circle_visible"] = 1 if getattr(self, 'aim_circle_visible_cb', None) and self.aim_circle_visible_cb.isChecked() else 0
        except Exception:
            pass

        
        self.settings["radius"] = self.radius_slider.value()
        
        # Radar settings
        if hasattr(self, 'radar_size_slider'):
            self.settings["radar_size"] = self.radar_size_slider.value()
        if hasattr(self, 'radar_scale_slider'):
            self.settings["radar_scale"] = self.radar_scale_slider.value() / 10.0
        if hasattr(self, 'radar_position_combo'):
            self.settings["radar_position"] = self.radar_position_combo.currentText()
        
        # FPS limit setting
        if hasattr(self, 'fps_limit_slider'):
            self.settings["fps_limit"] = self.fps_limit_slider.value()

    

        
        if getattr(self, "triggerbot_delay_slider", None):
            self.settings["triggerbot_delay"] = self.triggerbot_delay_slider.value()

        if getattr(self, "triggerbot_first_shot_delay_slider", None):
            self.settings["triggerbot_first_shot_delay"] = self.triggerbot_first_shot_delay_slider.value()

        if getattr(self, "center_dot_size_slider", None):
            self.settings["center_dot_size"] = self.center_dot_size_slider.value()

        
        try:
            if getattr(self, "aim_key_btn", None) is not None:
                
                text = self.aim_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                else:
                    val = text.strip()
                if val:
                    self.settings["AimKey"] = val
        except Exception:
            pass

        self.settings["aim_mode"] = self.aim_mode_cb.currentIndex()
        self.settings["aim_mode_distance"] = self.aim_mode_distance_cb.currentIndex()

        
        self.settings["trigger_bot_active"] = 1 if self.trigger_bot_active_cb.isChecked() else 0

        
        
        try:
            if getattr(self, 'trigger_key_btn', None) is not None:
                text = self.trigger_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["TriggerKey"] = val
        except Exception:
            pass

        
        self.settings["circle_opacity"] = self.opacity_slider.value()

        
        self.settings["circle_thickness"] = self.thickness_slider.value()

        # Topmost is always enabled (no longer user-configurable)
        try:
            self.settings["topmost"] = 1
        except Exception:
            pass

        
        try:
            val = getattr(self, "menu_key_combo", None)
            if val is not None:
                self.settings["MenuToggleKey"] = val.itemData(val.currentIndex())
        except Exception:
            pass

        
        try:
            val = getattr(self, "theme_combo", None)
            if val is not None:
                self.settings["theme"] = val.itemData(val.currentIndex())
        except Exception:
            pass

        
        try:
            self.settings["aim_smoothness"] = self.smooth_slider.value()
        except Exception:
            pass
        
        try:
            self.settings["aim_visibility_check"] = 1 if self.aim_visibility_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["aim_lock_target"] = 1 if getattr(self, 'lock_target_cb', None) and self.lock_target_cb.isChecked() else 0
        except Exception:
            pass
        
        try:
            self.settings["aim_disable_when_crosshair_on_enemy"] = 1 if getattr(self, 'disable_crosshair_cb', None) and self.disable_crosshair_cb.isChecked() else 0
        except Exception:
            pass
        
        # Save bhop key setting
        try:
            if getattr(self, 'bhop_key_btn', None) is not None:
                text = self.bhop_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["BhopKey"] = val
        except Exception:
            pass
        
        try:
            pass
        except Exception:
            pass
        save_settings(self.settings)

    def record_key(self, settings_key: str, btn: QtWidgets.QPushButton):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Press a key or mouse button')
        dialog.setModal(False)  # Changed to non-modal to keep overlay visible
        dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Dialog)  # Stay on top
        lbl = QtWidgets.QLabel('Press desired key or mouse button now...')
        v = QtWidgets.QVBoxLayout(dialog)
        v.addWidget(lbl)

        timer = QtCore.QTimer(dialog)
        dialog_cancelled = False

        def on_dialog_close():
            nonlocal dialog_cancelled
            dialog_cancelled = True
            timer.stop()

        # Override close event to handle X button clicks properly
        def closeEvent(event):
            on_dialog_close()
            QtWidgets.QDialog.closeEvent(dialog, event)

        dialog.closeEvent = closeEvent

        def check():
            if dialog_cancelled:
                return
                
            # Check mouse buttons first
            mouse_buttons = [
                (0x01, 'LMB'),    # Left mouse button
                (0x02, 'RMB'),    # Right mouse button  
                (0x04, 'MMB'),    # Middle mouse button
                (0x05, 'MOUSE4'), # X1 mouse button
                (0x06, 'MOUSE5'), # X2 mouse button
            ]
            
            for code, name in mouse_buttons:
                try:
                    if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                        # Skip left mouse button if dialog might be getting closed
                        if code == 0x01:
                            # Add a small delay to see if this is a window close action
                            QtCore.QTimer.singleShot(50, lambda: check_delayed_mouse(code, name))
                            return
                        else:
                            self.settings[settings_key] = name
                            save_settings(self.settings)
                            
                            # Set cooldown for this keybind (1 second)
                            self.set_keybind_cooldown(settings_key)
                            
                            short = settings_key
                            if '_' in settings_key:
                                short = settings_key.split('_')[0]
                            btn.setText(f"{short.capitalize()}: {name}")
                            timer.stop()
                            dialog.accept()
                            return
                except Exception:
                    continue
            
            # Check keyboard keys
            for code in range(0x08, 0xFF):
                try:
                    if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                        # Skip mouse buttons since we already checked them
                        if code in [0x01, 0x02, 0x04, 0x05, 0x06]:
                            continue
                            
                        try:
                            mods = []
                            
                            if (win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_LCONTROL', 0xA2)) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_RCONTROL', 0xA3)) & 0x8000) != 0:
                                mods.append('CTRL')
                            
                            if (win32api.GetAsyncKeyState(win32con.VK_MENU) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_LMENU', 0xA4)) & 0x8000) != 0 or (win32api.GetAsyncKeyState(getattr(win32con, 'VK_RMENU', 0xA5)) & 0x8000) != 0:
                                mods.append('ALT')
                            
                            if (win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000) != 0:
                                mods.append('SHIFT')

                            # Enhanced key mapping
                            vk_name_map = {
                                getattr(win32con, 'VK_ESCAPE', 0x1B): 'ESC',
                                getattr(win32con, 'VK_RETURN', 0x0D): 'ENTER',
                                getattr(win32con, 'VK_SPACE', 0x20): 'SPACE',
                                getattr(win32con, 'VK_TAB', 0x09): 'TAB',
                                getattr(win32con, 'VK_LEFT', 0x25): 'LEFT',
                                getattr(win32con, 'VK_UP', 0x26): 'UP',
                                getattr(win32con, 'VK_RIGHT', 0x27): 'RIGHT',
                                getattr(win32con, 'VK_DOWN', 0x28): 'DOWN',
                                getattr(win32con, 'VK_BACK', 0x08): 'BACKSPACE',
                                getattr(win32con, 'VK_DELETE', 0x2E): 'DELETE',
                                getattr(win32con, 'VK_INSERT', 0x2D): 'INSERT',
                                getattr(win32con, 'VK_HOME', 0x24): 'HOME',
                                getattr(win32con, 'VK_END', 0x23): 'END',
                                getattr(win32con, 'VK_PRIOR', 0x21): 'PAGEUP',
                                getattr(win32con, 'VK_NEXT', 0x22): 'PAGEDOWN',
                                getattr(win32con, 'VK_LSHIFT', 0xA0): 'LSHIFT',
                                getattr(win32con, 'VK_RSHIFT', 0xA1): 'RSHIFT',
                                getattr(win32con, 'VK_LCONTROL', 0xA2): 'LCTRL',
                                getattr(win32con, 'VK_RCONTROL', 0xA3): 'RCTRL',
                                getattr(win32con, 'VK_LMENU', 0xA4): 'LALT',
                                getattr(win32con, 'VK_RMENU', 0xA5): 'RALT',
                                getattr(win32con, 'VK_CAPITAL', 0x14): 'CAPS',
                                getattr(win32con, 'VK_NUMPAD0', 0x60): 'NUMPAD0',
                                getattr(win32con, 'VK_NUMPAD1', 0x61): 'NUMPAD1',
                                getattr(win32con, 'VK_NUMPAD2', 0x62): 'NUMPAD2',
                                getattr(win32con, 'VK_NUMPAD3', 0x63): 'NUMPAD3',
                                getattr(win32con, 'VK_NUMPAD4', 0x64): 'NUMPAD4',
                                getattr(win32con, 'VK_NUMPAD5', 0x65): 'NUMPAD5',
                                getattr(win32con, 'VK_NUMPAD6', 0x66): 'NUMPAD6',
                                getattr(win32con, 'VK_NUMPAD7', 0x67): 'NUMPAD7',
                                getattr(win32con, 'VK_NUMPAD8', 0x68): 'NUMPAD8',
                                getattr(win32con, 'VK_NUMPAD9', 0x69): 'NUMPAD9',
                                getattr(win32con, 'VK_MULTIPLY', 0x6A): 'MULTIPLY',
                                getattr(win32con, 'VK_ADD', 0x6B): 'ADD',
                                getattr(win32con, 'VK_SUBTRACT', 0x6D): 'SUBTRACT',
                                getattr(win32con, 'VK_DECIMAL', 0x6E): 'DECIMAL',
                                getattr(win32con, 'VK_DIVIDE', 0x6F): 'DIVIDE',
                                getattr(win32con, 'VK_SNAPSHOT', 0x2C): 'PRINTSCREEN',
                                getattr(win32con, 'VK_SCROLL', 0x91): 'SCROLLLOCK',
                                getattr(win32con, 'VK_PAUSE', 0x13): 'PAUSE',
                                getattr(win32con, 'VK_NUMLOCK', 0x90): 'NUMLOCK',
                                getattr(win32con, 'VK_LWIN', 0x5B): 'LWIN',
                                getattr(win32con, 'VK_RWIN', 0x5C): 'RWIN',
                                getattr(win32con, 'VK_APPS', 0x5D): 'APPS',
                                # OEM keys (symbols)
                                getattr(win32con, 'VK_OEM_1', 0xBA): 'SEMICOLON',
                                getattr(win32con, 'VK_OEM_PLUS', 0xBB): 'EQUALS',
                                getattr(win32con, 'VK_OEM_COMMA', 0xBC): 'COMMA',
                                getattr(win32con, 'VK_OEM_MINUS', 0xBD): 'MINUS',
                                getattr(win32con, 'VK_OEM_PERIOD', 0xBE): 'PERIOD',
                                getattr(win32con, 'VK_OEM_2', 0xBF): 'SLASH',
                                getattr(win32con, 'VK_OEM_3', 0xC0): 'GRAVE',
                                getattr(win32con, 'VK_OEM_4', 0xDB): 'LBRACKET',
                                getattr(win32con, 'VK_OEM_5', 0xDC): 'BACKSLASH',
                                getattr(win32con, 'VK_OEM_6', 0xDD): 'RBRACKET',
                                getattr(win32con, 'VK_OEM_7', 0xDE): 'QUOTE',
                            }
                            
                            base = ''
                            if 0x30 <= code <= 0x5A:
                                base = chr(code)
                            elif 0x70 <= code <= 0x87:
                                base = f'F{code - 0x6F}'
                            else:
                                base = vk_name_map.get(code, '')
                                if not base:
                                    # Handle generic cases
                                    if code == win32con.VK_MENU:
                                        base = 'ALT'
                                    elif code == win32con.VK_CONTROL:
                                        base = 'CTRL'
                                    elif code == win32con.VK_SHIFT:
                                        base = 'SHIFT'
                                    elif code == getattr(win32con, 'VK_CAPITAL', 0x14):
                                        base = 'CAPS'
                                    else:
                                        base = str(code)

                            # Build final key string
                            parts = []
                            for m in mods:
                                if m not in parts:
                                    parts.append(m)
                            if base and base.upper() not in parts:
                                parts.append(str(base).upper())
                            if parts:
                                val = '+'.join(parts)
                            else:
                                val = str(base).upper()
                        except Exception:
                            # Fallback key naming
                            if 0x30 <= code <= 0x5A:
                                val = chr(code)
                            elif 0x70 <= code <= 0x87:
                                val = f'F{code - 0x6F}'
                            else:
                                val = str(code)

                        # Save the key and track cooldown
                        self.settings[settings_key] = val
                        save_settings(self.settings)
                        
                        # Set cooldown for this keybind (1 second)
                        self.set_keybind_cooldown(settings_key)
                        
                        short = settings_key
                        if '_' in settings_key:
                            short = settings_key.split('_')[0]
                        btn.setText(f"{short.capitalize()}: {val}")
                        timer.stop()
                        dialog.accept()
                        return
                except Exception:
                    continue

        def check_delayed_mouse(code, name):
            # If dialog was cancelled, don't process the mouse click
            if dialog_cancelled:
                return
            
            # Double-check if the mouse button is still pressed after delay
            if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                self.settings[settings_key] = name
                save_settings(self.settings)
                
                # Set cooldown for this keybind (1 second)
                self.set_keybind_cooldown(settings_key)
                
                short = settings_key
                if '_' in settings_key:
                    short = settings_key.split('_')[0]
                btn.setText(f"{short.capitalize()}: {name}")
                timer.stop()
                dialog.accept()

        timer.timeout.connect(check)
        timer.start(20)
        dialog.show()  # Changed from dialog.exec() to dialog.show() for non-modal

    def pick_color(self, settings_key: str, btn: QtWidgets.QPushButton):
        init = QtGui.QColor(self.settings.get(settings_key, '#FFFFFF'))
        col = QtWidgets.QColorDialog.getColor(init, self, f'Choose {settings_key}')
        if col.isValid():
            hexc = col.name()
            self.settings[settings_key] = hexc
            save_settings(self.settings)
            btn.setStyleSheet(f'background-color: {hexc}; color: white;')

    def check_menu_toggle(self):
        
        try:
            
            if getattr(self, "_menu_toggle_ignore_until", 0) > time.time():
                return
            key = self.settings.get("MenuToggleKey", "M")
            
            if not key or str(key).upper() == "NONE":
                return
                
            # Check if MenuToggleKey is on cooldown
            if self.is_keybind_on_cooldown("MenuToggleKey"):
                return
                
            vk = key_str_to_vk(key)
            pressed = (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
            if pressed and not self.menu_toggle_pressed:
                
                if self.isVisible():
                    self.hide()
                    self._manually_hidden = True  # User manually hid the window
                    self._was_visible = False  # Update visibility tracking
                else:
                    
                    try:
                        self.apply_topmost()
                    except Exception:
                        pass
                    self.show()
                    self._manually_hidden = False  # User manually showed the window
                    self._was_visible = True  # Update visibility tracking
                self.menu_toggle_pressed = True
            elif not pressed:
                self.menu_toggle_pressed = False
            # ESP toggle handling: separate key that flips esp_rendering
            try:
                esp_key = self.settings.get('ESPToggleKey', 'NONE')
                if esp_key and str(esp_key).upper() != 'NONE':
                    # Check if ESPToggleKey is on cooldown
                    if not self.is_keybind_on_cooldown("ESPToggleKey"):
                        esp_vk = key_str_to_vk(esp_key)
                        esp_pressed = (win32api.GetAsyncKeyState(esp_vk) & 0x8000) != 0 if esp_vk != 0 else False
                        if esp_pressed and not getattr(self, 'esp_toggle_pressed', False):
                            # flip setting
                            cur = 1 if self.settings.get('esp_rendering', 1) == 1 else 0
                            self.settings['esp_rendering'] = 0 if cur == 1 else 1
                            save_settings(self.settings)
                            # update UI checkbox if present
                            try:
                                if getattr(self, 'esp_rendering_cb', None) is not None:
                                    self.esp_rendering_cb.setChecked(self.settings['esp_rendering'] == 1)
                            except Exception:
                                pass
                            self.esp_toggle_pressed = True
                        elif not esp_pressed:
                            self.esp_toggle_pressed = False
            except Exception:
                pass
        except Exception:
            pass

    def _check_escape_hold(self):
        """Poll ESC state; if held continuously for 4 seconds, trigger termination.

        This uses GetAsyncKeyState high-bit detection so it responds while the key is held.
        """
        try:
            
            app = QtWidgets.QApplication.instance()
            if app is not None:
                widget = app.focusWidget()
                
                if widget is not None and widget.metaObject().className() in ('QLineEdit', 'QTextEdit', 'QPlainTextEdit'):
                    self._escape_hold_start = 0
                    return

            
            if (win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0:
                if self._escape_hold_start == 0:
                    self._escape_hold_start = time.time()
                else:
                    if time.time() - self._escape_hold_start >= 1.20:
                        
                        try:
                            self.on_terminate_clicked()
                        except Exception:
                            pass
                        
                        try:
                            self._escape_hold_timer.stop()
                        except Exception:
                            pass
            else:
                
                self._escape_hold_start = 0
        except Exception:
            
            try:
                self._escape_hold_start = 0
            except Exception:
                pass

    
    def hideEvent(self, event: QtGui.QHideEvent):
        try:
            
            for le in (getattr(self, 'trigger_key_input', None), getattr(self, 'keyboard_input', None), getattr(self, 'menu_key_combo', None)):
                if le is not None:
                    le.setEnabled(False)
                    le.clearFocus()
        except Exception:
            pass
        super().hideEvent(event)
    
    def showEvent(self, event: QtGui.QShowEvent):
        try:
            
            for le in (getattr(self, 'trigger_key_input', None), getattr(self, 'keyboard_input', None), getattr(self, 'menu_key_combo', None)):
                if le is not None:
                    le.setEnabled(True)
        except Exception:
            pass
        super().showEvent(event)
        
        # Ensure window is positioned within CS2 bounds when shown
        try:
            current_pos = self.pos()
            constrained_pos = self.constrain_to_cs2_window(current_pos)
            if constrained_pos != current_pos:
                self.move(constrained_pos)
        except Exception:
            pass

    def resizeEvent(self, event):
        """Ensure window stays within CS2 bounds when resized"""
        super().resizeEvent(event)
        try:
            current_pos = self.pos()
            constrained_pos = self.constrain_to_cs2_window(current_pos)
            if constrained_pos != current_pos:
                self.move(constrained_pos)
        except Exception:
            pass

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            new_pos = self.pos() + delta
            
            # Constrain window within CS2 window boundaries
            constrained_pos = self.constrain_to_cs2_window(new_pos)
            
            self.move(constrained_pos)
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = False
            # Set a timestamp when dragging ends to prevent immediate hiding
            import time
            self._drag_end_time = time.time()

    def update_radius_label(self):
        val = self.radius_slider.value()
        self.lbl_radius.setText(f"Aim Radius: ({val})")
        self.save_settings()

    def update_opacity_label(self):
        val = self.opacity_slider.value()
        self.lbl_opacity.setText(f"Circle Transparency: ({val})")
        self.save_settings()

    def update_thickness_label(self):
        val = self.thickness_slider.value()
        self.lbl_thickness.setText(f"Circle Thickness: ({val})")
        self.save_settings()

    def update_smooth_label(self):
        val = self.smooth_slider.value()
        self.lbl_smooth.setText(f"Aim Smoothness: ({val})")
        self.save_settings()

    def update_triggerbot_delay_label(self):
        val = self.triggerbot_delay_slider.value()
        self.lbl_delay.setText(f"Triggerbot Delay (ms): ({val})")
        self.save_settings()

    def update_triggerbot_first_shot_delay_label(self):
        val = self.triggerbot_first_shot_delay_slider.value()
        self.lbl_first_shot_delay.setText(f"First Shot Delay (ms): ({val})")
        self.save_settings()

    def update_center_dot_size_label(self):
        val = self.center_dot_size_slider.value()
        self.lbl_center_dot_size.setText(f"Center Dot Size: ({val})")
        self.save_settings()

    def update_radar_size_label(self):
        try:
            val = self.radar_size_slider.value()
            self.lbl_radar_size.setText(f"Radar Size: ({val})")
            self.save_settings()
        except Exception:
            pass

    def update_radar_scale_label(self):
        try:
            val = self.radar_scale_slider.value() / 10.0
            self.lbl_radar_scale.setText(f"Radar Scale: ({val:.1f})")
            self.save_settings()
        except Exception:
            pass

    def on_radar_position_changed(self):
        try:
            position = self.radar_position_combo.currentText()
            self.settings["radar_position"] = position
            self.save_settings()
        except Exception:
            pass

    def update_fps_limit_label(self):
        try:
            # Don't allow FPS changes when low CPU mode is active
            if self.settings.get('low_cpu', 0) == 1:
                self.fps_limit_slider.setValue(10)  # Force back to 10
                self.lbl_fps_limit.setText("FPS Limit: (10) - Locked by Low CPU Mode")
                return
                
            val = self.fps_limit_slider.value()
            self.lbl_fps_limit.setText(f"FPS Limit: ({val})")
            self.save_settings()
        except Exception:
            pass

def configurator():
    app = QtWidgets.QApplication(sys.argv)
    
    try:
        settings = load_settings()
        theme = settings.get("theme", "dark_red.xml")
    except Exception:
        theme = "dark_red.xml"
    try:
        apply_stylesheet(app, theme=theme)
    except Exception:
        
        try:
            apply_stylesheet(app, theme='dark_red.xml')
        except Exception:
            pass
    window = ConfigWindow()
    
    # Only show the window initially if CS2 is the active window
    if window.is_game_window_active():
        window.show()
    
    sys.exit(app.exec())


class ESPWindow(QtWidgets.QWidget):
    def __init__(self, settings, window_width=None, window_height=None):
        super().__init__()
        self.settings = settings
        self.setWindowTitle('ESP Overlay')
        
        if window_width is not None and window_height is not None:
            self.window_width, self.window_height = window_width, window_height
            # Try to get position info as well - use client area for accurate positioning
            self.window_x, self.window_y, _, _ = get_window_client_rect("Counter-Strike 2")
            if self.window_x is None or self.window_y is None:
                self.window_x, self.window_y = 0, 0
        else:
            self.window_x, self.window_y, self.window_width, self.window_height = get_window_client_rect("Counter-Strike 2")
            if self.window_width is None or self.window_height is None:
                self.window_width, self.window_height = 800, 600
                self.window_x, self.window_y = 0, 0
        
        
        if self.window_width is None or self.window_height is None:
            self.window_width, self.window_height = 800, 600
            self.window_x, self.window_y = 0, 0
        
        # Track window size and position for dynamic updates
        self.last_window_width = self.window_width
        self.last_window_height = self.window_height
        self.last_window_x = self.window_x
        self.last_window_y = self.window_y
        self.window_check_counter = 0
        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        hwnd = self.winId()
        try:
            
            curr_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            new_exstyle = curr_exstyle | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
            
            new_exstyle |= getattr(win32con, 'WS_EX_TOOLWINDOW', 0)
            
            new_exstyle &= ~getattr(win32con, 'WS_EX_APPWINDOW', 0)
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_exstyle)
            
            try:
                win32gui.SetWindowPos(int(hwnd), win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)
            except Exception:
                try:
                    
                    SWP_FLAGS = 0x0010 | 0x0001 | 0x0002 | 0x0040
                    win32gui.SetWindowPos(int(hwnd), -1, 0, 0, 0, 0, SWP_FLAGS)
                except Exception:
                    pass
        except Exception:
            
            try:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
            except Exception:
                pass

        self.file_watcher = QFileSystemWatcher([CONFIG_FILE])
        self.file_watcher.fileChanged.connect(self.reload_settings)

        self.offsets, self.client_dll = get_offsets_and_client_dll()
        
        import pymem
        import time
        self.pm = None
        self.client = None
        while self.pm is None or self.client is None:
            try:
                self.pm = pymem.Pymem("cs2.exe")
                self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
            except Exception:
                self.pm = None
                self.client = None
                time.sleep(1)  
        

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, self.window_width, self.window_height)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing, False)  # Disable for performance
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent;")
        self.view.setSceneRect(0, 0, self.window_width, self.window_height)
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)

        # Optimize graphics view for performance
        try:
            # Use minimal update mode for better performance
            self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.MinimalViewportUpdate)
        except Exception:
            try:
                self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
            except Exception:
                pass
        try:
            # Disable caching for better performance with frequent updates
            self.view.setCacheMode(QtWidgets.QGraphicsView.CacheNone)
        except Exception:
            pass

        # Performance optimizations
        try:
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            # Additional performance attributes
            self.setAttribute(QtCore.Qt.WA_NoBackground)
            self.setAttribute(QtCore.Qt.WA_PaintOnScreen)
        except Exception:
            pass

        
        self._entity_items = {}

        self.timer = QtCore.QTimer(self)
        
        try:
            self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        except Exception:
            pass
        self.timer.timeout.connect(self.update_scene)
        
        self.timer.start(33)

        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0
        
        # Initialize precise frame timing variables
        self.last_frame_time = time.time()
        self.target_fps = 60
        self.target_frame_time = 1.0 / 60.0

        
        try:
            self.apply_low_cpu_mode()
        except Exception:
            pass

    

    

    

    def reload_settings(self):
        self.settings = load_settings()
        
        # Force a window size and position check when settings are reloaded
        current_x, current_y, current_width, current_height = get_window_client_rect("Counter-Strike 2")
        if current_width is not None and current_height is not None:
            self.window_x = current_x
            self.window_y = current_y
            self.window_width = current_width
            self.window_height = current_height
            self.last_window_x = current_x
            self.last_window_y = current_y
            self.last_window_width = current_width
            self.last_window_height = current_height
            self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
            try:
                self.view.setGeometry(0, 0, self.window_width, self.window_height)
                self.view.setSceneRect(0, 0, self.window_width, self.window_height)
            except Exception as view_error:
                pass
        
        self.update_scene()
        try:
            
            self.apply_low_cpu_mode()
        except Exception:
            pass

    def apply_low_cpu_mode(self):
        """Adjust internal timers/intervals for low CPU mode and FPS limit.

        This uses either low CPU mode (10 FPS) or the custom FPS limit setting.
        Low CPU mode overrides the FPS limit when enabled.
        """
        try:
            low = int(self.settings.get('low_cpu', 0)) if isinstance(self.settings, dict) else 0
            fps_limit = int(self.settings.get('fps_limit', 60)) if isinstance(self.settings, dict) else 60
            
            # Store target FPS for precise limiting
            if low:
                self.target_fps = 10
                self.target_frame_time = 1.0 / 10.0  # 100ms per frame
                # Low CPU mode: 10 FPS with optimized processing
                self.timer.start(100)
                # Enable additional optimizations for low CPU mode
                self.setUpdatesEnabled(False)
                self.view.setOptimizationFlags(QtWidgets.QGraphicsView.DontAdjustForAntialiasing | 
                                              QtWidgets.QGraphicsView.DontSavePainterState)
                self.setUpdatesEnabled(True)
            else:
                self.target_fps = fps_limit
                self.target_frame_time = 1.0 / max(fps_limit, 1)
                # For lower FPS (under 80), use more accurate timer intervals
                # For higher FPS, use faster timer with frame timing control
                if fps_limit < 80:
                    interval_ms = int(1000 / max(fps_limit, 1))  # Accurate timer intervals for lower FPS
                else:
                    interval_ms = max(int(1000 / max(fps_limit, 1)) - 3, 1)  # Faster timer for high FPS with timing control
                self.timer.start(interval_ms)
                # Reset optimizations for higher FPS modes
                try:
                    self.view.setOptimizationFlags(QtWidgets.QGraphicsView.DontSavePainterState)
                except Exception:
                    pass
            
            # Initialize frame timing variables for precise FPS limiting
            if not hasattr(self, 'last_frame_time'):
                self.last_frame_time = time.time()
                
        except Exception:
            pass

    def check_and_update_window_size(self):
        """Check for CS2 window size and position changes and update overlay accordingly."""
        try:
            # Determine check frequency based on low CPU mode and FPS limit
            low_cpu_mode = int(self.settings.get('low_cpu', 0)) if isinstance(self.settings, dict) else 0
            fps_limit = int(self.settings.get('fps_limit', 60)) if isinstance(self.settings, dict) else 60
            
            # Adaptive check frequency based on performance mode
            # Make window checking much less frequent to avoid FPS dips
            if low_cpu_mode:
                check_interval = 50   # Check every 5 seconds at 10 FPS
            elif fps_limit >= 100:
                check_interval = 500  # Check every 5 seconds at high FPS
            elif fps_limit >= 60:
                check_interval = 300  # Check every 5 seconds at 60 FPS
            else:
                check_interval = 150  # Check every 5 seconds at 30 FPS
            
            self.window_check_counter += 1
            if self.window_check_counter < check_interval:
                return False  # No check needed yet
            
            # Reset counter
            self.window_check_counter = 0
            
            # Quick optimization: only check if we're not in fullscreen mode
            # Most users don't resize CS2 window frequently, so this check is often unnecessary
            try:
                # Get current CS2 window client area position and size
                current_x, current_y, current_width, current_height = get_window_client_rect("Counter-Strike 2")
                
                # If we can't get the window client rect, keep current dimensions
                if current_width is None or current_height is None:
                    return False
                
                # Check if size or position changed significantly (reduce sensitivity for performance)
                size_threshold = 15  # Increased threshold to reduce unnecessary updates
                if (abs(current_width - self.last_window_width) > size_threshold or 
                    abs(current_height - self.last_window_height) > size_threshold or
                    abs(current_x - self.last_window_x) > size_threshold or
                    abs(current_y - self.last_window_y) > size_threshold):
                    
                    # Update stored dimensions and position
                    self.window_x = current_x
                    self.window_y = current_y
                    self.window_width = current_width
                    self.window_height = current_height
                    self.last_window_x = current_x
                    self.last_window_y = current_y
                    self.last_window_width = current_width
                    self.last_window_height = current_height
                    
                    # Resize and reposition overlay window
                    self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
                    
                    # Update view and scene
                    try:
                        self.view.setGeometry(0, 0, self.window_width, self.window_height)
                        self.view.setSceneRect(0, 0, self.window_width, self.window_height)
                        # Clear scene to prevent visual artifacts during resize
                        self.scene.clear()
                    except Exception:
                        pass
                    
                    return True  # Size/position was updated
            except Exception:
                # If window checking fails, don't spam retries
                pass
                
        except Exception:
            pass
            
        return False

    def update_scene(self):
        # Early exit if game is not active - avoid all processing
        if not self.is_game_window_active():
            if hasattr(self, 'scene') and self.scene.items():
                self.scene.clear()
            return
            
        # Early exit if memory access is not available
        if not hasattr(self, 'pm') or not hasattr(self, 'client') or self.pm is None or self.client is None:
            if hasattr(self, 'scene') and self.scene.items():
                self.scene.clear()
            return

        # Precise FPS limiting only for high FPS settings (80+ FPS)
        # For lower FPS, rely primarily on timer intervals
        current_time = time.time()
        if hasattr(self, 'target_fps') and hasattr(self, 'target_frame_time') and hasattr(self, 'last_frame_time'):
            if self.target_fps >= 80:  # Only use strict timing for high FPS
                elapsed_time = current_time - self.last_frame_time
                if elapsed_time < self.target_frame_time * 0.85:  # 85% threshold for high FPS
                    return
            self.last_frame_time = current_time

        # Check for window size and position changes (less frequently for performance)
        size_or_position_changed = self.check_and_update_window_size()

        # Clear scene only if necessary
        if hasattr(self, 'scene'):
            self.scene.clear()
        
        try:
            # Cache settings for this frame to avoid repeated dictionary lookups
            esp_enabled = self.settings.get('esp_rendering', 1) == 1
            radar_enabled = self.settings.get('radar_enabled', 0) == 1
            center_dot_enabled = self.settings.get('center_dot', 0) == 1
            aim_active = self.settings.get('aim_active', 0) == 1
            aim_circle_visible = self.settings.get('aim_circle_visible', 1) == 1
            
            # Only render what's actually enabled to save processing
            if center_dot_enabled:
                render_center_dot(self.scene, self.window_width, self.window_height, self.settings)
            
            if aim_circle_visible:
                render_aim_circle(self.scene, self.window_width, self.window_height, self.settings)
            
            if radar_enabled:
                render_radar(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
            if esp_enabled:
                esp(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
            # Render bomb ESP independently of main ESP toggle
            render_bomb_esp(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            
            # Update FPS counter calculation (using the current_time from precise timing)
            self.frame_count += 1
            if current_time - self.last_time >= 1.0:
                # Calculate actual FPS with more precision
                actual_elapsed = current_time - self.last_time
                self.fps = round(self.frame_count / actual_elapsed)
                self.frame_count = 0
                self.last_time = current_time
            
            # Always render FPS text (not just when updating counter)
            try:
                fps_item = self.scene.addText(f"Popsicle CS2 | FPS: {self.fps}", QtGui.QFont('DejaVu Sans', 15, QtGui.QFont.Bold))
                fps_item.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                fps_item.setPos(5, 5)
            except Exception:
                pass
            
        except Exception as e:
            # Reduce error logging frequency to avoid spam
            if not hasattr(self, '_last_error_time') or current_time - self._last_error_time > 5.0:
                pass
                self._last_error_time = current_time

    

    def is_game_window_active(self):
        """Check if CS2 or config UI is the currently active window"""
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            if not foreground_hwnd:
                return False
            
            # Check if CS2 is active
            cs2_hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
            if cs2_hwnd and cs2_hwnd == foreground_hwnd:
                return True
            
            # Check if config UI is active by window title
            try:
                window_title = win32gui.GetWindowText(foreground_hwnd)
                if "Popsicle CS2 Config" in window_title:
                    return True
            except Exception:
                pass
            
            return False
        except Exception:
            return False

def render_center_dot(scene, window_width, window_height, settings):
    """Render center dot independently of ESP settings"""
    try:
        center_dot_enabled = settings.get('center_dot', 0) == 1
        if center_dot_enabled:
            center_x = window_width / 2
            center_y = window_height / 2
            dot_size = settings.get('center_dot_size', 3)
            
            # Handle rainbow center dot
            if settings.get('rainbow_center_dot', 0) == 1:
                try:
                    global RAINBOW_HUE
                    # Update RAINBOW_HUE for center dot rainbow mode
                    RAINBOW_HUE = (RAINBOW_HUE + 0.005) % 1.0
                    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE, 1.0, 1.0)]
                    dot_qcolor = QtGui.QColor(r, g, b)
                except Exception:
                    dot_hex = settings.get('center_dot_color', '#FFFFFF')
                    dot_qcolor = QtGui.QColor(dot_hex)
            else:
                dot_hex = settings.get('center_dot_color', '#FFFFFF')
                dot_qcolor = QtGui.QColor(dot_hex)
            
            # Render center dot
            dot_rect = QtCore.QRectF(center_x - dot_size/2, center_y - dot_size/2, dot_size, dot_size)
            scene.addEllipse(dot_rect, QtGui.QPen(dot_qcolor, 0), QtGui.QBrush(dot_qcolor))
    except Exception:
        pass

def render_aim_circle(scene, window_width, window_height, settings):
    """Render aim circle independently of ESP settings"""
    try:
        aim_circle_visible = settings.get('aim_circle_visible', 1) == 1
        if aim_circle_visible and 'radius' in settings and settings.get('radius', 0) != 0:
            center_x = window_width / 2
            center_y = window_height / 2
            screen_radius = settings['radius'] / 100.0 * min(center_x, center_y)
            opacity = settings.get("circle_opacity", 16)
            
            global RAINBOW_HUE
            if settings.get('rainbow_fov', 0) == 1:
                try:
                    # Only update RAINBOW_HUE if center dot rainbow is not already doing it
                    # This prevents double-updating when both rainbow modes are enabled
                    if settings.get('rainbow_center_dot', 0) != 1:
                        RAINBOW_HUE = (RAINBOW_HUE + 0.005) % 1.0
                    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(RAINBOW_HUE, 1.0, 1.0)]
                    aim_qcolor = QtGui.QColor(r, g, b)
                    aim_qcolor.setAlpha(opacity)
                except Exception:
                    aim_hex = settings.get('aim_circle_color', '#FF0000')
                    aim_qcolor = QtGui.QColor(aim_hex)
                    aim_qcolor.setAlpha(opacity)
            else:
                aim_hex = settings.get('aim_circle_color', '#FF0000')
                aim_qcolor = QtGui.QColor(aim_hex)
                aim_qcolor.setAlpha(opacity)
            
            # Get circle thickness from settings
            circle_thickness = settings.get('circle_thickness', 2)
            
            # Render aim circle
            scene.addEllipse(
                QtCore.QRectF(center_x - screen_radius, center_y - screen_radius, screen_radius * 2, screen_radius * 2),
                QtGui.QPen(aim_qcolor, circle_thickness),
                QtCore.Qt.NoBrush
            )
    except Exception:
        pass

def render_radar(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    """Render radar showing enemy positions"""
    try:
        if not settings.get('radar_enabled', 0):
            return
            
        # Radar settings
        radar_size = settings.get('radar_size', 200)
        radar_scale = settings.get('radar_scale', 5.0)
        radar_position = settings.get('radar_position', 'Top Right')
        radar_opacity = settings.get('radar_opacity', 180)
        
        # Calculate radar position based on setting
        margin = 50  # Margin from screen edges
        if radar_position == 'Top Right':
            radar_x = window_width - radar_size - margin
            radar_y = margin
        elif radar_position == 'Top Left':
            radar_x = margin
            radar_y = margin
        elif radar_position == 'Bottom Right':
            radar_x = window_width - radar_size - margin
            radar_y = window_height - radar_size - margin
        elif radar_position == 'Bottom Left':
            radar_x = margin
            radar_y = window_height - radar_size - margin
        elif radar_position == 'Bottom Middle':
            radar_x = (window_width - radar_size) / 2
            radar_y = window_height - radar_size - margin
        elif radar_position == 'Center Right':
            radar_x = window_width - radar_size - margin
            radar_y = (window_height - radar_size) / 2
        elif radar_position == 'Center Left':
            radar_x = margin
            radar_y = (window_height - radar_size) / 2
        else:
            # Default to top right if unknown position
            radar_x = window_width - radar_size - margin
            radar_y = margin
        
        # Draw radar background
        radar_bg = QtGui.QColor(0, 0, 0, radar_opacity)
        radar_border = QtGui.QColor(255, 255, 255, 200)
        
        # Radar circle background
        scene.addEllipse(
            QtCore.QRectF(radar_x, radar_y, radar_size, radar_size),
            QtGui.QPen(radar_border, 2),
            QtGui.QBrush(radar_bg)
        )
        
        # Radar center (local player)
        center_x = radar_x + radar_size / 2
        center_y = radar_y + radar_size / 2
        
        # Draw center dot (local player)
        player_color = QtGui.QColor(255, 255, 255, 255)  # White for local player
        scene.addEllipse(
            QtCore.QRectF(center_x - 3, center_y - 3, 6, 6),
            QtGui.QPen(player_color, 1),
            QtGui.QBrush(player_color)
        )
        
        # Get local player position and team
        dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
        dwViewMatrix = offsets['client.dll']['dwViewMatrix']
        m_pGameSceneNode = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
        m_vecAbsOrigin = client_dll['client.dll']['classes']['CGameSceneNode']['fields']['m_vecAbsOrigin']
        m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
        m_lifeState = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_lifeState']
        m_hPlayerPawn = client_dll['client.dll']['classes']['CCSPlayerController']['fields']['m_hPlayerPawn']
        m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
        
        local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
        if not local_player_pawn_addr:
            return
            
        try:
            local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
            local_game_scene = pm.read_longlong(local_player_pawn_addr + m_pGameSceneNode)
            local_x = pm.read_float(local_game_scene + m_vecAbsOrigin)
            local_y = pm.read_float(local_game_scene + m_vecAbsOrigin + 0x4)
            local_z = pm.read_float(local_game_scene + m_vecAbsOrigin + 0x8)  # Read Z coordinate for height comparison
            
            # Extract view direction from view matrix (already defined offset)
            view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]
            
            # Calculate yaw from view matrix - extract forward vector correctly
            # CS2 view matrix layout: forward vector is in elements [8], [9], [10]
            # Elements [8] and [9] represent the horizontal components of the forward vector
            forward_x = view_matrix[8]   # Forward X component
            forward_y = view_matrix[9]   # Forward Y component
            
            # Calculate yaw angle from forward vector (corrected coordinate system)
            local_yaw = math.degrees(math.atan2(forward_x, -forward_y))
            
        except Exception:
            # Fallback to no rotation if view matrix read fails
            local_yaw = 0.0
        
        # Get entity list
        dwEntityList = offsets['client.dll']['dwEntityList']
        entity_list = pm.read_longlong(client + dwEntityList)
        entity_ptr = pm.read_longlong(entity_list + 0x10)
        
        # Optimize radar entity processing - limit entities for performance
        max_radar_entities = 16 if settings.get('low_cpu', 0) == 1 else 32
        entities_processed = 0
        
        # Draw enemies on radar
        for i in range(1, 64):
            if entities_processed >= max_radar_entities:
                break
                
            try:
                if entity_ptr == 0:
                    break

                entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
                if entity_controller == 0:
                    continue

                entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
                if entity_controller_pawn == 0:
                    continue

                entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
                if entity_list_pawn == 0:
                    continue

                entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
                if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                    continue

                # Validate entity before processing
                try:
                    # Check if entity is still valid and connected
                    entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
                    entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
                    entity_health = pm.read_int(entity_pawn_addr + m_iHealth)
                    
                    # Strict validation for disconnected players
                    # 1. Must be alive (lifeState == 256)
                    # 2. Must have valid health (> 0)
                    # 3. Must have valid team (2 or 3 for CS2)
                    # 4. Team must not be same as player (unless ESP mode allows it)
                    if entity_alive != 256:
                        continue
                    if entity_health <= 0:
                        continue
                    if entity_team < 2 or entity_team > 3:  # Valid CS2 teams are 2 (T) and 3 (CT)
                        continue
                    if entity_team == local_player_team:
                        # Skip teammates unless ESP mode includes them
                        esp_mode = settings.get('esp_mode', 0)
                        if esp_mode == 0:  # Enemies only mode
                            continue
                    
                    # Additional validation: check if entity has valid position data
                    entity_game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                    if entity_game_scene == 0:
                        continue
                        
                    entity_x = pm.read_float(entity_game_scene + m_vecAbsOrigin)
                    entity_y = pm.read_float(entity_game_scene + m_vecAbsOrigin + 0x4)
                    entity_z = pm.read_float(entity_game_scene + m_vecAbsOrigin + 0x8)
                    
                    # Check for invalid positions (common with disconnected players)
                    if abs(entity_x) > 50000 or abs(entity_y) > 50000 or abs(entity_z) > 50000:
                        continue
                    if entity_x == 0.0 and entity_y == 0.0 and entity_z == 0.0:
                        continue
                        
                except Exception:
                    # If we can't read basic entity data, skip this entity
                    continue
                
                entities_processed += 1
                
                # Calculate relative position
                rel_x = (entity_x - local_x) / radar_scale
                rel_y = (entity_y - local_y) / radar_scale
                
                # Apply rotation so player's facing direction is always at top of radar
                try:
                    # Calculate angle offset to make player's forward direction point "up" (north)
                    rotation_angle = math.radians(-local_yaw + 180)
                    cos_rot = math.cos(rotation_angle)
                    sin_rot = math.sin(rotation_angle)
                    
                    # Apply rotation matrix to make forward direction always point up
                    rotated_x = rel_x * cos_rot - rel_y * sin_rot
                    rotated_y = rel_x * sin_rot + rel_y * cos_rot
                    
                    # Convert to radar coordinates
                    radar_entity_x = center_x + rotated_x
                    radar_entity_y = center_y - rotated_y  # Negative Y to make "up" work correctly
                except Exception:
                    # Fallback to non-rotated coordinates if rotation fails
                    radar_entity_x = center_x + rel_x
                    radar_entity_y = center_y - rel_y  # Flip Y axis
                
                # Check if entity is within radar bounds
                radar_radius = radar_size / 2
                distance_from_center = ((radar_entity_x - center_x) ** 2 + (radar_entity_y - center_y) ** 2) ** 0.5
                
                if distance_from_center <= radar_radius - 5:
                    # Choose color based on team (team validation already done above)
                    if entity_team == local_player_team:
                        entity_color = QtGui.QColor(0, 255, 0, 255)  # Green for teammates
                    else:
                        entity_color = QtGui.QColor(255, 0, 0, 255)  # Red for enemies
                    
                    # Check if enemy is spotted for white outline (only for enemies)
                    is_spotted = False
                    if entity_team != local_player_team:
                        try:
                            m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_entitySpottedState']
                            m_bSpotted = client_dll['client.dll']['classes']['EntitySpottedState_t']['fields']['m_bSpotted']
                            spotted_flag = pm.read_int(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            is_spotted = spotted_flag != 0
                        except Exception:
                            is_spotted = False
                    
                    # Check height difference to determine dot shape
                    try:
                        height_threshold = 50.0  # Height difference threshold in game units (adjust as needed)
                        height_diff = entity_z - local_z
                        is_height_different = abs(height_diff) > height_threshold
                        is_above = height_diff > 0
                    except Exception:
                        is_height_different = False
                        is_above = False
                    
                    # If enemy is spotted, draw white outline (adjust shape based on height)
                    if is_spotted and entity_team != local_player_team:
                        if is_height_different:
                            # Draw white outline for arrow shape
                            if is_above:
                                # Upward arrow outline
                                outline_points = [
                                    QtCore.QPointF(radar_entity_x, radar_entity_y - 3),      # Top point
                                    QtCore.QPointF(radar_entity_x - 3, radar_entity_y + 2),  # Bottom left
                                    QtCore.QPointF(radar_entity_x + 3, radar_entity_y + 2)   # Bottom right
                                ]
                            else:
                                # Downward arrow outline
                                outline_points = [
                                    QtCore.QPointF(radar_entity_x, radar_entity_y + 3),      # Bottom point
                                    QtCore.QPointF(radar_entity_x - 3, radar_entity_y - 2),  # Top left
                                    QtCore.QPointF(radar_entity_x + 3, radar_entity_y - 2)   # Top right
                                ]
                            outline_polygon = QtGui.QPolygonF(outline_points)
                            scene.addPolygon(
                                outline_polygon,
                                QtGui.QPen(QtGui.QColor(255, 255, 255, 255), 1),
                                QtCore.Qt.NoBrush
                            )
                        else:
                            # Draw white outline (larger circle) for same height
                            outline_rect = QtCore.QRectF(radar_entity_x - 3, radar_entity_y - 3, 6, 6)
                            scene.addEllipse(
                                outline_rect,
                                QtGui.QPen(QtGui.QColor(255, 255, 255, 255), 1),
                                QtCore.Qt.NoBrush
                            )
                    
                    # Draw the main dot - change shape based on height difference
                    if is_height_different:
                        # Draw arrow shape instead of circle
                        if is_above:
                            # Upward arrow (entity is above)
                            arrow_points = [
                                QtCore.QPointF(radar_entity_x, radar_entity_y - 2),      # Top point
                                QtCore.QPointF(radar_entity_x - 2, radar_entity_y + 1),  # Bottom left
                                QtCore.QPointF(radar_entity_x + 2, radar_entity_y + 1)   # Bottom right
                            ]
                        else:
                            # Downward arrow (entity is below)
                            arrow_points = [
                                QtCore.QPointF(radar_entity_x, radar_entity_y + 2),      # Bottom point
                                QtCore.QPointF(radar_entity_x - 2, radar_entity_y - 1),  # Top left
                                QtCore.QPointF(radar_entity_x + 2, radar_entity_y - 1)   # Top right
                            ]
                        arrow_polygon = QtGui.QPolygonF(arrow_points)
                        scene.addPolygon(
                            arrow_polygon,
                            QtGui.QPen(entity_color, 1),
                            QtGui.QBrush(entity_color)
                        )
                    else:
                        # Draw regular circular dot for same height
                        dot_rect = QtCore.QRectF(radar_entity_x - 2, radar_entity_y - 2, 4, 4)
                        scene.addEllipse(
                            dot_rect,
                            QtGui.QPen(entity_color, 1),
                            QtGui.QBrush(entity_color)
                        )
                    
            except Exception:
                continue
                
    except Exception:
        pass

def render_bomb_esp(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    """Render bomb ESP independently of main ESP"""
    try:
        bomb_esp_enabled = settings.get('bomb_esp', 0) == 1
        if not bomb_esp_enabled:
            return
            
        # Cache offsets for bomb ESP
        dwPlantedC4 = offsets['client.dll']['dwPlantedC4']
        m_pGameSceneNode = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
        m_vecAbsOrigin = client_dll['client.dll']['classes']['CGameSceneNode']['fields']['m_vecAbsOrigin']
        m_flTimerLength = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_flTimerLength']
        m_flDefuseLength = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_flDefuseLength']
        m_bBeingDefused = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_bBeingDefused']

        # Get view matrix for world to screen conversion
        dwViewMatrix = offsets['client.dll']['dwViewMatrix']
        view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]

        def bombisplant():
            global BombPlantedTime
            bombisplant = pm.read_bool(client + dwPlantedC4 - 0x8)
            if bombisplant:
                if (BombPlantedTime == 0):
                    BombPlantedTime = time.time()
            else:
                BombPlantedTime = 0
            return bombisplant
        
        def getC4BaseClass():
            plantedc4 = pm.read_longlong(client + dwPlantedC4)
            plantedc4class = pm.read_longlong(plantedc4)
            return plantedc4class
        
        def getPositionWTS():
            c4node = pm.read_longlong(getC4BaseClass() + m_pGameSceneNode)
            c4posX = pm.read_float(c4node + m_vecAbsOrigin)
            c4posY = pm.read_float(c4node + m_vecAbsOrigin + 0x4)
            c4posZ = pm.read_float(c4node + m_vecAbsOrigin + 0x8)
            bomb_pos = w2s(view_matrix, c4posX, c4posY, c4posZ, window_width, window_height)
            return bomb_pos
        
        def getBombTime():
            BombTime = pm.read_float(getC4BaseClass() + m_flTimerLength) - (time.time() - BombPlantedTime)
            return BombTime if (BombTime >= 0) else 0
        
        def isBeingDefused():
            global BombDefusedTime
            BombIsDefused = pm.read_bool(getC4BaseClass() + m_bBeingDefused)
            if (BombIsDefused):
                if (BombDefusedTime == 0):
                    BombDefusedTime = time.time() 
            else:
                BombDefusedTime = 0
            return BombIsDefused
        
        def getDefuseTime():
            DefuseTime = pm.read_float(getC4BaseClass() + m_flDefuseLength) - (time.time() - BombDefusedTime)
            return DefuseTime if (isBeingDefused() and DefuseTime >= 0) else 0

        bfont = QtGui.QFont('DejaVu Sans', 10, QtGui.QFont.Bold)

        # Bomb ESP rendering
        if bombisplant():
            BombPosition = getPositionWTS()
            BombTime = getBombTime()
            DefuseTime = getDefuseTime()
        
            if (BombPosition[0] > 0 and BombPosition[1] > 0):
                if DefuseTime > 0:
                    c4_name_text = scene.addText(f'BOMB {round(BombTime, 2)} | DIF {round(DefuseTime, 2)}', bfont)
                else:
                    c4_name_text = scene.addText(f'BOMB {round(BombTime, 2)}', bfont)
                c4_name_x = BombPosition[0]
                c4_name_y = BombPosition[1]
                c4_name_text.setPos(c4_name_x, c4_name_y)
                c4_name_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                
    except Exception:
        pass

def esp(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    # Early exit if ESP is disabled
    if settings.get('esp_rendering', 1) == 0:
        return
    
    # Cache frequently accessed settings for performance
    esp_mode = settings.get('esp_mode', 1)
    
    # Cache rendering flags - early exit optimization
    box_rendering = settings.get('box_rendering', 1) == 1
    line_rendering = settings.get('line_rendering', 1) == 1
    hp_bar_rendering = settings.get('hp_bar_rendering', 1) == 1
    head_hitbox_rendering = settings.get('head_hitbox_rendering', 1) == 1
    bones_rendering = settings.get('Bones', 0) == 1
    nickname_rendering = settings.get('nickname', 0) == 1
    weapon_rendering = settings.get('weapon', 0) == 1
    
    # Early exit if nothing to render (bomb ESP is now separate)
    if not (box_rendering or line_rendering or hp_bar_rendering or head_hitbox_rendering or 
            bones_rendering or nickname_rendering or weapon_rendering):
        return
    
    # Cache color objects to avoid repeated creation
    try:
        team_hex = settings.get('team_color', '#47A76A')
        enemy_hex = settings.get('enemy_color', '#C41E3A')
        team_color = QtGui.QColor(team_hex)
        enemy_color = QtGui.QColor(enemy_hex)
    except Exception:
        team_color = QtGui.QColor(71, 167, 106)
        enemy_color = QtGui.QColor(196, 30, 58)

    # Cache offsets for better performance
    dwEntityList = offsets['client.dll']['dwEntityList']
    dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
    dwViewMatrix = offsets['client.dll']['dwViewMatrix']
    dwPlantedC4 = offsets['client.dll']['dwPlantedC4']
    m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
    m_lifeState = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_lifeState']
    m_pGameSceneNode = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
    m_modelState = client_dll['client.dll']['classes']['CSkeletonInstance']['fields']['m_modelState']
    m_hPlayerPawn = client_dll['client.dll']['classes']['CCSPlayerController']['fields']['m_hPlayerPawn']
    m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
    m_iszPlayerName = client_dll['client.dll']['classes']['CBasePlayerController']['fields']['m_iszPlayerName']
    m_pClippingWeapon = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_pClippingWeapon']
    m_AttributeManager = client_dll['client.dll']['classes']['C_EconEntity']['fields']['m_AttributeManager']
    m_Item = client_dll['client.dll']['classes']['C_AttributeContainer']['fields']['m_Item']
    m_iItemDefinitionIndex = client_dll['client.dll']['classes']['C_EconItemView']['fields']['m_iItemDefinitionIndex']
    m_ArmorValue = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_ArmorValue']
    m_vecAbsOrigin = client_dll['client.dll']['classes']['CGameSceneNode']['fields']['m_vecAbsOrigin']
    m_flTimerLength = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_flTimerLength']
    m_flDefuseLength = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_flDefuseLength']
    m_bBeingDefused = client_dll['client.dll']['classes']['C_PlantedC4']['fields']['m_bBeingDefused']

    view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]

    local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
    try:
        local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
    except:
        return

    no_center_x = window_width / 2
    no_center_y = window_height * 0.9
    entity_list = pm.read_longlong(client + dwEntityList)
    entity_ptr = pm.read_longlong(entity_list + 0x10)

    for i in range(1, 64):
        try:
            if entity_ptr == 0:
                break

            entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
            if entity_controller == 0:
                continue

            entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
            if entity_controller_pawn == 0:
                continue

            entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
            if entity_list_pawn == 0:
                continue

            entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
            if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                continue

            entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
            if entity_team == local_player_team and esp_mode == 0:
                continue

            entity_hp = pm.read_int(entity_pawn_addr + m_iHealth)
            if entity_hp <= 0:
                continue

            entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
            if entity_alive != 256:
                continue
            
            # Read armor only if HP bar rendering is enabled
            armor_hp = 0
            if hp_bar_rendering:
                armor_hp = pm.read_int(entity_pawn_addr + m_ArmorValue)
            
            # Read weapon only if weapon rendering is enabled
            weapon_name = ""
            if weapon_rendering:
                try:
                    weapon_pointer = pm.read_longlong(entity_pawn_addr + m_pClippingWeapon)
                    weapon_index = pm.read_int(weapon_pointer + m_AttributeManager + m_Item + m_iItemDefinitionIndex)
                    weapon_name = get_weapon_name_by_index(weapon_index)
                except Exception:
                    weapon_name = "Unknown"

            # Use cached color objects
            color = team_color if entity_team == local_player_team else enemy_color
            
            # Calculate position only if we have the entity
            game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
            bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)

            try:
                # Read bone positions once
                headX = pm.read_float(bone_matrix + 6 * 0x20)
                headY = pm.read_float(bone_matrix + 6 * 0x20 + 0x4)
                headZ = pm.read_float(bone_matrix + 6 * 0x20 + 0x8) + 8
                legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                
                # Calculate screen positions once
                head_pos = w2s(view_matrix, headX, headY, headZ, window_width, window_height)
                if head_pos[1] < 0:
                    continue
                    
                leg_pos = w2s(view_matrix, headX, headY, legZ, window_width, window_height)
                deltaZ = abs(head_pos[1] - leg_pos[1])
                leftX = head_pos[0] - deltaZ // 4
                rightX = head_pos[0] + deltaZ // 4
                
                # Render line if enabled
                if line_rendering:
                    bottom_left_x = head_pos[0] - (head_pos[0] - leg_pos[0]) // 2
                    bottom_y = leg_pos[1]
                    line = scene.addLine(bottom_left_x, bottom_y, no_center_x, no_center_y, QtGui.QPen(color, 1))
                
                # Render box if enabled
                if box_rendering:
                    rect = scene.addRect(QtCore.QRectF(leftX, head_pos[1], rightX - leftX, leg_pos[1] - head_pos[1]), QtGui.QPen(color, 1), QtCore.Qt.NoBrush)

                # Render HP bar if enabled
                if hp_bar_rendering:
                    max_hp = 100
                    hp_percentage = min(1.0, max(0.0, entity_hp / max_hp))
                    hp_bar_width = 2
                    hp_bar_height = deltaZ
                    hp_bar_x_left = leftX - hp_bar_width - 2
                    hp_bar_y_top = head_pos[1]
                    
                    # Create HP bar background and current HP in one operation
                    hp_bar = scene.addRect(QtCore.QRectF(hp_bar_x_left, hp_bar_y_top, hp_bar_width, hp_bar_height), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(0, 0, 0))
                    current_hp_height = hp_bar_height * hp_percentage
                    hp_bar_y_bottom = hp_bar_y_top + hp_bar_height - current_hp_height
                    hp_bar_current = scene.addRect(QtCore.QRectF(hp_bar_x_left, hp_bar_y_bottom, hp_bar_width, current_hp_height), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(255, 0, 0))
                    
                    # Render armor bar if there's armor
                    if armor_hp > 0:
                        max_armor_hp = 100
                        armor_hp_percentage = min(1.0, max(0.0, armor_hp / max_armor_hp))
                        armor_bar_width = 2
                        armor_bar_height = deltaZ
                        armor_bar_x_left = hp_bar_x_left - armor_bar_width - 2
                        armor_bar_y_top = head_pos[1]
                    
                        armor_bar = scene.addRect(QtCore.QRectF(armor_bar_x_left, armor_bar_y_top, armor_bar_width, armor_bar_height), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(0, 0, 0))
                        current_armor_height = armor_bar_height * armor_hp_percentage
                        armor_bar_y_bottom = armor_bar_y_top + armor_bar_height - current_armor_height
                        armor_bar_current = scene.addRect(QtCore.QRectF(armor_bar_x_left, armor_bar_y_bottom, armor_bar_width, current_armor_height), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(62, 95, 138))

                # Render head hitbox if enabled
                if head_hitbox_rendering:
                    head_hitbox_size = (rightX - leftX) / 5
                    head_hitbox_radius = head_hitbox_size * 2 ** 0.5 / 2
                    head_hitbox_x = leftX + 2.5 * head_hitbox_size
                    head_hitbox_y = head_pos[1] + deltaZ / 9
                    ellipse = scene.addEllipse(QtCore.QRectF(head_hitbox_x - head_hitbox_radius, head_hitbox_y - head_hitbox_radius, head_hitbox_radius * 2, head_hitbox_radius * 2), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(255, 0, 0, 128))

                # Render bones if enabled
                if bones_rendering:
                    draw_Bones(scene, pm, bone_matrix, view_matrix, window_width, window_height)

                # Render nickname if enabled
                if nickname_rendering:
                    player_name = pm.read_string(entity_controller + m_iszPlayerName, 32)
                    font_size = max(6, min(18, deltaZ / 25))
                    font = QtGui.QFont('DejaVu Sans', font_size, QtGui.QFont.Bold)
                    name_text = scene.addText(player_name, font)
                    text_rect = name_text.boundingRect()
                    name_x = head_pos[0] - text_rect.width() / 2
                    name_y = head_pos[1] - text_rect.height()
                    name_text.setPos(name_x, name_y)
                    name_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                
                # Render spotted status if enabled (independent of nickname)
                if settings.get('show_visibility', 0) == 1:
                    try:
                        m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_entitySpottedState']
                        m_bSpotted = client_dll['client.dll']['classes']['EntitySpottedState_t']['fields']['m_bSpotted']
                        try:
                            spotted_flag = pm.read_int(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            is_spotted = spotted_flag != 0
                        except Exception:
                            # Fallback to bool read
                            try:
                                is_spotted = pm.read_bool(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                            except Exception:
                                is_spotted = False
                        vis_text = "(Spotted)" if is_spotted else "(Not Spotted)"
                        
                        font_size = max(6, min(18, deltaZ / 25))
                        vis_font = QtGui.QFont('DejaVu Sans', max(5, min(14, font_size)))
                        vis_font.setBold(True)
                        vis_item = scene.addText(vis_text, vis_font)
                        vrect = vis_item.boundingRect()
                        vis_x = head_pos[0] - vrect.width() / 2
                        
                        # Position spotted status based on whether nickname is shown
                        if nickname_rendering:
                            # If nickname is shown, place spotted status above it
                            name_y = head_pos[1] - 20  # Approximate nickname position
                            vis_y = name_y - 15
                        else:
                            # If no nickname, place spotted status above head
                            vis_y = head_pos[1] - 20
                        
                        vis_item.setPos(vis_x, vis_y)
                        
                        if is_spotted:
                            vis_item.setDefaultTextColor(QtGui.QColor(0, 200, 0))
                        else:
                            vis_item.setDefaultTextColor(QtGui.QColor(200, 0, 0))
                    except Exception:
                        pass
                
                # Render weapon if enabled
                if weapon_rendering and weapon_name:
                    font_size = max(6, min(18, deltaZ / 25))
                    font = QtGui.QFont('DejaVu Sans', font_size, QtGui.QFont.Bold)
                    weapon_name_text = scene.addText(weapon_name, font)
                    text_rect = weapon_name_text.boundingRect()
                    weapon_name_x = head_pos[0] - text_rect.width() / 2
                    weapon_name_y = head_pos[1] + deltaZ
                    weapon_name_text.setPos(weapon_name_x, weapon_name_y)
                    weapon_name_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))


            except:
                return
        except:
            return

def get_weapon_name_by_index(index):
    weapon_names = {
    32: "P2000",
    61: "USP-S",
    4: "Glock",
    2: "Dual Berettas",
    36: "P250",
    30: "Tec-9",
    63: "CZ75-Auto",
    1: "Desert Eagle",
    3: "Five-SeveN",
    64: "R8",
    35: "Nova",
    25: "XM1014",
    27: "MAG-7",
    29: "Sawed-Off",
    14: "M249",
    28: "Negev",
    17: "MAC-10",
    23: "MP5-SD",
    24: "UMP-45",
    19: "P90",
    26: "Bizon",
    34: "MP9",
    33: "MP7",
    10: "FAMAS",
    16: "M4A4",
    60: "M4A1-S",
    8: "AUG",
    43: "Galil",
    7: "AK-47",
    39: "SG 553",
    40: "SSG 08",
    9: "AWP",
    38: "SCAR-20",
    11: "G3SG1",
    43: "Flashbang",
    44: "Hegrenade",
    45: "Smoke",
    46: "Molotov",
    47: "Decoy",
    48: "Incgrenage",
    49: "C4",
    31: "Taser",
    42: "Knife",
    41: "Knife Gold",
    59: "Knife",
    80: "Knife Ghost",
    500: "Knife Bayonet",
    505: "Knife Flip",
    506: "Knife Gut",
    507: "Knife Karambit",
    508: "Knife M9",
    509: "Knife Tactica",
    512: "Knife Falchion",
    514: "Knife Survival Bowie",
    515: "Knife Butterfly",
    516: "Knife Rush",
    519: "Knife Ursus",
    520: "Knife Gypsy Jackknife",
    522: "Knife Stiletto",
    523: "Knife Widowmaker"
}
    return weapon_names.get(index, 'Unknown')

def draw_Bones(scene, pm, bone_matrix, view_matrix, width, height):
    bone_ids = {
        "head": 6,
        "neck": 5,
        "spine": 4,
        "pelvis": 0,
        "left_shoulder": 13,
        "left_elbow": 14,
        "left_wrist": 15,
        "right_shoulder": 9,
        "right_elbow": 10,
        "right_wrist": 11,
        "left_hip": 25,
        "left_knee": 26,
        "left_ankle": 27,
        "right_hip": 22,
        "right_knee": 23,
        "right_ankle": 24,
    }
    bone_connections = [
        ("head", "neck"),
        ("neck", "spine"),
        ("spine", "pelvis"),
        ("pelvis", "left_hip"),
        ("left_hip", "left_knee"),
        ("left_knee", "left_ankle"),
        ("pelvis", "right_hip"),
        ("right_hip", "right_knee"),
        ("right_knee", "right_ankle"),
        ("neck", "left_shoulder"),
        ("left_shoulder", "left_elbow"),
        ("left_elbow", "left_wrist"),
        ("neck", "right_shoulder"),
        ("right_shoulder", "right_elbow"),
        ("right_elbow", "right_wrist"),
    ]
    bone_positions = {}
    try:
        for bone_name, bone_id in bone_ids.items():
            boneX = pm.read_float(bone_matrix + bone_id * 0x20)
            boneY = pm.read_float(bone_matrix + bone_id * 0x20 + 0x4)
            boneZ = pm.read_float(bone_matrix + bone_id * 0x20 + 0x8)
            bone_pos = w2s(view_matrix, boneX, boneY, boneZ, width, height)
            if bone_pos[0] != -999 and bone_pos[1] != -999:
                bone_positions[bone_name] = bone_pos
        for connection in bone_connections:
            if connection[0] in bone_positions and connection[1] in bone_positions:
                scene.addLine(
                    bone_positions[connection[0]][0], bone_positions[connection[0]][1],
                    bone_positions[connection[1]][0], bone_positions[connection[1]][1],
                    QtGui.QPen(QtGui.QColor(255, 255, 255, 128), 1)
                )
    except Exception as e:
        pass

def esp_main():
    settings = load_settings()
    app = QtWidgets.QApplication(sys.argv)
    
    
    window_width = None
    window_height = None
    pm = None
    client = None
    while True:
        
        w, h = get_window_size("Counter-Strike 2")
        if w is not None and h is not None:
            window_width, window_height = w, h
        
        # Use the improved CS2 detection function
        if is_cs2_running():
            try:
                pm = pymem.Pymem("cs2.exe")
                try:
                    client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                except Exception:
                    client = None
            except Exception:
                pm = None
        else:
            pm = None
            client = None

        
        if window_width and window_height and pm is not None and client is not None:
            break
        time.sleep(1)

    
    window = ESPWindow(settings, window_width=window_width, window_height=window_height)
    
    try:
        window.offsets, window.client_dll = get_offsets_and_client_dll()
        window.pm = pm
        window.client = client
    except Exception:
               pass

    window.show()
    sys.exit(app.exec())


def triggerbot():
    offsets = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json').json()
    client_dll = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json').json()
    dwEntityList = offsets['client.dll']['dwEntityList']
    dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
    m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']

    m_iIDEntIndex = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_iIDEntIndex']
    m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
    from pynput.mouse import Controller, Button
    mouse = Controller()
    default_settings = {
        "TriggerKey": "X",
        "trigger_bot_active":  1,
        "esp_mode": 1
    }

    def load_settings():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return default_settings

    def main(settings):
        pm = None
        client = None
        
        # State tracking for first shot delay
        trigger_key_pressed = False
        first_shot_time = None
        
        while pm is None or client is None:
            if is_cs2_running():
                try:
                    pm = pymem.Pymem("cs2.exe")
                    client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                except Exception:
                    pm = None
                    client = None
                    time.sleep(1)
            else:
                pm = None
                client = None
                time.sleep(1)
        while True:
            try:
                trigger_bot_active = settings.get("trigger_bot_active", 0)
                keyboards = settings.get("TriggerKey", "X")
                delay_ms = settings.get("triggerbot_delay", 30)
                first_shot_delay_ms = settings.get("triggerbot_first_shot_delay", 0)
                
                vk = key_str_to_vk(keyboards)
                
                # Check if trigger key is on cooldown
                if is_keybind_on_global_cooldown("TriggerKey"):
                    key_currently_pressed = False
                else:
                    # Check if trigger key is currently pressed
                    key_currently_pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                
                # Track key press state changes
                if key_currently_pressed and not trigger_key_pressed:
                    # Key just pressed - start first shot timer
                    trigger_key_pressed = True
                    first_shot_time = time.time()
                elif not key_currently_pressed and trigger_key_pressed:
                    # Key just released - reset state
                    trigger_key_pressed = False
                    first_shot_time = None
                
                if key_currently_pressed:
                    if trigger_bot_active == 1:
                        try:
                            player = pm.read_longlong(client + dwLocalPlayerPawn)
                            entityId = pm.read_int(player + m_iIDEntIndex)
                            
                            # Debug: Print entityId to see if we're detecting targets
                            if entityId > 0:
                                pass
                            
                            if entityId > 0:
                                entList = pm.read_longlong(client + dwEntityList)
                                entEntry = pm.read_longlong(entList + 0x8 * (entityId >> 9) + 0x10)
                                entity = pm.read_longlong(entEntry + 0x78 * (entityId & 0x1FF))
                                entityTeam = pm.read_int(entity + m_iTeamNum)
                                playerTeam = pm.read_int(player + m_iTeamNum)
                                entityHp = pm.read_int(entity + m_iHealth)
                                
                                # Debug: Print team and health info
                                pass
                                
                                # Triggerbot should only shoot enemies, never teammates
                                if entityTeam != playerTeam:
                                    if entityHp > 0:
                                        # Check if first shot delay has elapsed
                                        current_time = time.time()
                                        if first_shot_time is None or current_time - first_shot_time >= (first_shot_delay_ms / 1000.0):
                                            pass
                                            
                                            # Fire the shot
                                            try:
                                                mouse.press(Button.left)
                                                mouse.release(Button.left)
                                                pass
                                                
                                                # Set up for continuous firing
                                                if first_shot_time is not None:
                                                    first_shot_time = None  # Clear first shot delay
                                                last_shot_time = current_time
                                                
                                                # Continuous firing loop
                                                while key_currently_pressed and trigger_bot_active == 1:
                                                    time.sleep(0.001)  # Small sleep first
                                                    
                                                    # Check if enough time has passed for next shot
                                                    current_time = time.time()
                                                    if current_time - last_shot_time >= (delay_ms / 1000.0):
                                                        # Re-check key state
                                                        key_currently_pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
                                                        if not key_currently_pressed:
                                                            break
                                                        
                                                        # Re-check settings
                                                        trigger_bot_active = settings.get("trigger_bot_active", 0)
                                                        if trigger_bot_active != 1:
                                                            break
                                                        
                                                        # Re-read player/entity to ensure still valid target
                                                        try:
                                                            player_r = pm.read_longlong(client + dwLocalPlayerPawn)
                                                            entityId_r = pm.read_int(player_r + m_iIDEntIndex)
                                                            if entityId_r <= 0:
                                                                pass
                                                                break
                                                            entList_r = pm.read_longlong(client + dwEntityList)
                                                            entEntry_r = pm.read_longlong(entList_r + 0x8 * (entityId_r >> 9) + 0x10)
                                                            entity_r = pm.read_longlong(entEntry_r + 0x78 * (entityId_r & 0x1FF))
                                                            entityTeam_r = pm.read_int(entity_r + m_iTeamNum)
                                                            playerTeam_r = pm.read_int(player_r + m_iTeamNum)
                                                            # Triggerbot should only shoot enemies, never teammates
                                                            if entityTeam_r == playerTeam_r:
                                                                pass
                                                                break
                                                            entityHp_r = pm.read_int(entity_r + m_iHealth)
                                                            if entityHp_r <= 0:
                                                                pass
                                                                break
                                                        except Exception as e:
                                                            pass
                                                            break
                                                        
                                                        # Fire next shot
                                                        try:
                                                            mouse.press(Button.left)
                                                            mouse.release(Button.left)
                                                            last_shot_time = current_time
                                                            pass
                                                        except Exception as e:
                                                            pass
                                                            break
                                                
                                            except Exception as e:
                                                pass
                                        else:
                                            pass
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                # Only print this occasionally to avoid spam
                                if hasattr(main, '_no_target_counter'):
                                    main._no_target_counter += 1
                                else:
                                    main._no_target_counter = 1
                                    
                                if main._no_target_counter % 100 == 0:  # Print every 100 iterations
                                    pass
                        except Exception as e:
                            pass
                    else:
                        # Only print this occasionally
                        if hasattr(main, '_inactive_counter'):
                            main._inactive_counter += 1
                        else:
                            main._inactive_counter = 1
                            
                        if main._inactive_counter % 1000 == 0:  # Print every 1000 iterations
                            pass
                # Idle sleep when not actively repeating shots: keep short for responsiveness
                time.sleep(0.01)
            except KeyboardInterrupt:
                break
            except Exception:
                time.sleep(1)

    def start_main_thread(settings):
        while True:
            main(settings)

    def setup_watcher(app, settings):
        watcher = QFileSystemWatcher()
        watcher.addPath(CONFIG_FILE)
        def reload_settings():
            new_settings = load_settings()
            settings.update(new_settings)
        watcher.fileChanged.connect(reload_settings)
        app.exec()

    def main_program():
        app = QCoreApplication(sys.argv)
        settings = load_settings()
        threading.Thread(target=start_main_thread, args=(settings,), daemon=True).start()
        setup_watcher(app, settings)

    main_program()

def bhop():
    """Bunny hop function with configurable keybind"""
    import time
    import keyboard
    
    # Timing constants
    TICK_64_MS = 0.0156
    exit_key = "end"
    toggle_key = "+"
    
    toggle = True
    
    def convert_key_to_keyboard_format(key_str):
        """Convert key string to keyboard library format"""
        if not key_str:
            return "space"
        
        key = str(key_str).strip().upper()
        
        # Handle special cases for keyboard library
        key_mapping = {
            'SPACE': 'space',
            'ENTER': 'enter',
            'RETURN': 'enter',
            'SHIFT': 'shift',
            'CTRL': 'ctrl',
            'CONTROL': 'ctrl',
            'ALT': 'alt',
            'TAB': 'tab',
            'ESC': 'esc',
            'ESCAPE': 'esc',
            'UP': 'up',
            'DOWN': 'down',
            'LEFT': 'left',
            'RIGHT': 'right',
            'BACKSPACE': 'backspace',
            'DELETE': 'delete',
            'INSERT': 'insert',
            'HOME': 'home',
            'END': 'end',
            'PAGEUP': 'page up',
            'PAGEDOWN': 'page down',
            # Mouse buttons fallback to space
            'LMB': 'space',
            'RMB': 'space',
            'MMB': 'space',
            'MOUSE4': 'space',
            'MOUSE5': 'space',
        }
        
        if key in key_mapping:
            return key_mapping[key]
        
        # Handle F-keys
        if key.startswith('F') and key[1:].isdigit():
            try:
                num = int(key[1:])
                if 1 <= num <= 24:
                    return f"f{num}"
            except:
                pass
        
        # Handle single characters - be very specific about format
        if len(key) == 1:
            if key.isalpha():
                return key.lower()
            elif key.isdigit():
                return key
        
        # If nothing matches, test if the key is valid by trying to use it
        try:
            # Test if keyboard library recognizes this key
            keyboard.is_pressed(key.lower())
            return key.lower()
        except:
            pass
        
        try:
            # Test uppercase
            keyboard.is_pressed(key)
            return key
        except:
            pass
        
        # Fallback to space if nothing works
        return "space"

    def send_space(duration):
        try:
            keyboard.send("space")
            time.sleep(duration)
        except Exception:
            time.sleep(duration)
    
    try:
        keyboard.add_hotkey(exit_key, lambda: exit())
    except Exception:
        pass
    
    default_settings = {
        "bhop_enabled": 1,
        "BhopKey": "SPACE"
    }

    def load_settings():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    settings = default_settings.copy()
                    settings.update(loaded)
                    return settings
            except:
                pass
        return default_settings

    def is_cs2_window_active():
        """Check if CS2 is the currently active window"""
        try:
            hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
            if hwnd:
                foreground_hwnd = win32gui.GetForegroundWindow()
                return hwnd == foreground_hwnd
            return False
        except Exception:
            return False

    def main(settings):
        nonlocal toggle
        
        while True:
            try:
                bhop_enabled = settings.get("bhop_enabled", 0)
                
                if bhop_enabled == 1 and is_cs2_window_active():
                    # Get the current keybind from settings each time (this allows live updates)
                    bhop_key_setting = settings.get("BhopKey", "SPACE")
                    activation_key = convert_key_to_keyboard_format(bhop_key_setting)
                    
                    # Test if the key is valid, fallback to space if not
                    try:
                        keyboard.is_pressed(activation_key)
                    except:
                        activation_key = "space"
                    
                    if keyboard.is_pressed(activation_key):
                        if toggle:
                            send_space(TICK_64_MS * 1.5)
                            
                            while keyboard.is_pressed(activation_key) and is_cs2_window_active():
                                send_space(TICK_64_MS * 3)
                    elif keyboard.is_pressed(toggle_key):
                        toggle = not toggle
                        time.sleep(0.2)
                    else:
                        time.sleep(0.001)
                else:
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                break
            except Exception:
                time.sleep(1)

    def start_main_thread(settings):
        while True:
            try:
                main(settings)
            except Exception:
                time.sleep(5)

    def setup_watcher(app, settings):
        watcher = QFileSystemWatcher()
        watcher.addPath(CONFIG_FILE)
        def reload_settings():
            new_settings = load_settings()
            settings.update(new_settings)
        watcher.fileChanged.connect(reload_settings)
        app.exec()

    def main_program():
        app = QCoreApplication(sys.argv)
        settings = load_settings()
        threading.Thread(target=start_main_thread, args=(settings,), daemon=True).start()
        setup_watcher(app, settings)

    main_program()

def aim():
    default_settings = {
         'esp_rendering': 1,
         'esp_mode': 1,
         'AimKey': "C",
         'aim_active': 1,
         'aim_mode': 1,
         'radius': 20,
         'aim_mode_distance': 1,
         'aim_smoothness': 50,
         'aim_disable_when_crosshair_on_enemy': 0
     }
    
    def get_window_size(window_name="Counter-Strike 2"):
        hwnd = win32gui.FindWindow(None, window_name)
        if hwnd:
            rect = win32gui.GetClientRect(hwnd)
            return rect[2] - rect[0], rect[3] - rect[1]
        return 1920, 1080

    def load_settings():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return default_settings

    def get_offsets_and_client_dll():
        offsets = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json').json()
        client_dll = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json').json()
        return offsets, client_dll

    def esp(pm, client, offsets, client_dll, settings, target_list, window_size):
        width, height = window_size
        if settings['aim_active'] == 0:
            return
        dwEntityList = offsets['client.dll']['dwEntityList']
        dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
        dwViewMatrix = offsets['client.dll']['dwViewMatrix']
        m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
        m_lifeState = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_lifeState']
        m_pGameSceneNode = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
        m_modelState = client_dll['client.dll']['classes']['CSkeletonInstance']['fields']['m_modelState']
        m_hPlayerPawn = client_dll['client.dll']['classes']['CCSPlayerController']['fields']['m_hPlayerPawn']
        
        view_matrix = [pm.read_float(client + dwViewMatrix + i * 4) for i in range(16)]

        local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
        try:
            local_player_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
        except:
            return
        entity_list = pm.read_longlong(client + dwEntityList)
        entity_ptr = pm.read_longlong(entity_list + 0x10)
    
        for i in range(1, 64):
            try:
                if entity_ptr == 0:
                    break

                entity_controller = pm.read_longlong(entity_ptr + 0x78 * (i & 0x1FF))
                if entity_controller == 0:
                    continue

                entity_controller_pawn = pm.read_longlong(entity_controller + m_hPlayerPawn)
                if entity_controller_pawn == 0:
                    continue

                entity_list_pawn = pm.read_longlong(entity_list + 0x8 * ((entity_controller_pawn & 0x7FFF) >> 0x9) + 0x10)
                if entity_list_pawn == 0:
                    continue

                entity_pawn_addr = pm.read_longlong(entity_list_pawn + 0x78 * (entity_controller_pawn & 0x1FF))
                if entity_pawn_addr == 0 or entity_pawn_addr == local_player_pawn_addr:
                    continue

                entity_team = pm.read_int(entity_pawn_addr + m_iTeamNum)
                if entity_team == local_player_team and settings['esp_mode'] == 0:
                    continue

                entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
                if entity_alive != 256:
                    continue
                
                if settings.get('aim_active', 0) == 1 and settings.get('aim_visibility_check', 0) == 1:
                    m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_entitySpottedState']
                    m_bSpotted = client_dll['client.dll']['classes']['EntitySpottedState_t']['fields']['m_bSpotted']
                    is_visible = pm.read_bool(entity_pawn_addr + m_entitySpottedState + m_bSpotted)
                    if not is_visible:
                        continue
                game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)
                try:
                    
                    
                    aim_mode_idx = int(settings.get('aim_mode', 1))
                    bone_map = {
                        0: 4,  # Body (spine)
                        1: 6,  # Head
                    }
                    
                    
                    bone_id = bone_map.get(aim_mode_idx, 6)  # Default to head if invalid index

                    # Calculate bone positions for head and body only
                    bone_positions = {}
                    bone_ids_to_calc = [4, 5, 6]  # Body (spine), Neck, and Head
                    for bid in bone_ids_to_calc:
                        try:
                            bx = pm.read_float(bone_matrix + bid * 0x20)
                            by = pm.read_float(bone_matrix + bid * 0x20 + 0x4)
                            bz = pm.read_float(bone_matrix + bid * 0x20 + 0x8)
                            bpos = w2s(view_matrix, bx, by, bz, width, height)
                            bone_positions[bid] = bpos
                        except Exception:
                            bone_positions[bid] = (-999, -999)

                    
                    head_pos = bone_positions.get(6, (-999, -999))
                    legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                    leg_pos = w2s(view_matrix, head_pos[0], head_pos[1], legZ, width, height) if head_pos[0] != -999 else (-999, -999)
                    deltaZ = abs(head_pos[1] - leg_pos[1]) if head_pos[1] != -999 and leg_pos[1] != -999 else None

                    
                    any_valid = any(p[0] != -999 and p[1] != -999 for p in bone_positions.values())
                    if any_valid:
                        target_list.append({
                            'bone_positions': bone_positions,
                            'deltaZ': deltaZ,
                            'entity_pawn_addr': entity_pawn_addr
                        })
                except Exception as e:
                    pass
            except:
                return
        return target_list

    def aimbot(target_list, radius, aim_mode_distance, smoothness, pm=None, client=None, offsets=None, client_dll=None):
        """Select a target and move the mouse toward it applying smoothing.

        When 'Lock Target' is enabled, the function will prefer a previously
        locked entity and will only set a new lock when the AimKey edge was
        detected in `main()` (that clears previous lock on fresh press).
        """
        # Load settings for mouse blocking
        try:
            settings = load_settings()
        except Exception:
            settings = {}
        
        if not target_list:
            return

        center_x = win32api.GetSystemMetrics(0) // 2
        center_y = win32api.GetSystemMetrics(1) // 2

        aim_mode_idx = int(settings.get('aim_mode', 2)) if settings.get('aim_mode') is not None else 2
        bone_map = {0:4, 1:5, 2:6}  # 0: Body (spine), 1: Neck, 2: Head

        def _select_bone_for_entity(ent_addr):
            return bone_map.get(aim_mode_idx, 6)  # Default to head

        
        closest = None  
        closest_dist = float('inf')

        if radius == 0:
            for target in target_list:
                ent_addr = target.get('entity_pawn_addr')
                bone_positions = target.get('bone_positions', {})
                bone_id = _select_bone_for_entity(ent_addr)
                pos = bone_positions.get(bone_id, (-999, -999))
                if pos[0] == -999:
                    continue
                dist = ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5
                if dist < closest_dist:
                    closest = (pos, ent_addr)
                    closest_dist = dist
        else:
            screen_radius = radius / 100.0 * min(center_x, center_y)
            if aim_mode_distance == 1:
                
                target_with_max_deltaZ = None
                max_deltaZ = -float('inf')
                for target in target_list:
                    ent_addr = target.get('entity_pawn_addr')
                    bone_positions = target.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(ent_addr)
                    pos = bone_positions.get(bone_id, (-999, -999))
                    if pos[0] == -999:
                        continue
                    dist = ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5
                    if dist < screen_radius and (target.get('deltaZ') or 0) > max_deltaZ:
                        max_deltaZ = target.get('deltaZ') or 0
                        target_with_max_deltaZ = target
                if target_with_max_deltaZ:
                    ent_addr = target_with_max_deltaZ.get('entity_pawn_addr')
                    bone_positions = target_with_max_deltaZ.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(ent_addr)
                    pos = bone_positions.get(bone_id, (-999, -999))
                    if pos[0] != -999:
                        closest = (pos, ent_addr)
            else:
                for target in target_list:
                    ent_addr = target.get('entity_pawn_addr')
                    bone_positions = target.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(ent_addr)
                    pos = bone_positions.get(bone_id, (-999, -999))
                    if pos[0] == -999:
                        continue
                    dist = ((pos[0] - center_x) ** 2 + (pos[1] - center_y) ** 2) ** 0.5
                    if dist < screen_radius and dist < closest_dist:
                        closest = (pos, ent_addr)
                        closest_dist = dist

        if not closest:
            return

        
        try:
            lock_enabled = int(settings.get('aim_lock_target', 0)) == 1
        except Exception:
            lock_enabled = False

        pos, ent_addr = closest
        
        if lock_enabled and aim_lock_state.get('locked_entity') is not None:
            locked_ent = aim_lock_state.get('locked_entity')
            found = None
            for t in target_list:
                if t.get('entity_pawn_addr') == locked_ent:
                    bone_positions = t.get('bone_positions', {})
                    bone_id = _select_bone_for_entity(locked_ent)
                    p = bone_positions.get(bone_id, (-999, -999))
                    if p[0] != -999:
                        found = (p, locked_ent)
                        break
            if found is not None:
                pos, ent_addr = found
            else:
                
                aim_lock_state['locked_entity'] = None

        
        if lock_enabled and aim_lock_state.get('locked_entity') is None:
            aim_lock_state['locked_entity'] = ent_addr

        
        target_x, target_y = pos
        dx = target_x - center_x
        dy = target_y - center_y

        # Use regular smoothness value
        if smoothness is None:
            smoothness = 0

        # Distance-based smoothness modification (applies to both regular and dynamic)
        # Feature removed

        if smoothness <= 0:
            move_x = int(dx)
            move_y = int(dy)
        else:
            # Improved smoothness formula - uses slider's maximum value automatically
            # smoothness 0 = instant (alpha = 1.0)
            # smoothness max = maximum smooth (alpha = 0.0005)
            max_smoothness = float(globals().get('smooth_slider_max', 500000))
            min_alpha = 0.0005  # Minimum movement multiplier (0.05%)
            max_alpha = 1.0     # Maximum movement multiplier (100%)
            
            # Exponential curve for better feel across the range
            normalized_smoothness = min(1.0, smoothness / max_smoothness)
            alpha = min_alpha + (max_alpha - min_alpha) * (1.0 - normalized_smoothness) ** 2
            
            move_x = int(dx * alpha)
            move_y = int(dy * alpha)
            if move_x == 0 and dx != 0:
                move_x = 1 if dx > 0 else -1
            if move_y == 0 and dy != 0:
                move_y = 1 if dy > 0 else -1

        # Check if we should disable aim when crosshair is on enemy
        disable_when_crosshair_on_enemy = settings.get('aim_disable_when_crosshair_on_enemy', 0) == 1
        
        if disable_when_crosshair_on_enemy and pm and client and offsets and client_dll:
            try:
                # Get local player and check what's in crosshair
                dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
                dwEntityList = offsets['client.dll']['dwEntityList']
                m_iIDEntIndex = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_iIDEntIndex']
                m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
                m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
                
                local_player_pawn_addr = pm.read_longlong(client + dwLocalPlayerPawn)
                if local_player_pawn_addr:
                    # Check what entity is in crosshair
                    entity_id = pm.read_int(local_player_pawn_addr + m_iIDEntIndex)
                    
                    if entity_id > 0:
                        # Get the entity in crosshair
                        entity_list = pm.read_longlong(client + dwEntityList)
                        entity_entry = pm.read_longlong(entity_list + 0x8 * (entity_id >> 9) + 0x10)
                        entity = pm.read_longlong(entity_entry + 0x78 * (entity_id & 0x1FF))
                        
                        if entity:
                            entity_team = pm.read_int(entity + m_iTeamNum)
                            entity_health = pm.read_int(entity + m_iHealth)
                            local_team = pm.read_int(local_player_pawn_addr + m_iTeamNum)
                            
                            # If crosshair is on a living enemy, don't move mouse
                            if entity_health > 0 and entity_team != local_team:
                                return  # Exit without moving mouse
                            
            except Exception:
                pass  # If crosshair check fails, continue with normal aim

        # Perform the aimbot mouse movement
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)

    def main(settings):
        import time
        pm = None
        client = None
        
        while pm is None or client is None:
            if is_cs2_running():
                try:
                    pm = pymem.Pymem("cs2.exe")
                    client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
                except Exception:
                    pm = None
                    client = None
                    time.sleep(1)
            else:
                pm = None
                client = None
                time.sleep(1)
        offsets, client_dll = get_offsets_and_client_dll()
        window_size = get_window_size()
        while True:
            target_list = []
            target_list = esp(pm, client, offsets, client_dll, settings, target_list, window_size)
            
            # Check aim key
            try:
                vk = key_str_to_vk(settings.get('AimKey', ''))
            except Exception:
                vk = 0
            try:
                # Check if aim key is on cooldown
                if is_keybind_on_global_cooldown("AimKey"):
                    pressed = False
                else:
                    pressed = vk != 0 and (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
            except Exception:
                pressed = False

            
            
            # Handle normal aim mode
            try:
                if pressed and not aim_lock_state.get('aim_was_pressed', False):
                    aim_lock_state['locked_entity'] = None
                    aim_lock_state['aim_was_pressed'] = True
                if not pressed:
                    
                    aim_lock_state['aim_was_pressed'] = False
            except Exception:
                pass

            if pressed:
                # Use the aim smoothness setting
                smoothness = settings.get('aim_smoothness', 0)
                aimbot(target_list, settings['radius'], settings['aim_mode_distance'], smoothness, pm, client, offsets, client_dll)
            time.sleep(0.001)

    def start_main_thread(settings):
        while True:
            main(settings)

    def setup_watcher(app, settings):
        watcher = QFileSystemWatcher()
        watcher.addPath(CONFIG_FILE)
        def reload_settings():
            new_settings = load_settings()
            settings.update(new_settings)
        watcher.fileChanged.connect(reload_settings)
        app.exec()

    def main_program():
        app = QCoreApplication(sys.argv)
        settings = load_settings()
        threading.Thread(target=start_main_thread, args=(settings,), daemon=True).start()
        setup_watcher(app, settings)

    main_program()

def wait_for_cs2_startup():
    """Wait for CS2 to start and then wait additional 6 seconds"""
    pass
    
    # Wait for CS2 process to appear
    while not is_cs2_running():
        time.sleep(0.5)
    
    # Check if startup delays are enabled
    if STARTUP_ENABLED:
        pass
        time.sleep(25)
        
        # Restart graphics driver
        trigger_graphics_restart()
        
        pass

if __name__ == "__main__":
    
    try:
        multiprocessing.freeze_support()
    except Exception:
        pass

    # Check for existing instance and handle user choice
    if not handle_instance_check():
        sys.exit(0)
    
    # Create lock file to indicate this instance is running
    if not create_lock_file():
        ctypes.windll.user32.MessageBoxW(
            0,
            "Failed to create lock file. Another instance may be starting.",
            "Popsicle CS2 - Error",
            0x00000010 | 0x00010000 | 0x00040000  # MB_ICONERROR | MB_SETFOREGROUND | MB_TOPMOST
        )
        sys.exit(0)
    
    MB_OK = 0x00000000
    MB_OKCANCEL = 0x00000001
    MB_SETFOREGROUND = 0x00010000
    MB_TOPMOST = 0x00040000
    MB_SYSTEMMODAL = 0x00001000
    IDOK = 1
    IDCANCEL = 2
    
    # Check if CS2 is already running
    if is_cs2_running():
        # Check if startup delays are enabled
        if STARTUP_ENABLED:
            pass
            time.sleep(4)
            
            # Restart graphics driver
            trigger_graphics_restart()
            
            pass
        # CS2 is already running, start everything after delay
        pm = None
        try:
            pm = pymem.Pymem("cs2.exe")
        except Exception:
            pass
    else:
        # CS2 is not running, show message and wait
        result = ctypes.windll.user32.MessageBoxW(0, "Waiting for CS2.exe", "Popsicle CS2", MB_OKCANCEL | MB_SETFOREGROUND | MB_TOPMOST | MB_SYSTEMMODAL)
        if result != IDOK:
            # User clicked Cancel or closed the dialog, exit the script
            remove_lock_file()
            try:
                if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                    os.remove(KEYBIND_COOLDOWNS_FILE)
            except Exception:
                pass
            sys.exit(0)
        
        # Wait for CS2 to start and then wait 6 seconds
        wait_for_cs2_startup()
        
        # Now ensure CS2 is accessible
        pm = None
        while pm is None:
            try:
                pm = pymem.Pymem("cs2.exe")
                break
            except Exception:
                time.sleep(1)


    procs = [
        multiprocessing.Process(target=configurator),
        multiprocessing.Process(target=esp_main),
        multiprocessing.Process(target=triggerbot),
        multiprocessing.Process(target=aim),
        multiprocessing.Process(target=bhop),
    ]
    for p in procs:
        p.start()

    try:
        
        
        while True:
            time.sleep(1)
            
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                break
            # Use the new CS2 detection function instead of trying to create pymem object
            if not is_cs2_running():
                pass
                break
    finally:
        for p in procs:
            try:
                if p.is_alive():
                    p.terminate()
                    p.join(1)
            except Exception:
                pass
        
        # Clean up files
        remove_lock_file()
        try:
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                os.remove(TERMINATE_SIGNAL_FILE)
        except Exception:
            pass
        try:
            if os.path.exists(KEYBIND_COOLDOWNS_FILE):
                os.remove(KEYBIND_COOLDOWNS_FILE)
        except Exception:
            pass
        sys.exit(0)


