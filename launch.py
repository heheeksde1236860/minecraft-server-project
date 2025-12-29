import sys
import subprocess
import threading
from PySide6 import QtCore, QtWidgets, QtGui

class ServerManager(QtCore.QObject):
    console_output = QtCore.Signal(str)
    server_started = QtCore.Signal()
    server_stopped = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.process = None
        self.running = False
        self.stop_event = threading.Event()

    def start_server(self, jar_path="server.jar", ram="2G"):
        if self.running:
            return

        cmd = ["java", f"-Xmx{ram}", f"-Xms{ram}", "-jar", jar_path, "nogui"]
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            self.running = True
            self.server_started.emit()
            
            self.stop_event.clear()
            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()
            
        except Exception as e:
            self.console_output.emit(f"Failed to start server: {e}")

    def stop_server(self):
        if not self.running or not self.process:
            return

        self.send_command("stop")
        threading.Timer(10.0, self._force_kill).start()

    def _force_kill(self):
        if self.running and self.process:
            try:
                self.process.kill()
            except:
                pass

    def send_command(self, command, hide_log=False):
        if self.running and self.process:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                if not hide_log:
                     pass 
            except Exception as e:
                self.console_output.emit(f"Error sending command: {e}")

    def _read_output(self):
        while self.running and self.process:
            line = self.process.stdout.readline()
            if not line:
                break
            
            if "/ban" in line and "issued server command" in line:
                continue

            self.console_output.emit(line.strip())

        self.running = False
        self.process = None
        self.server_stopped.emit()

class LaunchTab(QtWidgets.QWidget):
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.hero = QtWidgets.QFrame()
        self.hero.setObjectName("Card")
        
        hero_layout = QtWidgets.QHBoxLayout(self.hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        
        hero_text_layout = QtWidgets.QVBoxLayout()
        h1 = QtWidgets.QLabel("Manage Your Server")
        h1.setObjectName("H1")
        sub = QtWidgets.QLabel("Monitor performance, view logs, and control your Minecraft server instance directly from this panel.")
        sub.setObjectName("Muted")
        sub.setWordWrap(True)
        
        hero_text_layout.addWidget(h1)
        hero_text_layout.addWidget(sub)
        
        hero_layout.addLayout(hero_text_layout)
        
        layout.addWidget(self.hero)
        self.console = QtWidgets.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #0E0C1A;
                color: #E9E7FF;
                border: 1px solid rgba(255,255,255,30);
                border-radius: 8px;
                font-family: Consolas, Monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.console)

        self.console_input = QtWidgets.QLineEdit()
        self.console_input.setPlaceholderText("Type a command...")
        self.console_input.setStyleSheet("""
            QLineEdit {
                background: rgba(0,0,0,35);
                border: 1px solid rgba(255,255,255,30);
                border-radius: 8px;
                padding: 10px 12px;
                color: #E9E7FF;
            }
            QLineEdit:focus {
                border-color: rgba(186, 138, 255, 170);
            }
        """)
        layout.addWidget(self.console_input)

        controls = QtWidgets.QHBoxLayout()
        
        self.start_btn = QtWidgets.QPushButton("Start Server")
        self.start_btn.setObjectName("Primary")
        self.start_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        
        self.stop_btn = QtWidgets.QPushButton("Stop Server")
        self.stop_btn.setObjectName("Primary")
        self.stop_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.stop_btn.setEnabled(False)

        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)
        layout.addLayout(controls)

    def connect_signals(self):
        self.start_btn.clicked.connect(lambda: self.server_manager.start_server())
        self.stop_btn.clicked.connect(lambda: self.server_manager.stop_server())
        self.server_manager.console_output.connect(self.append_log)
        self.server_manager.server_started.connect(self.on_start)
        self.server_manager.server_stopped.connect(self.on_stop)
        
        self.console_input.returnPressed.connect(self.send_console_command)

    def send_console_command(self):
        text = self.console_input.text().strip()
        if text:
            self.server_manager.send_command(text)
            self.console_input.clear()

    def append_log(self, text):
        self.console.append(text)
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_start(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.console.append("--- Server Started ---")

    def on_stop(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.console.append("--- Server Stopped ---")
