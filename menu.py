import sys
import os
import shutil
from PySide6 import QtCore, QtGui, QtWidgets
from launch import LaunchTab, ServerManager
from ban import BanTab
from plugin_handler import PluginsTab

IS_FROZEN = getattr(sys, "frozen", False)
BASE_DIR = sys._MEIPASS if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))

# ======================================================
# the actual design
# ======================================================
QSS = """
* {
    font-family: Inter, Segoe UI, Arial;
    font-size: 12px;
    color: #E9E7FF;
}
QWidget {
    background: #0B0B12;
}
QWidget#Root {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0B0B12, stop:0.55 #0E0C1A, stop:1 #0A0A10);
}
QDialog {
    background: #0E0C1A;
    border: 1px solid rgba(255,255,255,30);
    border-radius: 12px;
}
QMessageBox {
    background: #0E0C1A;
}
QMessageBox QLabel {
    color: #E9E7FF;
}
QMessageBox QPushButton {
    min-width: 80px;
    min-height: 28px;
}
QFrame#TopBar {
    background: rgba(20, 16, 40, 160);
    border: 1px solid rgba(255,255,255,35);
    border-radius: 16px;
}
QFrame#SideBar {
    background: rgba(20, 16, 40, 140);
    border: 1px solid rgba(255,255,255,30);
    border-radius: 18px;
}
QFrame#Card {
    background: rgba(20, 16, 40, 155);
    border: 1px solid rgba(255,255,255,30);
    border-radius: 18px;
}
QLabel {
    background: transparent;
}
QLabel#H1 {
    font-size: 22px;
    font-weight: 700;
    background: transparent;
}
QLabel#H2 {
    font-size: 14px;
    font-weight: 600;
    color: rgba(233,231,255,210);
    background: transparent;
}
QLabel#Muted {
    color: rgba(233,231,255,160);
    background: transparent;
}
QPushButton {
    background: rgba(255,255,255,18);
    border: 1px solid rgba(255,255,255,35);
    border-radius: 12px;
    padding: 15px 20px; /* Bigger buttons */
    font-size: 14px; /* Larger font */
    min-height: 25px;
}
QPushButton:hover {
    background: rgba(255,255,255,26);
    border-color: rgba(186, 138, 255, 140);
}
QPushButton:pressed {
    background: rgba(186, 138, 255, 40);
}
QPushButton#Primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(140, 96, 255, 210), stop:1 rgba(186, 138, 255, 210));
    border: 1px solid rgba(255,255,255,55);
    color: #0B0B12;
    font-weight: 700;
}
QLineEdit {
    background: rgba(0,0,0,35);
    border: 1px solid rgba(255,255,255,30);
    border-radius: 12px;
    padding: 10px 12px;
    selection-background-color: rgba(186, 138, 255, 130);
}
QLineEdit:focus {
    border-color: rgba(186, 138, 255, 170);
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    width: 10px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,25);
    border-radius: 5px;
    min-height: 30px;
}
QStackedWidget {
    background: transparent;
}
"""

class Glow(QtWidgets.QGraphicsDropShadowEffect):
    def __init__(self, color="#B88AFF", blur=28, y=8, parent=None):
        super().__init__(parent)
        c = QtGui.QColor(color)
        c.setAlpha(140)
        self.setColor(c)
        self.setBlurRadius(blur)
        self.setOffset(0, y)

# ======================================================
# selector window 
# ======================================================
class VersionSelectorDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Install Minecraft Server")
        self.setFixedSize(400, 250)
        
        self.selected_version = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QtWidgets.QLabel("Select Server Version")
        title.setObjectName("H1")
        layout.addWidget(title)
        
        desc = QtWidgets.QLabel("No server installation found.\nPlease select a version to install.")
        desc.setObjectName("Muted")
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        btn_layout = QtWidgets.QVBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_v5 = QtWidgets.QPushButton("Minecraft 1.21.5")
        self.btn_v5.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_v5.clicked.connect(lambda: self.select_version("1.21.5"))
        
        self.btn_v10 = QtWidgets.QPushButton("Minecraft 1.21.10")
        self.btn_v10.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_v10.clicked.connect(lambda: self.select_version("1.21.10"))
        
        btn_layout.addWidget(self.btn_v5)
        btn_layout.addWidget(self.btn_v10)
        
        layout.addLayout(btn_layout)
        layout.addStretch(1)

    def select_version(self, version):
        self.selected_version = version
        self.accept()

# ======================================================
# main window
# ======================================================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft Server Panel")
        self.resize(1100, 680)

        # Server Manager Instance
        self.server_manager = ServerManager()

        root = QtWidgets.QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)

        grid = QtWidgets.QGridLayout(root)
        grid.setContentsMargins(18, 18, 18, 18)
        grid.setSpacing(14)

        sidebar = QtWidgets.QFrame()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(240)
        
        sb_layout = QtWidgets.QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 16, 16, 16)
        sb_layout.setSpacing(10)
        
        logo_path = os.path.join(BASE_DIR, "images", "programlogo.png")
        if os.path.exists(logo_path):
            logo_lbl = QtWidgets.QLabel()
            logo_lbl.setAlignment(QtCore.Qt.AlignCenter)
            pix = QtGui.QPixmap(logo_path)
            if not pix.isNull():
                pix = pix.scaled(72, 72, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                logo_lbl.setPixmap(pix)
            sb_layout.addWidget(logo_lbl)
        
        logo = QtWidgets.QLabel("SERVER PANEL")
        logo.setObjectName("H1")
        sb_layout.addWidget(logo)
        
        sb_layout.addSpacing(20)
        
        self.nav_buttons = {}
        for name in ["Launch", "Ban", "Plugins"]:
            btn = QtWidgets.QPushButton(name)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            sb_layout.addWidget(btn)
            self.nav_buttons[name] = btn
            
        sb_layout.addStretch(1)

        content_area = QtWidgets.QFrame()
        content_area.setObjectName("Card") 
        content_area.setGraphicsEffect(Glow(blur=30, y=10))
        
        content_layout = QtWidgets.QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QtWidgets.QStackedWidget()
        content_layout.addWidget(self.stack)

        self.tab_launch = LaunchTab(self.server_manager)
        self.tab_ban = BanTab(self.server_manager)
        self.tab_plugins = PluginsTab()

        self.stack.addWidget(self.tab_launch)
        self.stack.addWidget(self.tab_ban)
        self.stack.addWidget(self.tab_plugins)

        self.nav_buttons["Launch"].clicked.connect(lambda: self.switch_tab(0))
        self.nav_buttons["Ban"].clicked.connect(lambda: self.switch_tab(1))
        self.nav_buttons["Plugins"].clicked.connect(lambda: self.switch_tab(2))
        
        self.switch_tab(0)

        grid.addWidget(sidebar, 0, 0)
        grid.addWidget(content_area, 0, 1)

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)

    def closeEvent(self, event):
        if self.server_manager.running:
             reply = QtWidgets.QMessageBox.question(
                 self, 'Exit', 'Server is still running. Stop it?',
                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

             if reply == QtWidgets.QMessageBox.Yes:
                 self.server_manager.stop_server()
        
        event.accept()

# ======================================================
# entry point
# ======================================================
def check_installation():
    # Check if ./world/ exists (as a proxy for installed server)
    if os.path.exists("world") and os.path.isdir("world"):
        return True
    
    if os.path.exists("server.jar"):
        return True
        
    return False

def install_server(version):
    source_path = os.path.join(BASE_DIR, "server_options", version, "server.jar")
    dest_path = "server.jar"
    
    if not os.path.exists(source_path):
        QtWidgets.QMessageBox.critical(None, "Error", f"Could not find server jar at:\n{source_path}")
        return False
        
    try:
        shutil.copy2(source_path, dest_path)
        QtWidgets.QMessageBox.information(None, "Success", f"Installed Server {version} successfully.")
        return True
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Error", f"Failed to copy server jar:\n{e}")
        return False

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(QSS)
    
    if not check_installation():
        # Show selection dialog
        dlg = VersionSelectorDialog()
        if dlg.exec() == QtWidgets.QDialog.Accepted and dlg.selected_version:
            if not install_server(dlg.selected_version):
                return
        else:
            return

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
