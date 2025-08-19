from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import QFileSystemWatcher, QCoreApplication
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from qt_material import apply_stylesheet
import multiprocessing
import threading
import requests
import pymem
import pymem.process
import win32api
import win32con
import win32gui
from pynput.mouse import Controller, Button
import json
import os
import sys
import time
import random
import ctypes

def key_str_to_vk(key_str):
    import win32con
    if not key_str:
        return 0
    ks = str(key_str).strip().upper()
    if len(ks) == 1:
        return ord(ks)
    if ks.startswith('F') and ks[1:].isdigit():
        try:
            n = int(ks[1:])
            if 1 <= n <= 24:
                return 0x70 + (n - 1)
        except Exception:
            pass
    key_map = {
        'LMB': 0x01, 'LEFTMOUSE': 0x01, 'MOUSE1': 0x01,
        'RMB': 0x02, 'RIGHTMOUSE': 0x02, 'MOUSE2': 0x02,
        'SPACE': win32con.VK_SPACE, 'ENTER': win32con.VK_RETURN,
        'SHIFT': win32con.VK_SHIFT, 'CTRL': win32con.VK_CONTROL,
        'ALT': win32con.VK_MENU, 'TAB': win32con.VK_TAB,
        'ESC': win32con.VK_ESCAPE, 'UP': win32con.VK_UP,
        'DOWN': win32con.VK_DOWN, 'LEFT': win32con.VK_LEFT,
        'RIGHT': win32con.VK_RIGHT,
        'RALT': getattr(win32con, 'VK_RMENU', 0xA5), 'RIGHTALT': getattr(win32con, 'VK_RMENU', 0xA5),
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
    return ord(ks[0])

CONFIG_DIR = os.getcwd()
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
TERMINATE_SIGNAL_FILE = os.path.join(CONFIG_DIR, 'terminate_now.signal')

DEFAULT_SETTINGS = {
    "esp_rendering": 1,
    "esp_mode": 1,
    "line_rendering": 1,
    "hp_bar_rendering": 1,
    "head_hitbox_rendering": 1,
    "bons": 1,
    "nickname": 1,
    "radius": 50,
    "AimKey": "C",
    "aim_active": 0,
    "aim_mode": 1,
    "aim_mode_distance": 1,
    "trigger_bot_active": 0,
    "TriggerKey": "X", 
    "weapon": 1,
    "bomb_esp": 1,
    "circle_opacity": 16,
    "aim_smoothness": 50,
    "topmost": 1,
    "MenuToggleKey": "F8",
    "theme": "dark_red.xml",
    "team_color": "#47A76A",
    "enemy_color": "#C41E3A",
    "aim_circle_color": "#FF0000"
}

# new: available themes
THEMES = ['dark_red.xml','dark_amber.xml','dark_blue.xml','dark_cyan.xml','dark_lightgreen.xml','dark_pink.xml','dark_purple.xml','dark_teal.xml','dark_yellow.xml','light_amber.xml','light_blue.xml','light_cyan.xml','light_cyan_500.xml','light_lightgreen.xml','light_pink.xml','light_purple.xml','light_red.xml','light_teal.xml','light_yellow.xml']

BombPlantedTime = 0
BombDefusedTime = 0


def load_settings():
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

def save_settings(settings):
    tmp_file = CONFIG_FILE + ".tmp"
    with open(tmp_file, "w") as f:
        json.dump(settings, f, indent=4)
    os.replace(tmp_file, CONFIG_FILE)

def get_offsets_and_client_dll():
    offsets = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json').json()
    client_dll = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json').json()
    return offsets, client_dll

def get_window_size(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd:
        rect = win32gui.GetClientRect(hwnd)
        return rect[2], rect[3]
    return None, None

def w2s(mtx, posx, posy, posz, width, height):
    screenW = (mtx[12] * posx) + (mtx[13] * posy) + (mtx[14] * posz) + mtx[15]
    if screenW > 0.001:
        screenX = (mtx[0] * posx) + (mtx[1] * posy) + (mtx[2] * posz) + mtx[3]
        screenY = (mtx[4] * posx) + (mtx[5] * posy) + (mtx[6] * posz) + mtx[7]
        camX = width / 2
        camY = height / 2
        x = camX + (camX * screenX / screenW)
        y = camY - (camY * screenY / screenW)
        return [int(x), int(y)]
    return [-999, -999]

# Конфигуратор
class ConfigWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.initUI()
        # apply initial topmost after UI widgets are created
        try:
            self.apply_topmost()
        except Exception:
            pass
        # used to detect key press edge for menu toggle
        self.menu_toggle_pressed = False
        self.is_dragging = False
        self.drag_start_position = None
        self.setStyleSheet("background-color: #020203;")

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        # smaller overall window so containers appear smaller
        self.setFixedSize(700, 700)

        # use a 2x2 grid layout for containers (ESP | Aim / Trigger | Misc)
        main_layout = QtWidgets.QGridLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # add header label at the top
        header_label = QtWidgets.QLabel("Popsicle CS2 External")
        header_label.setAlignment(QtCore.Qt.AlignCenter)
        header_label.setMinimumHeight(28)
        header_font = QtGui.QFont('DejaVu Sans Mono', 17, QtGui.QFont.Bold)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: white;")
        main_layout.addWidget(header_label, 0, 0, 1, 2)

        # create the four containers (reuse existing factory methods)
        esp_container = self.create_esp_container()
        aim_container = self.create_aim_container()
        trigger_container = self.create_trigger_container()
        misc_container = self.create_misc_container()

        # place them in a 2x2 grid (shifted down one row because of header)
        main_layout.addWidget(esp_container, 1, 0)
        main_layout.addWidget(aim_container, 1, 1)
        main_layout.addWidget(trigger_container, 2, 0)
        main_layout.addWidget(misc_container, 2, 1)

        # make cells expand evenly; keep header compact
        main_layout.setRowStretch(0, 0)
        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(2, 1)
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)

        self.setLayout(main_layout)

        # poll menu toggle key (50ms)
        self._menu_toggle_timer = QtCore.QTimer(self)
        self._menu_toggle_timer.timeout.connect(self.check_menu_toggle)
        self._menu_toggle_timer.start(50)

        # ignore menu toggle for a short period after startup so menu stays visible by default
        try:
            self._menu_toggle_ignore_until = time.time() + 0.5
        except Exception:
            self._menu_toggle_ignore_until = 0

    

    def create_esp_container(self):
        esp_container = QtWidgets.QWidget()
        esp_layout = QtWidgets.QVBoxLayout()
        esp_layout.setSpacing(6)
        esp_layout.setContentsMargins(6, 6, 6, 6)

        esp_label = QtWidgets.QLabel("ESP Settings")
        esp_label.setAlignment(QtCore.Qt.AlignCenter)
        esp_label.setMinimumHeight(20)
        esp_layout.addWidget(esp_label)

        self.esp_rendering_cb = QtWidgets.QCheckBox("Enable ESP")
        self.esp_rendering_cb.setChecked(self.settings["esp_rendering"] == 1)
        self.esp_rendering_cb.stateChanged.connect(self.save_settings)
        self.esp_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_rendering_cb)

        self.esp_mode_cb = QtWidgets.QComboBox()
        self.esp_mode_cb.addItems(["Enemies Only", "All Players"])
        self.esp_mode_cb.setCurrentIndex(self.settings["esp_mode"])
        self.esp_mode_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.esp_mode_cb.currentIndexChanged.connect(self.save_settings)
        self.esp_mode_cb.setMinimumHeight(22)
        self.esp_mode_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.esp_mode_cb)

        self.line_rendering_cb = QtWidgets.QCheckBox("Draw Lines")
        self.line_rendering_cb.setChecked(self.settings["line_rendering"] == 1)
        self.line_rendering_cb.stateChanged.connect(self.save_settings)
        self.line_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.line_rendering_cb)

        self.hp_bar_rendering_cb = QtWidgets.QCheckBox("Draw HP Bars")
        self.hp_bar_rendering_cb.setChecked(self.settings["hp_bar_rendering"] == 1)
        self.hp_bar_rendering_cb.stateChanged.connect(self.save_settings)
        self.hp_bar_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.hp_bar_rendering_cb)

        self.head_hitbox_rendering_cb = QtWidgets.QCheckBox("Draw Head Hitbox")
        self.head_hitbox_rendering_cb.setChecked(self.settings["head_hitbox_rendering"] == 1)
        self.head_hitbox_rendering_cb.stateChanged.connect(self.save_settings)
        self.head_hitbox_rendering_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.head_hitbox_rendering_cb)

        self.bons_cb = QtWidgets.QCheckBox("Draw bons")
        self.bons_cb.setChecked(self.settings["bons"] == 1)
        self.bons_cb.stateChanged.connect(self.save_settings)
        self.bons_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.bons_cb)

        self.nickname_cb = QtWidgets.QCheckBox("Show Nickname")
        self.nickname_cb.setChecked(self.settings["nickname"] == 1)
        self.nickname_cb.stateChanged.connect(self.save_settings)
        self.nickname_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.nickname_cb)

        self.weapon_cb = QtWidgets.QCheckBox("Show Weapon")
        self.weapon_cb.setChecked(self.settings["weapon"] == 1)
        self.weapon_cb.stateChanged.connect(self.save_settings)
        self.weapon_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.weapon_cb)

        self.bomb_esp_cb = QtWidgets.QCheckBox("Bomb ESP")
        self.bomb_esp_cb.setChecked(self.settings["bomb_esp"] == 1)
        self.bomb_esp_cb.stateChanged.connect(self.save_settings)
        self.bomb_esp_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        esp_layout.addWidget(self.bomb_esp_cb)

        esp_container.setLayout(esp_layout)
        esp_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return esp_container

    def create_trigger_container(self):
        trigger_container = QtWidgets.QWidget()
        trigger_layout = QtWidgets.QVBoxLayout()
        trigger_layout.setSpacing(6)
        trigger_layout.setContentsMargins(6, 6, 6, 6)

        trigger_label = QtWidgets.QLabel("Trigger Bot Settings")
        trigger_label.setAlignment(QtCore.Qt.AlignCenter)
        trigger_label.setMinimumHeight(18)
        trigger_layout.addWidget(trigger_label)

        self.trigger_bot_active_cb = QtWidgets.QCheckBox("Enable Trigger Bot")
        self.trigger_bot_active_cb.setChecked(self.settings["trigger_bot_active"] == 1)
        self.trigger_bot_active_cb.stateChanged.connect(self.save_settings)
        self.trigger_bot_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_bot_active_cb)

        # Trigger key binder button (moved from Misc)
        self.trigger_key_btn = QtWidgets.QPushButton(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
        self.trigger_key_btn.clicked.connect(lambda: self.record_key('TriggerKey', self.trigger_key_btn))
        self.trigger_key_btn.setMinimumHeight(22)
        self.trigger_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        trigger_layout.addWidget(self.trigger_key_btn)

        trigger_container.setLayout(trigger_layout)
        trigger_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return trigger_container

    def create_aim_container(self):
        aim_container = QtWidgets.QWidget()
        aim_layout = QtWidgets.QVBoxLayout()
        aim_layout.setSpacing(6)
        aim_layout.setContentsMargins(6, 6, 6, 6)

        aim_label = QtWidgets.QLabel("Aim Settings")
        aim_label.setAlignment(QtCore.Qt.AlignCenter)
        aim_label.setMinimumHeight(18)
        aim_layout.addWidget(aim_label)

        self.aim_active_cb = QtWidgets.QCheckBox("Enable Aim")
        self.aim_active_cb.setChecked(self.settings["aim_active"] == 1)
        self.aim_active_cb.stateChanged.connect(self.save_settings)
        self.aim_active_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_active_cb)

        self.radius_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.radius_slider.setMinimum(0)
        self.radius_slider.setMaximum(100)
        self.radius_slider.setValue(self.settings["radius"])
        self.radius_slider.valueChanged.connect(self.save_settings)
        lbl_radius = QtWidgets.QLabel("Aim Radius:")
        lbl_radius.setMinimumHeight(16)
        aim_layout.addWidget(lbl_radius)
        self.radius_slider.setMinimumHeight(18)
        self.radius_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.radius_slider)

    # Aim Key textbox removed; use the binder button below to set AimKey

        # Aim key binder button (moved from Misc)
        self.aim_key_btn = QtWidgets.QPushButton(f"AimKey: {self.settings.get('AimKey', 'C')}")
        self.aim_key_btn.clicked.connect(lambda: self.record_key('AimKey', self.aim_key_btn))
        self.aim_key_btn.setMinimumHeight(22)
        self.aim_key_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_key_btn)

        self.aim_mode_cb = QtWidgets.QComboBox()
        # add new "Random" aim mode (index 2)
        self.aim_mode_cb.addItems(["Body", "Head", "Random"])
        self.aim_mode_cb.setCurrentIndex(self.settings["aim_mode"])
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
        self.aim_mode_distance_cb.setCurrentIndex(self.settings["aim_mode_distance"])
        self.aim_mode_distance_cb.setStyleSheet("background-color: #020203; border-radius: 5px;")
        self.aim_mode_distance_cb.currentIndexChanged.connect(self.save_settings)
        lbl_aimdist = QtWidgets.QLabel("Aim Distance Mode:")
        lbl_aimdist.setMinimumHeight(16)
        aim_layout.addWidget(lbl_aimdist)
        self.aim_mode_distance_cb.setMinimumHeight(22)
        self.aim_mode_distance_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.aim_mode_distance_cb)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(255)
        self.opacity_slider.setValue(self.settings.get("circle_opacity", 16))
        self.opacity_slider.valueChanged.connect(self.save_settings)
        lbl_opacity = QtWidgets.QLabel("Circle Opacity:")
        lbl_opacity.setMinimumHeight(16)
        aim_layout.addWidget(lbl_opacity)
        self.opacity_slider.setMinimumHeight(18)
        self.opacity_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.opacity_slider)

        # Aim smoothness slider (0 = instant, 100 = smooth/slow)
        self.smooth_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.smooth_slider.setMinimum(0)
        self.smooth_slider.setMaximum(100)
        self.smooth_slider.setValue(self.settings.get("aim_smoothness", 50))
        self.smooth_slider.valueChanged.connect(self.save_settings)
        lbl_smooth = QtWidgets.QLabel("Aim Smoothness:")
        lbl_smooth.setMinimumHeight(16)
        aim_layout.addWidget(lbl_smooth)
        self.smooth_slider.setMinimumHeight(18)
        self.smooth_slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        aim_layout.addWidget(self.smooth_slider)

        aim_container.setLayout(aim_layout)
        aim_container.setStyleSheet("background-color: #080809; border-radius: 10px;")
        return aim_container

    def create_misc_container(self):
        misc_container = QtWidgets.QWidget()
        misc_layout = QtWidgets.QVBoxLayout()
        misc_layout.setSpacing(6)
        misc_layout.setContentsMargins(6, 6, 6, 6)

        misc_label = QtWidgets.QLabel("Miscellaneous")
        misc_label.setAlignment(QtCore.Qt.AlignCenter)
        misc_label.setMinimumHeight(18)
        misc_layout.addWidget(misc_label)

        self.topmost_cb = QtWidgets.QCheckBox("Topmost")
        self.topmost_cb.setChecked(self.settings.get("topmost", 0) == 1)
        self.topmost_cb.stateChanged.connect(self.on_topmost_changed)
        self.topmost_cb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.topmost_cb)

        # Theme selection dropdown (new)
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
        self.theme_combo.setMaximumWidth(200)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        lbl_theme = QtWidgets.QLabel("Theme:")
        lbl_theme.setMinimumHeight(16)
        misc_layout.addWidget(lbl_theme)
        self.theme_combo.setMinimumHeight(22)
        self.theme_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        misc_layout.addWidget(self.theme_combo)

        # Key recorder button for Menu
        key_row = QtWidgets.QHBoxLayout()
        self.menu_key_btn = QtWidgets.QPushButton(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'M')}")
        self.menu_key_btn.clicked.connect(lambda: self.record_key('MenuToggleKey', self.menu_key_btn))
        key_row.addWidget(self.menu_key_btn)
        misc_layout.addLayout(key_row)

        # Color pickers for team/enemy/aim circle
        color_row = QtWidgets.QHBoxLayout()
        self.team_color_btn = QtWidgets.QPushButton('Team Color')
        team_hex = self.settings.get('team_color', '#47A76A')
        self.team_color_btn.setStyleSheet(f'background-color: {team_hex}; color: white;')
        self.team_color_btn.clicked.connect(lambda: self.pick_color('team_color', self.team_color_btn))
        color_row.addWidget(self.team_color_btn)

        self.enemy_color_btn = QtWidgets.QPushButton('Enemy Color')
        enemy_hex = self.settings.get('enemy_color', '#C41E3A')
        self.enemy_color_btn.setStyleSheet(f'background-color: {enemy_hex}; color: white;')
        self.enemy_color_btn.clicked.connect(lambda: self.pick_color('enemy_color', self.enemy_color_btn))
        color_row.addWidget(self.enemy_color_btn)

        self.aim_circle_color_btn = QtWidgets.QPushButton('Aim Circle')
        aim_hex = self.settings.get('aim_circle_color', '#FF0000')
        self.aim_circle_color_btn.setStyleSheet(f'background-color: {aim_hex}; color: white;')
        self.aim_circle_color_btn.clicked.connect(lambda: self.pick_color('aim_circle_color', self.aim_circle_color_btn))
        color_row.addWidget(self.aim_circle_color_btn)

        misc_layout.addLayout(color_row)

        # add an Exit button that signals the parent to terminate all processes
        self.terminate_btn = QtWidgets.QPushButton("Exit Script")
        self.terminate_btn.setToolTip("Close Script")
        self.terminate_btn.clicked.connect(self.on_terminate_clicked)
        self.terminate_btn.setMinimumHeight(22)
        self.terminate_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        # Reset to defaults button
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

    def on_topmost_changed(self):
        # persist and apply immediately
        try:
            self.settings["topmost"] = 1 if self.topmost_cb.isChecked() else 0
            save_settings(self.settings)
            self.apply_topmost()
        except Exception:
            pass

    def apply_topmost(self):
        # add or remove WindowStaysOnTopHint based on checkbox/state
        flags = self.windowFlags()
        if self.settings.get("topmost", 0) == 1:
            flags |= QtCore.Qt.WindowStaysOnTopHint
        else:
            flags &= ~QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        # re-show to apply flag change
        self.show()

    def on_theme_changed(self):
        # update settings and apply stylesheet immediately
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

    # new: when clicked, create the terminate signal file and close the configurator UI
    def on_terminate_clicked(self):
        try:
            # create or overwrite the signal file so the parent can detect it
            with open(TERMINATE_SIGNAL_FILE, 'w') as f:
                f.write('terminate')
        except Exception:
            pass
        try:
            # close configurator UI immediately
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
        # assemble list of widget references we may update; use getattr to be safe
        widget_names = [
            'esp_rendering_cb', 'esp_mode_cb', 'line_rendering_cb', 'hp_bar_rendering_cb',
            'head_hitbox_rendering_cb', 'bons_cb', 'nickname_cb', 'weapon_cb', 'bomb_esp_cb',
            'trigger_bot_active_cb', 'aim_active_cb', 'radius_slider', 'opacity_slider',
            'smooth_slider', 'aim_key_btn', 'trigger_key_btn', 'menu_key_btn', 'theme_combo',
            'team_color_btn', 'enemy_color_btn', 'aim_circle_color_btn', 'topmost_cb'
        ]
        widgets = [getattr(self, name, None) for name in widget_names]

        try:
            # set settings to defaults and persist immediately
            self.settings = DEFAULT_SETTINGS.copy()
            save_settings(self.settings)

            # block signals so intermediate changes don't trigger save_settings repeatedly
            for w in widgets:
                try:
                    if w is not None:
                        w.blockSignals(True)
                except Exception:
                    pass

            # apply values to widgets (use safe getattr checks)
            try:
                if getattr(self, 'esp_rendering_cb', None) is not None:
                    self.esp_rendering_cb.setChecked(self.settings.get('esp_rendering', 1) == 1)
                if getattr(self, 'esp_mode_cb', None) is not None:
                    self.esp_mode_cb.setCurrentIndex(self.settings.get('esp_mode', 1))

                # checkboxes
                mapping = {
                    'line_rendering_cb': 'line_rendering',
                    'hp_bar_rendering_cb': 'hp_bar_rendering',
                    'head_hitbox_rendering_cb': 'head_hitbox_rendering',
                    'bons_cb': 'bons',
                    'nickname_cb': 'nickname',
                    'weapon_cb': 'weapon',
                    'bomb_esp_cb': 'bomb_esp',
                    'trigger_bot_active_cb': 'trigger_bot_active',
                    'aim_active_cb': 'aim_active',
                    'topmost_cb': 'topmost'
                }
                for cb_name, key in mapping.items():
                    cb = getattr(self, cb_name, None)
                    if cb is not None:
                        cb.setChecked(self.settings.get(key, 0) == 1)

                # sliders
                if getattr(self, 'radius_slider', None) is not None:
                    self.radius_slider.setValue(self.settings.get('radius', 50))
                if getattr(self, 'opacity_slider', None) is not None:
                    self.opacity_slider.setValue(self.settings.get('circle_opacity', 16))
                if getattr(self, 'smooth_slider', None) is not None:
                    self.smooth_slider.setValue(self.settings.get('aim_smoothness', 50))

                # key/button labels
                if getattr(self, 'aim_key_btn', None) is not None:
                    self.aim_key_btn.setText(f"AimKey: {self.settings.get('AimKey', 'C')}")
                if getattr(self, 'trigger_key_btn', None) is not None:
                    self.trigger_key_btn.setText(f"TriggerKey: {self.settings.get('TriggerKey', 'X')}")
                if getattr(self, 'menu_key_btn', None) is not None:
                    self.menu_key_btn.setText(f"MenuToggleKey: {self.settings.get('MenuToggleKey', 'F8')}")

                # theme combo
                if getattr(self, 'theme_combo', None) is not None:
                    theme = self.settings.get('theme', DEFAULT_SETTINGS.get('theme'))
                    for i in range(self.theme_combo.count()):
                        if str(self.theme_combo.itemData(i)) == str(theme):
                            self.theme_combo.setCurrentIndex(i)
                            break

                # color buttons
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

                # apply theme immediately
                try:
                    app = QtWidgets.QApplication.instance()
                    if app is not None:
                        try:
                            apply_stylesheet(app, theme=self.settings.get('theme', DEFAULT_SETTINGS.get('theme')))
                        except Exception:
                            pass
                except Exception:
                    pass

                # persist topmost and apply
                try:
                    if getattr(self, 'topmost_cb', None) is not None:
                        # topmost_cb already set above; ensure flag is applied
                        self.apply_topmost()
                except Exception:
                    pass

            except Exception as e:
                print(f"Error applying defaults to widgets: {e}")
        finally:
            # unblock signals and save final settings once
            for w in widgets:
                try:
                    if w is not None:
                        w.blockSignals(False)
                except Exception:
                    pass
            try:
                save_settings(self.settings)
            except Exception:
                pass

    def save_settings(self):
        # persist simple checkboxes / sliders
        self.settings["esp_rendering"] = 1 if self.esp_rendering_cb.isChecked() else 0
        self.settings["esp_mode"] = self.esp_mode_cb.currentIndex()
        self.settings["line_rendering"] = 1 if self.line_rendering_cb.isChecked() else 0
        self.settings["hp_bar_rendering"] = 1 if self.hp_bar_rendering_cb.isChecked() else 0
        self.settings["head_hitbox_rendering"] = 1 if self.head_hitbox_rendering_cb.isChecked() else 0
        self.settings["bons"] = 1 if self.bons_cb.isChecked() else 0
        self.settings["nickname"] = 1 if self.nickname_cb.isChecked() else 0
        self.settings["weapon"] = 1 if self.weapon_cb.isChecked() else 0
        self.settings["bomb_esp"] = 1 if self.bomb_esp_cb.isChecked() else 0
        self.settings["aim_active"] = 1 if self.aim_active_cb.isChecked() else 0

        # sliders
        self.settings["radius"] = self.radius_slider.value()

        # AimKey: read from the binder button if present, otherwise keep existing setting
        try:
            if getattr(self, "aim_key_btn", None) is not None:
                # expected format "Aim: <KEY>"
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

        # trigger bot checkbox
        self.settings["trigger_bot_active"] = 1 if self.trigger_bot_active_cb.isChecked() else 0

        # TriggerKey is set via the keybinder button (record_key) which persists immediately;
        # ensure we don't try to access missing inputs
        try:
            if getattr(self, 'trigger_key_btn', None) is not None:
                text = self.trigger_key_btn.text()
                if ':' in text:
                    val = text.split(':', 1)[1].strip()
                    if val:
                        self.settings["TriggerKey"] = val
        except Exception:
            pass

        # circle opacity
        self.settings["circle_opacity"] = self.opacity_slider.value()

        # persist topmost setting if UI present
        try:
            self.settings["topmost"] = 1 if self.topmost_cb.isChecked() else 0
        except Exception:
            pass

        # persist menu toggle key (if UI present) - store canonical value
        try:
            val = getattr(self, "menu_key_combo", None)
            if val is not None:
                self.settings["MenuToggleKey"] = val.itemData(val.currentIndex())
        except Exception:
            pass

        # persist theme selection if UI present
        try:
            val = getattr(self, "theme_combo", None)
            if val is not None:
                self.settings["theme"] = val.itemData(val.currentIndex())
        except Exception:
            pass

        # persist new smoothness setting
        try:
            self.settings["aim_smoothness"] = self.smooth_slider.value()
        except Exception:
            pass

        save_settings(self.settings)

    def record_key(self, settings_key: str, btn: QtWidgets.QPushButton):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle('Press a key')
        dialog.setModal(True)
        lbl = QtWidgets.QLabel('Press desired key now...')
        v = QtWidgets.QVBoxLayout(dialog)
        v.addWidget(lbl)

        timer = QtCore.QTimer(dialog)

        def check():
            for code in range(0x08, 0xFF):
                try:
                    if (win32api.GetAsyncKeyState(code) & 0x8000) != 0:
                        if 0x30 <= code <= 0x5A:
                            val = chr(code)
                        elif 0x70 <= code <= 0x87:
                            val = f'F{code - 0x6F}'
                        elif code == 0xA5:
                            val = 'RALT'
                        else:
                            val = str(code)
                        self.settings[settings_key] = val
                        save_settings(self.settings)
                        # update button label
                        short = settings_key
                        if '_' in settings_key:
                            short = settings_key.split('_')[0]
                        btn.setText(f"{short.capitalize()}: {val}")
                        timer.stop()
                        dialog.accept()
                        return
                except Exception:
                    continue

        timer.timeout.connect(check)
        timer.start(20)
        dialog.exec()

    def pick_color(self, settings_key: str, btn: QtWidgets.QPushButton):
        init = QtGui.QColor(self.settings.get(settings_key, '#FFFFFF'))
        col = QtWidgets.QColorDialog.getColor(init, self, f'Choose {settings_key}')
        if col.isValid():
            hexc = col.name()
            self.settings[settings_key] = hexc
            save_settings(self.settings)
            btn.setStyleSheet(f'background-color: {hexc}; color: white;')

    def check_menu_toggle(self):
        # edge-detect configured key and toggle visibility
        try:
            # skip checking for a short startup interval to ensure menu is visible by default
            if getattr(self, "_menu_toggle_ignore_until", 0) > time.time():
                return
            key = self.settings.get("MenuToggleKey", "M")
            # if explicitly None/NONE/empty -> do not toggle
            if not key or str(key).upper() == "NONE":
                return
            vk = key_str_to_vk(key)
            pressed = (win32api.GetAsyncKeyState(vk) & 0x8000) != 0
            if pressed and not self.menu_toggle_pressed:
                # toggle visibility
                if self.isVisible():
                    self.hide()
                else:
                    # ensure flag changes (topmost) applied when showing
                    try:
                        self.apply_topmost()
                    except Exception:
                        pass
                    self.show()
                self.menu_toggle_pressed = True
            elif not pressed:
                self.menu_toggle_pressed = False
        except Exception:
            pass

    # ensure inputs cannot be typed into while hidden
    def hideEvent(self, event: QtGui.QHideEvent):
        try:
            # disable line edits (prevents typing/focus) and clear focus
            for le in (getattr(self, 'trigger_key_input', None), getattr(self, 'keyboard_input', None), getattr(self, 'menu_key_combo', None)):
                if le is not None:
                    le.setEnabled(False)
                    le.clearFocus()
        except Exception:
            pass
        super().hideEvent(event)
    
    def showEvent(self, event: QtGui.QShowEvent):
        try:
            # re-enable line edits when shown
            for le in (getattr(self, 'trigger_key_input', None), getattr(self, 'keyboard_input', None), getattr(self, 'menu_key_combo', None)):
                if le is not None:
                    le.setEnabled(True)
        except Exception:
            pass
        super().showEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.drag_start_position
            self.move(self.pos() + delta)
            self.drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton:
            self.is_dragging = False

def configurator():
    app = QtWidgets.QApplication(sys.argv)
    # apply saved theme (fallback to default in settings)
    try:
        settings = load_settings()
        theme = settings.get("theme", "dark_red.xml")
    except Exception:
        theme = "dark_red.xml"
    try:
        apply_stylesheet(app, theme=theme)
    except Exception:
        # fallback to default theme if apply fails
        try:
            apply_stylesheet(app, theme='dark_red.xml')
        except Exception:
            pass
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec())

# ESP
class ESPWindow(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle('ESP Overlay')
        self.window_width, self.window_height = get_window_size("Counter-Strike 2")
        if self.window_width is None or self.window_height is None:
            print("Ошибка: окно игры не найдено.")
            sys.exit(1)
        self.setGeometry(0, 0, self.window_width, self.window_height)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        hwnd = self.winId()
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

        self.file_watcher = QFileSystemWatcher([CONFIG_FILE])
        self.file_watcher.fileChanged.connect(self.reload_settings)

        self.offsets, self.client_dll = get_offsets_and_client_dll()
        self.pm = pymem.Pymem("cs2.exe")
        self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, self.window_width, self.window_height)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setStyleSheet("background: transparent;")
        self.view.setSceneRect(0, 0, self.window_width, self.window_height)
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(0)  # Update as fast as possible

        self.last_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def reload_settings(self):
        self.settings = load_settings()
        self.window_width, self.window_height = get_window_size("Counter-Strike 2")
        if self.window_width is None or self.window_height is None:
            print("Ошибка: окно игры не найдено.")
            sys.exit(1)
        self.setGeometry(0, 0, self.window_width, self.window_height)
        self.update_scene()

    def update_scene(self):
        if not self.is_game_window_active():
            self.scene.clear()
            return

        self.scene.clear()
        try:
            esp(self.scene, self.pm, self.client, self.offsets, self.client_dll, self.window_width, self.window_height, self.settings)
            current_time = time.time()
            self.frame_count += 1
            if current_time - self.last_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_time = current_time
            fps_text = self.scene.addText(f"Popsicle CS2 | FPS: {self.fps}", QtGui.QFont('DejaVu Sans', 15, QtGui.QFont.Bold))
            fps_text.setPos(5, 5)
            fps_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))
        except Exception as e:
            print(f"Scene Update Error: {e}")
            QtWidgets.QApplication.quit()

    def is_game_window_active(self):
        hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
        if hwnd:
            foreground_hwnd = win32gui.GetForegroundWindow()
            return hwnd == foreground_hwnd
        return False

def esp(scene, pm, client, offsets, client_dll, window_width, window_height, settings):
    # Draw aim circle independently of ESP toggle, controlled by the "Enable Aim" toggle (aim_active)
    try:
        if settings.get('aim_active', 0) == 1 and 'radius' in settings and settings.get('radius', 0) != 0:
            center_x = window_width / 2
            center_y = window_height / 2
            screen_radius = settings['radius'] / 100.0 * min(center_x, center_y)
            opacity = settings.get("circle_opacity", 16)
            # draw once per frame (outline only, no fill)
            aim_hex = settings.get('aim_circle_color', '#FF0000')
            aim_qcolor = QtGui.QColor(aim_hex)
            aim_qcolor.setAlpha(opacity)
            scene.addEllipse(
                QtCore.QRectF(center_x - screen_radius, center_y - screen_radius, screen_radius * 2, screen_radius * 2),
                QtGui.QPen(aim_qcolor, 1),
                QtCore.Qt.NoBrush
            )
    except Exception:
        # silently ignore drawing errors so it won't break ESP loop
        pass

    if settings.get('esp_rendering', 1) == 0:
        return

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

    if settings.get('bomb_esp', 0) == 1:
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

            entity_hp = pm.read_int(entity_pawn_addr + m_iHealth)
            armor_hp = pm.read_int(entity_pawn_addr + m_ArmorValue)
            if entity_hp <= 0:
                continue

            entity_alive = pm.read_int(entity_pawn_addr + m_lifeState)
            if entity_alive != 256:
                continue

            weapon_pointer = pm.read_longlong(entity_pawn_addr + m_pClippingWeapon)
            weapon_index = pm.read_int(weapon_pointer + m_AttributeManager + m_Item + m_iItemDefinitionIndex)
            weapon_name = get_weapon_name_by_index(weapon_index)

            # use configured colors (hex strings) for team/enemy
            try:
                team_hex = settings.get('team_color', '#47A76A')
                enemy_hex = settings.get('enemy_color', '#C41E3A')
                team_q = QtGui.QColor(team_hex)
                enemy_q = QtGui.QColor(enemy_hex)
                color = team_q if entity_team == local_player_team else enemy_q
            except Exception:
                color = QtGui.QColor(71, 167, 106) if entity_team == local_player_team else QtGui.QColor(196, 30, 58)
            game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
            bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)

            try:
                headX = pm.read_float(bone_matrix + 6 * 0x20)
                headY = pm.read_float(bone_matrix + 6 * 0x20 + 0x4)
                headZ = pm.read_float(bone_matrix + 6 * 0x20 + 0x8) + 8
                head_pos = w2s(view_matrix, headX, headY, headZ, window_width, window_height)
                if head_pos[1] < 0:
                    continue
                if settings['line_rendering'] == 1:
                    legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                    leg_pos = w2s(view_matrix, headX, headY, legZ, window_width, window_height)
                    bottom_left_x = head_pos[0] - (head_pos[0] - leg_pos[0]) // 2
                    bottom_y = leg_pos[1]
                    line = scene.addLine(bottom_left_x, bottom_y, no_center_x, no_center_y, QtGui.QPen(color, 1))

                legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                leg_pos = w2s(view_matrix, headX, headY, legZ, window_width, window_height)
                deltaZ = abs(head_pos[1] - leg_pos[1])
                leftX = head_pos[0] - deltaZ // 4
                rightX = head_pos[0] + deltaZ // 4
                rect = scene.addRect(QtCore.QRectF(leftX, head_pos[1], rightX - leftX, leg_pos[1] - head_pos[1]), QtGui.QPen(color, 1), QtCore.Qt.NoBrush)

                if settings['hp_bar_rendering'] == 1:
                    max_hp = 100
                    hp_percentage = min(1.0, max(0.0, entity_hp / max_hp))
                    hp_bar_width = 2
                    hp_bar_height = deltaZ
                    hp_bar_x_left = leftX - hp_bar_width - 2
                    hp_bar_y_top = head_pos[1]
                    hp_bar = scene.addRect(QtCore.QRectF(hp_bar_x_left, hp_bar_y_top, hp_bar_width, hp_bar_height), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(0, 0, 0))
                    current_hp_height = hp_bar_height * hp_percentage
                    hp_bar_y_bottom = hp_bar_y_top + hp_bar_height - current_hp_height
                    hp_bar_current = scene.addRect(QtCore.QRectF(hp_bar_x_left, hp_bar_y_bottom, hp_bar_width, current_hp_height), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(255, 0, 0))
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


                if settings['head_hitbox_rendering'] == 1:
                    head_hitbox_size = (rightX - leftX) / 5
                    head_hitbox_radius = head_hitbox_size * 2 ** 0.5 / 2
                    head_hitbox_x = leftX + 2.5 * head_hitbox_size
                    head_hitbox_y = head_pos[1] + deltaZ / 9
                    ellipse = scene.addEllipse(QtCore.QRectF(head_hitbox_x - head_hitbox_radius, head_hitbox_y - head_hitbox_radius, head_hitbox_radius * 2, head_hitbox_radius * 2), QtGui.QPen(QtCore.Qt.NoPen), QtGui.QColor(255, 0, 0, 128))

                if settings.get('bons', 0) == 1:
                    draw_bons(scene, pm, bone_matrix, view_matrix, window_width, window_height)

                if settings.get('nickname', 0) == 1:
                    player_name = pm.read_string(entity_controller + m_iszPlayerName, 32)
                    font_size = max(6, min(18, deltaZ / 25))
                    font = QtGui.QFont('DejaVu Sans', font_size, QtGui.QFont.Bold)
                    name_text = scene.addText(player_name, font)
                    text_rect = name_text.boundingRect()
                    name_x = head_pos[0] - text_rect.width() / 2
                    name_y = head_pos[1] - text_rect.height()
                    name_text.setPos(name_x, name_y)
                    name_text.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                
                if settings.get('weapon', 0) == 1:
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

def draw_bons(scene, pm, bone_matrix, view_matrix, width, height):
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
        print(f"Error drawing bons: {e}")

def esp_main():
    settings = load_settings()
    app = QtWidgets.QApplication(sys.argv)
    window = ESPWindow(settings)
    window.show()
    sys.exit(app.exec())

# Trigger Bot
def triggerbot():
    offsets = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/offsets.json').json()
    client_dll = requests.get('https://raw.githubusercontent.com/popsiclez/offsets/refs/heads/main/output/client_dll.json').json()
    dwEntityList = offsets['client.dll']['dwEntityList']
    dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']
    m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
    m_iIDEntIndex = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_iIDEntIndex']
    m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
    mouse = Controller()
    default_settings = {
        "TriggerKey": "X",
        "trigger_bot_active": 1,
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
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        while True:
            try:
                trigger_bot_active = settings["trigger_bot_active"]
                attack_all = settings["esp_mode"]
                keyboards = settings["TriggerKey"]
                if win32api.GetAsyncKeyState(key_str_to_vk(keyboards)):
                    if trigger_bot_active == 1:
                        try:
                            player = pm.read_longlong(client + dwLocalPlayerPawn)
                            entityId = pm.read_int(player + m_iIDEntIndex)
                            if entityId > 0:
                                entList = pm.read_longlong(client + dwEntityList)
                                entEntry = pm.read_longlong(entList + 0x8 * (entityId >> 9) + 0x10)
                                entity = pm.read_longlong(entEntry + 120 * (entityId & 0x1FF))
                                entityTeam = pm.read_int(entity + m_iTeamNum)
                                playerTeam = pm.read_int(player + m_iTeamNum)
                                if (attack_all == 1) or (entityTeam != playerTeam and attack_all == 0):
                                    entityHp = pm.read_int(entity + m_iHealth)
                                    if entityHp > 0:
                                        mouse.press(Button.left)
                                        time.sleep(0.03)
                                        mouse.release(Button.left)
                        except Exception:
                            pass
                    time.sleep(0.03)
                else:
                    time.sleep(0.1)
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

# Aim Bot
def aim():
    default_settings = {
         'esp_rendering': 1,
         'esp_mode': 1,
         'AimKey': "C",
         'aim_active': 1,
         'aim_mode': 1,
         'radius': 20,
         'aim_mode_distance': 1,
         'aim_smoothness': 50
     }
    # store chosen bone per-entity so "Random" picks persist while entity is tracked
    chosen_bones = {}

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
        # occlusion/visibility check removed
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
                game_scene = pm.read_longlong(entity_pawn_addr + m_pGameSceneNode)
                bone_matrix = pm.read_longlong(game_scene + m_modelState + 0x80)
                try:
                    # aim_mode: 0 = Body, 1 = Head, 2 = Random (choose head/body per entity)
                    if settings.get('aim_mode', 0) == 2:
                        # persist choice per entity to avoid flipping every frame
                        key = entity_pawn_addr
                        if key not in chosen_bones:
                            chosen_bones[key] = random.choice([4, 6])
                        bone_id = chosen_bones[key]
                    else:
                        bone_id = 6 if settings['aim_mode'] == 1 else 4

                    headX = pm.read_float(bone_matrix + bone_id * 0x20)
                    headY = pm.read_float(bone_matrix + bone_id * 0x20 + 0x4)
                    headZ = pm.read_float(bone_matrix + bone_id * 0x20 + 0x8)
                    head_pos = w2s(view_matrix, headX, headY, headZ, width, height)
                    legZ = pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
                    leg_pos = w2s(view_matrix, headX, headY, legZ, width, height)
                    deltaZ = abs(head_pos[1] - leg_pos[1])
                    if head_pos[0] != -999 and head_pos[1] != -999:
                        if settings['aim_mode_distance'] == 1:
                            target_list.append({
                                'pos': head_pos,
                                'deltaZ': deltaZ
                            })
                        else:
                            target_list.append({
                                'pos': head_pos,
                                'deltaZ': None
                            })
                except Exception as e:
                    pass
            except:
                return
        return target_list

    def aimbot(target_list, radius, aim_mode_distance, smoothness):
        if not target_list:
            return
        center_x = win32api.GetSystemMetrics(0) // 2
        center_y = win32api.GetSystemMetrics(1) // 2
        if radius == 0:
            closest_target = None
            closest_dist = float('inf')
            for target in target_list:
                dist = ((target['pos'][0] - center_x) ** 2 + (target['pos'][1] - center_y) ** 2) ** 0.5
                if dist < closest_dist:
                    closest_target = target['pos']
                    closest_dist = dist
        else:
            screen_radius = radius / 100.0 * min(center_x, center_y)
            closest_target = None
            closest_dist = float('inf')
            if aim_mode_distance == 1:
                target_with_max_deltaZ = None
                max_deltaZ = -float('inf')
                for target in target_list:
                    dist = ((target['pos'][0] - center_x) ** 2 + (target['pos'][1] - center_y) ** 2) ** 0.5
                    if dist < screen_radius and target['deltaZ'] > max_deltaZ:
                        max_deltaZ = target['deltaZ']
                        target_with_max_deltaZ = target
                closest_target = target_with_max_deltaZ['pos'] if target_with_max_deltaZ else None
            else:
                for target in target_list:
                    dist = ((target['pos'][0] - center_x) ** 2 + (target['pos'][1] - center_y) ** 2) ** 0.5
                    if dist < screen_radius and dist < closest_dist:
                        closest_target = target['pos']
                        closest_dist = dist
        if closest_target:
            target_x, target_y = closest_target
            dx = target_x - center_x
            dy = target_y - center_y
            # smoothness: 0 => instant (move full delta)
            # 1..100 => interpolate: alpha linearly maps from ~1.0 down to 0.02
            if smoothness is None:
                smoothness = 0
            s = int(smoothness)
            if s <= 0:
                move_x = int(dx)
                move_y = int(dy)
            else:
                # map s in [1,100] to alpha in [~0.99..0.02] -> higher s = smaller steps
                alpha = max(0.02, 1.0 - (s / 100.0) * (1.0 - 0.02))
                move_x = int(dx * alpha)
                move_y = int(dy * alpha)
                # ensure movement if target not already centered
                if move_x == 0 and dx != 0:
                    move_x = 1 if dx > 0 else -1
                if move_y == 0 and dy != 0:
                    move_y = 1 if dy > 0 else -1
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, move_x, move_y, 0, 0)

    def main(settings):
        offsets, client_dll = get_offsets_and_client_dll()
        window_size = get_window_size()
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        while True:
            target_list = []
            target_list = esp(pm, client, offsets, client_dll, settings, target_list, window_size)
            if win32api.GetAsyncKeyState(key_str_to_vk(settings.get('AimKey', ''))):
                aimbot(target_list, settings['radius'], settings['aim_mode_distance'], settings.get('aim_smoothness', 0))
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

if __name__ == "__main__":

    # wait for the game to start
    ctypes.windll.user32.MessageBoxW(0, "Waiting For CS2.exe", "", 0)
    while True:
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
    ]
    for p in procs:
        p.start()

    try:
        # monitor: if the game process disappears or a terminate signal file is created,
        # stop child processes and exit
        while True:
            time.sleep(1)
            # stop if external terminate signal was created
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                break
            try:
                _ = pymem.Pymem("cs2.exe")
            except Exception:
                break
    finally:
        for p in procs:
            try:
                if p.is_alive():
                    p.terminate()
                    p.join(1)
            except Exception:
                pass
        # cleanup signal file if present
        try:
            if os.path.exists(TERMINATE_SIGNAL_FILE):
                os.remove(TERMINATE_SIGNAL_FILE)
        except Exception:
            pass
        sys.exit(0)
    

