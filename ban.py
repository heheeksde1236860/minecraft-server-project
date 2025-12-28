from PySide6 import QtWidgets, QtCore, QtGui

class BanTab(QtWidgets.QWidget):
    def __init__(self, server_manager):
        super().__init__()
        self.server_manager = server_manager
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QtWidgets.QLabel("Ban User")
        title.setObjectName("H2")
        layout.addWidget(title)

        form_layout = QtWidgets.QFormLayout()
        
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Minecraft Username")
        
        self.reason_input = QtWidgets.QLineEdit()
        self.reason_input.setPlaceholderText("Ban Reason")
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Reason:", self.reason_input)
        
        layout.addLayout(form_layout)

        self.ban_btn = QtWidgets.QPushButton("BAN USER")
        self.ban_btn.setObjectName("Primary")
        self.ban_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.ban_btn.clicked.connect(self.execute_ban)
        
        layout.addWidget(self.ban_btn)
        layout.addStretch(1)

    def execute_ban(self):
        username = self.username_input.text().strip()
        reason = self.reason_input.text().strip()

        if not username:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter a username.")
            return

        if not reason:
            reason = "Banned by operator."

        cmd = f"ban {username} {reason}"
        self.server_manager.send_command(cmd, hide_log=True)
        
        QtWidgets.QMessageBox.information(self, "Success", f"Ban command sent for {username}.")
        self.username_input.clear()
        self.reason_input.clear()

