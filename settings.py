from PySide6 import QtCore, QtWidgets, QtGui
import os
import json
import threading
from utils import UUIDFetcher


class NoWheelSpinBox(QtWidgets.QSpinBox):
    def wheelEvent(self, event):
        # Prevent accidental value changes when scrolling the page
        event.ignore()


class NoWheelComboBox(QtWidgets.QComboBox):
    def wheelEvent(self, event):
        # Prevent accidental value changes when scrolling the page
        event.ignore()

class SettingsTab(QtWidgets.QWidget):
    def __init__(self, server_props_path="server.properties"):
        super().__init__()
        self.server_props_path = server_props_path
        self.whitelist_path = "whitelist.json"
        self.props = {}
        self.whitelist_data = []
        self.load_properties()
        self.load_whitelist()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        container = QtWidgets.QWidget()
        self.form_layout = QtWidgets.QVBoxLayout(container)
        self.form_layout.setSpacing(15)
        
        lbl_title = QtWidgets.QLabel("Server Settings")
        lbl_title.setObjectName("H1")
        self.form_layout.addWidget(lbl_title)
        
        self.seed_input = self.add_text_input("Level Seed", "level-seed")
        
        self.slots_input = self.add_spin_input("Max Players (Slots)", "max-players", 1, 10000)
        
        self.gamemode_input = self.add_combo_input("Gamemode", "gamemode", ["survival", "creative", "adventure", "spectator"])

        self.difficulty_input = self.add_combo_input("Difficulty", "difficulty", ["peaceful", "easy", "normal", "hard"])
        
        self.whitelist_input = self.add_bool_input("Whitelist", "white-list")
        
        self.cracked_input = self.add_custom_bool_input("Cracked Mode", self.get_cracked_state, self.set_cracked_state)

        self.fly_input = self.add_bool_input("Allow Flight", "allow-flight")
        
        self.force_gamemode_input = self.add_bool_input("Force Gamemode", "force-gamemode")
        
        self.spawn_protection_input = self.add_spin_input("Spawn Protection", "spawn-protection", 0, 10000)
        
        self.idle_timeout_input = self.add_spin_input("Idle Timeout (minutes)", "player-idle-timeout", 0, 10000)

        self.view_distance_input = self.add_spin_input("View Distance", "view-distance", 2, 32)
        
        self.motd_input = self.add_text_input("MOTD (Server Bio)", "motd")
        
        # No proxy/velocity controls
        
        # --- Whitelist Management ---
        self.form_layout.addSpacing(20)
        lbl_wl = QtWidgets.QLabel("Whitelist Management")
        lbl_wl.setObjectName("H2")
        self.form_layout.addWidget(lbl_wl)

        wl_input_layout = QtWidgets.QVBoxLayout()
        self.wl_username_input = QtWidgets.QLineEdit()
        self.wl_username_input.setPlaceholderText("Enter Minecraft Username")
        
        self.btn_add_wl = QtWidgets.QPushButton("Add User")
        self.btn_add_wl.setObjectName("Primary")
        self.btn_add_wl.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_add_wl.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(140, 96, 255, 210), stop:1 rgba(186, 138, 255, 210));
                border: 1px solid rgba(255,255,255,55);
                color: #0B0B12;
                font-weight: 700;
                padding: 15px 20px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,26);
                border-color: rgba(186, 138, 255, 140);
            }
            QPushButton:pressed {
                background: rgba(186, 138, 255, 40);
            }
        """)
        self.btn_add_wl.clicked.connect(self.add_whitelist_user)
        
        wl_input_layout.addWidget(self.wl_username_input)
        wl_input_layout.addWidget(self.btn_add_wl)
        self.form_layout.addLayout(wl_input_layout)
        
        self.wl_list_widget = QtWidgets.QListWidget()
        self.wl_list_widget.setStyleSheet("""
            QListWidget {
                background: rgba(0,0,0,35);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 8px;
                color: #E9E7FF;
            }
        """)
        self.wl_list_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.wl_list_widget.customContextMenuRequested.connect(self.show_wl_context_menu)
        self.update_whitelist_display()
        self.form_layout.addWidget(self.wl_list_widget)

        self.form_layout.addSpacing(20)
        self.btn_save = QtWidgets.QPushButton("Save Settings")
        self.btn_save.setObjectName("Primary")
        self.btn_save.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(140, 96, 255, 210), stop:1 rgba(186, 138, 255, 210));
                border: 1px solid rgba(255,255,255,55);
                color: #0B0B12;
                font-weight: 700;
                padding: 15px 20px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,26);
                border-color: rgba(186, 138, 255, 140);
            }
            QPushButton:pressed {
                background: rgba(186, 138, 255, 40);
            }
        """)
        self.btn_save.clicked.connect(self.save_properties)
        self.form_layout.addWidget(self.btn_save)

        self.form_layout.addStretch(1)
        
        scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def load_whitelist(self):
        if os.path.exists(self.whitelist_path):
            try:
                with open(self.whitelist_path, 'r') as f:
                    self.whitelist_data = json.load(f)
            except:
                self.whitelist_data = []
        else:
             self.whitelist_data = []

    def save_whitelist(self):
        try:
            with open(self.whitelist_path, 'w') as f:
                json.dump(self.whitelist_data, f, indent=2)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save whitelist: {e}")

    def update_whitelist_display(self):
        self.wl_list_widget.clear()
        for user in self.whitelist_data:
            item = QtWidgets.QListWidgetItem(f"{user['name']} ({user['uuid']})")
            self.wl_list_widget.addItem(item)

    def add_whitelist_user(self):
        username = self.wl_username_input.text().strip()
        if not username:
            return
        
        self.btn_add_wl.setEnabled(False)
        self.btn_add_wl.setText("Fetching...")
        
        # Run fetch in thread
        self.fetcher = UUIDFetcher(username, proxy=getattr(self, "selected_proxy", None))
        self.thread = QtCore.QThread()
        self.fetcher.moveToThread(self.thread)
        self.thread.started.connect(self.fetcher.run)
        self.fetcher.finished.connect(self.on_uuid_fetched)
        self.fetcher.finished.connect(self.thread.quit)
        self.fetcher.finished.connect(self.fetcher.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_uuid_fetched(self, username, uuid, error):
        self.btn_add_wl.setEnabled(True)
        self.btn_add_wl.setText("Add User")
        
        if error:
            QtWidgets.QMessageBox.warning(self, "Error", f"Could not find player: {error}")
            return
            
        # Check if already exists
        for user in self.whitelist_data:
            if user['uuid'] == uuid:
                QtWidgets.QMessageBox.information(self, "Info", "User already whitelisted.")
                return

        self.whitelist_data.append({"uuid": uuid, "name": username})
        self.save_whitelist()
        self.update_whitelist_display()
        self.wl_username_input.clear()

    def show_wl_context_menu(self, pos):
        item = self.wl_list_widget.itemAt(pos)
        if not item:
            return
            
        menu = QtWidgets.QMenu()
        remove_action = menu.addAction("Remove from Whitelist")
        action = menu.exec(self.wl_list_widget.mapToGlobal(pos))
        
        if action == remove_action:
            row = self.wl_list_widget.row(item)
            del self.whitelist_data[row]
            self.save_whitelist()
            self.update_whitelist_display()

    def load_properties(self):
        if not os.path.exists(self.server_props_path):
            return
        
        with open(self.server_props_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    self.props[key.strip()] = value.strip()

    def get_prop(self, key, default=""):
        return self.props.get(key, default)

    def add_text_input(self, label_text, key):
        lbl = QtWidgets.QLabel(label_text)
        lbl.setObjectName("H2")
        self.form_layout.addWidget(lbl)
        
        inp = QtWidgets.QLineEdit()
        inp.setText(self.get_prop(key))
        self.form_layout.addWidget(inp)
        return inp

    def add_spin_input(self, label_text, key, min_val, max_val):
        lbl = QtWidgets.QLabel(label_text)
        lbl.setObjectName("H2")
        self.form_layout.addWidget(lbl)
        
        inp = NoWheelSpinBox()
        inp.setRange(min_val, max_val)
        val = self.get_prop(key)
        try:
            inp.setValue(int(val))
        except:
            inp.setValue(min_val)
        
        inp.setStyleSheet("""
            QSpinBox {
                background: rgba(0,0,0,35);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
        """)
        self.form_layout.addWidget(inp)
        return inp

    def add_combo_input(self, label_text, key, options):
        lbl = QtWidgets.QLabel(label_text)
        lbl.setObjectName("H2")
        self.form_layout.addWidget(lbl)
        
        inp = NoWheelComboBox()
        inp.addItems(options)
        
        current = self.get_prop(key)
        idx = inp.findText(current)
        if idx >= 0:
            inp.setCurrentIndex(idx)
            
        inp.setStyleSheet("""
            QComboBox {
                background: rgba(0,0,0,35);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 8px;
                padding: 8px;
                color: white;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #0E0C1A;
                color: white;
                selection-background-color: rgba(186, 138, 255, 100);
            }
        """)
        self.form_layout.addWidget(inp)
        return inp

    def add_bool_input(self, label_text, key):
        inp = QtWidgets.QCheckBox(label_text)
        inp.setStyleSheet("QCheckBox { color: #E9E7FF; font-size: 14px; }")
        
        val = self.get_prop(key).lower()
        inp.setChecked(val == 'true')
        
        self.form_layout.addWidget(inp)
        return inp

    def add_custom_bool_input(self, label_text, getter, setter):
        inp = QtWidgets.QCheckBox(label_text)
        inp.setStyleSheet("QCheckBox { color: #E9E7FF; font-size: 14px; }")
        inp.setChecked(getter())
        self.form_layout.addWidget(inp)
        inp.setProperty("custom_setter", setter)
        return inp

    def get_cracked_state(self):
        val = self.get_prop("online-mode", "true").lower()
        return val == 'false'

    def set_cracked_state(self, is_checked):
        self.props["online-mode"] = "false" if is_checked else "true"

    def save_properties(self):
        self.props["level-seed"] = self.seed_input.text()
        self.props["max-players"] = str(self.slots_input.value())
        self.props["gamemode"] = self.gamemode_input.currentText()
        self.props["difficulty"] = self.difficulty_input.currentText()
        self.props["white-list"] = "true" if self.whitelist_input.isChecked() else "false"
        self.props["allow-flight"] = "true" if self.fly_input.isChecked() else "false"
        self.props["force-gamemode"] = "true" if self.force_gamemode_input.isChecked() else "false"
        self.props["spawn-protection"] = str(self.spawn_protection_input.value())
        self.props["player-idle-timeout"] = str(self.idle_timeout_input.value())
        self.props["view-distance"] = str(self.view_distance_input.value())
        self.props["motd"] = self.motd_input.text()
        
        if hasattr(self.cracked_input, "property"):
             setter = self.cracked_input.property("custom_setter")
             if setter:
                 setter(self.cracked_input.isChecked())

        try:
            lines = []
            if os.path.exists(self.server_props_path):
                with open(self.server_props_path, 'r') as f:
                    lines = f.readlines()
            
            key_line_map = {}
            for i, line in enumerate(lines):
                if '=' in line and not line.strip().startswith('#'):
                    k = line.split('=', 1)[0].strip()
                    key_line_map[k] = i
            
            for k, v in self.props.items():
                if k in key_line_map:
                    lines[key_line_map[k]] = f"{k}={v}\n"
                else:
                    lines.append(f"{k}={v}\n")
            
            with open(self.server_props_path, 'w') as f:
                f.writelines(lines)
                
            QtWidgets.QMessageBox.information(self, "Success", "Settings saved successfully!")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def apply_proxy_settings(self):
        # Deprecated: proxy is not used for hosting. Kept for compatibility/no-op.
        self.selected_proxy_ip = None
        self.selected_proxy_port = None
