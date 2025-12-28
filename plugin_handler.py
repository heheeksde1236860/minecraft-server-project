import os
import shutil
import json
import zipfile
from PySide6 import QtWidgets, QtCore, QtGui

class PluginDropArea(QtWidgets.QLabel):
    file_dropped = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText("Drag & Drop Plugins (.jar) Here")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed rgba(255, 255, 255, 50);
                border-radius: 12px;
                color: rgba(255, 255, 255, 150);
                font-size: 14px;
                padding: 30px;
                background: rgba(0, 0, 0, 20);
            }
            QLabel:hover {
                border-color: rgba(186, 138, 255, 150);
                background: rgba(186, 138, 255, 20);
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(".jar"):
                self.file_dropped.emit(f)

class PluginsTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.plugins_dir = "plugins"
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir)
        
        self.init_ui()
        self.load_plugins()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Drop Area
        self.drop_area = PluginDropArea()
        self.drop_area.file_dropped.connect(self.install_plugin)
        layout.addWidget(self.drop_area)

        # Plugin List
        self.plugin_list = QtWidgets.QListWidget()
        self.plugin_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                background: rgba(20, 16, 40, 155);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 5px;
                color: #E9E7FF;
            }
        """)
        layout.addWidget(self.plugin_list)

    def install_plugin(self, file_path):
        filename = os.path.basename(file_path)
        dest = os.path.join(self.plugins_dir, filename)
        
        try:
            shutil.copy2(file_path, dest)
            self.load_plugins() # Refresh
            QtWidgets.QMessageBox.information(self, "Success", f"Installed {filename}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to install plugin: {e}")

    def load_plugins(self):
        self.plugin_list.clear()
        if not os.path.exists(self.plugins_dir):
            return

        for filename in os.listdir(self.plugins_dir):
            if filename.lower().endswith(".jar"):
                path = os.path.join(self.plugins_dir, filename)
                info = self.get_plugin_info(path)
                
                item_text = f"{info['name']} v{info['version']}\n{info['description']}"
                item = QtWidgets.QListWidgetItem(item_text)
                self.plugin_list.addItem(item)

    def get_plugin_info(self, jar_path):
        default_info = {
            "name": os.path.basename(jar_path),
            "version": "Unknown",
            "description": "No fabric.mod.json found"
        }
        
        try:
            with zipfile.ZipFile(jar_path, 'r') as z:
                if "fabric.mod.json" in z.namelist():
                    with z.open("fabric.mod.json") as f:
                        data = json.load(f)
                        return {
                            "name": data.get("name", default_info["name"]),
                            "version": data.get("version", "Unknown"),
                            "description": data.get("description", "No description")
                        }
        except Exception:
            pass
            
        return default_info

