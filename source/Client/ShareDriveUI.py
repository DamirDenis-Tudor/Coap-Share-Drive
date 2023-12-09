from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QTreeView,
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QWidget,
    QDialog,
    QLabel,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
)


class ServerLoginDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.server_address_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        form_layout.addRow("Server Address:", self.server_address_input)
        form_layout.addRow("Password:", self.password_input)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self.accept)

        layout.addLayout(form_layout)
        layout.addWidget(login_button)

        self.setLayout(layout)
        self.setWindowTitle("Server Login")
        self.setFixedSize(QSize(400, 300))  # Set the fixed size of the login window


class ShareDriveClientApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.login_dialog = ServerLoginDialog()
        self.login_dialog.accepted.connect(self.show_file_system_page)

    def show_file_system_page(self):
        # Configuration of the main window
        self.setWindowTitle("Share Drive Client")
        self.setGeometry(100, 100, 1200, 600)

        # Configuration of the tree views
        self.server_tree_view = QTreeView()
        self.server_tree_view.setHeaderHidden(True)

        self.local_tree_view = QTreeView()
        self.local_tree_view.setHeaderHidden(True)

        # Configuration of buttons
        self.connect_button = QPushButton("Connect to Server")

        # Connection of signals to functions
        self.connect_button.clicked.connect(self.show_login_page)

        # Configuration of the layouts
        layout = QVBoxLayout()

        server_layout = QVBoxLayout()
        server_layout.addWidget(self.server_tree_view)
        server_layout.addWidget(self.connect_button)

        local_layout = QVBoxLayout()
        local_layout.addWidget(self.local_tree_view)

        layout.addLayout(server_layout)
        layout.addLayout(local_layout)

        # Configuration of the central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set the root items for the item models
        self.server_root_item = QStandardItem("Server Root")
        self.server_item_model = QStandardItemModel()
        self.server_item_model.appendRow(self.server_root_item)
        self.server_tree_view.setModel(self.server_item_model)

        self.local_root_item = QStandardItem("Local Root")
        self.local_item_model = QStandardItemModel()
        self.local_item_model.appendRow(self.local_root_item)
        self.local_tree_view.setModel(self.local_item_model)

        # Show the main window
        self.show()


def main():
    app = QApplication([])

    # Display the login dialog first
    login_dialog = ServerLoginDialog()
    result = login_dialog.exec_()

    # If login is successful, show the file system page
    if result == QDialog.Accepted:
        window = ShareDriveClientApp()
        app.exec()


if __name__ == "__main__":
    main()
