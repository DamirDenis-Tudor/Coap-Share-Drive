import sys
from PyQt5.QtCore import QModelIndex, Qt, QAbstractItemModel
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTreeView, QPushButton, QInputDialog,
    QMessageBox, QFileDialog, QDialog, QLabel, QLineEdit
)


class FileItem:
    def __init__(self, name, is_folder=False, parent=None):
        self.name = name
        self.is_folder = is_folder
        self.children = []
        self.parent = parent

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class RemoteFileSystemModel(QAbstractItemModel):
    def __init__(self, root_items):
        super().__init__()
        self.root_items = root_items

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self.root_items)
        parent_item = parent.internalPointer()
        return len(parent_item.children) if parent_item else 0

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.name
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            parent_item = self.root_items[row]
        else:
            parent_item = parent.internalPointer().children[row]

        if parent_item:
            return self.createIndex(row, column, parent_item)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent
        if parent_item:
            return self.createIndex(parent_item.row(), 0, parent_item)
        else:
            return QModelIndex()


class UploadDialog(QDialog):
    def __init__(self, parent=None):
        super(UploadDialog, self).__init__(parent)

        self.setWindowTitle("Upload Files")
        self.setGeometry(200, 200, 400, 200)

        self.file_list = QFileDialog.getOpenFileNames(self, 'Select Files to Upload')[0]
        self.upload_button = QPushButton("Upload", self)
        self.upload_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.upload_button)


class RenameMoveDialog(QDialog):
    def __init__(self, title, prompt, parent=None):
        super(RenameMoveDialog, self).__init__(parent)

        self.setWindowTitle(title)
        self.setGeometry(200, 200, 400, 150)

        self.prompt_label = QLabel(prompt, self)
        self.name_input = QLineEdit(self)
        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.prompt_label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.ok_button)


class FileManagerApp(QWidget):
    def __init__(self, root_items):
        super().__init__()

        self.file_tree_view = None
        self.remote_file_system_model = RemoteFileSystemModel(root_items)

        self.setWindowTitle('Remote File Manager')
        self.setGeometry(100, 100, 800, 600)

        self.file_tree_view = QTreeView()
        self.file_tree_view.setModel(self.remote_file_system_model)

        self.download_button = QPushButton('Download')
        self.upload_button = QPushButton('Upload')
        self.rename_button = QPushButton('Rename')
        self.move_button = QPushButton('Move')
        self.delete_button = QPushButton('Delete')

        self.download_button.clicked.connect(self.download_handler)
        self.upload_button.clicked.connect(self.show_upload_dialog)
        self.rename_button.clicked.connect(self.show_rename_dialog)
        self.move_button.clicked.connect(self.show_move_dialog)
        self.delete_button.clicked.connect(self.delete_handler)

        layout = QVBoxLayout()
        layout.addWidget(self.file_tree_view)
        layout.addWidget(self.download_button)
        layout.addWidget(self.upload_button)
        layout.addWidget(self.rename_button)
        layout.addWidget(self.move_button)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def download_handler(self):
        selected_index = self.file_tree_view.currentIndex()
        file_item = selected_index.internalPointer()
        if file_item.is_folder:
            return  # You may want to handle folder selection differently
        # Perform download logic using file_item
        print(f'Download: {file_item.name}')

    def show_upload_dialog(self):
        upload_dialog = UploadDialog(self)
        if upload_dialog.exec_():
            # Perform upload logic using upload_dialog.file_list
            print("Upload: Selected Files:", upload_dialog.file_list)

    def show_rename_dialog(self):
        selected_index = self.file_tree_view.currentIndex()
        file_item = selected_index.internalPointer()

        rename_dialog = RenameMoveDialog("Rename", "Enter new name:", self)
        rename_dialog.name_input.setText(file_item.name)

        if rename_dialog.exec_():
            new_name = rename_dialog.name_input.text()
            # Update the file_item name with the new name
            file_item.name = new_name
            print(f'Rename: {file_item.name}')

    def show_move_dialog(self):
        selected_index = self.file_tree_view.currentIndex()
        file_item = selected_index.internalPointer()

        move_dialog = RenameMoveDialog("Move", "Enter new parent folder:", self)
        move_dialog.name_input.setText(file_item.parent.name if file_item.parent else "")

        if move_dialog.exec_():
            new_parent = move_dialog.name_input.text()
            # Perform move logic using file_item and new_parent
            print(f'Move: {file_item.name} -> {new_parent}')

    def delete_handler(self):
        selected_index = self.file_tree_view.currentIndex()
        file_item = selected_index.internalPointer()
        reply = QMessageBox.question(self, 'Delete', f'Are you sure you want to delete {file_item.name}?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Perform delete logic using file_item
            print(f'Delete: {file_item.name}')


if __name__ == '__main__':
    root_items = [
        FileItem("Folder1", is_folder=True),
        FileItem("File1.txt"),
        FileItem("Folder2", is_folder=True),
        FileItem("File2.txt")
    ]

    # Add child relationships
    root_items[0].add_child(FileItem("Subfolder1", is_folder=True))
    root_items[0].add_child(FileItem("File3.txt"))

    app = QApplication(sys.argv)
    window = FileManagerApp(root_items)
    window.show()
    sys.exit(app.exec_())
