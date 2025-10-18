import sys
import os
import json
from pathlib import Path

# Import necessary PySide6 modules
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTreeView, QTextEdit, QDockWidget,
    QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QHBoxLayout, QWidget, QTabWidget, QMessageBox, QFileSystemModel, QToolBar
)
from PySide6.QtCore import Qt, QDir, QUrl, QProcess
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QIcon, QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

# --- Simple Syntax Highlighter ---
class SimpleSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self.highlighting_rules = []
        # Rule for HTML tags
        html_tag_format = QTextCharFormat(); html_tag_format.setForeground(QColor("#569CD6"))
        self.highlighting_rules.append((r'<[/?!]?\w+', html_tag_format)); self.highlighting_rules.append((r'>', html_tag_format))
        # Rule for attributes
        attribute_format = QTextCharFormat(); attribute_format.setForeground(QColor("#9CDCFE"))
        self.highlighting_rules.append((r'\b\w+(?=\=)', attribute_format))
        # Rule for attribute values (strings)
        string_format = QTextCharFormat(); string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((r'"[^"]*"', string_format)); self.highlighting_rules.append((r"'[^']*'", string_format))
        
    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in __import__('re').finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

# --- Project Creation Wizard ---
class ProjectWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Project")
        self.addPage(CreateProjectPage())

    def accept(self):
        project_name = self.field("projectName"); project_path = self.field("projectPath")
        full_path = Path(project_path) / project_name
        try:
            # Create directory structure
            os.makedirs(full_path / "src" / "js", exist_ok=True)
            os.makedirs(full_path / "src" / "css", exist_ok=True)
            os.makedirs(full_path / "assets" / "images", exist_ok=True)
            
            # Create default files
            (full_path / "src" / "index.html").write_text(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{project_name}</title>\n    <link rel=\"stylesheet\" href=\"css/style.css\">\n</head>\n<body>\n    <h1>Welcome to {project_name}</h1>\n    <script src=\"js/main.js\"></script>\n</body>\n</html>")
            (full_path / "src" / "css" / "style.css").write_text("body {\n    font-family: sans-serif;\n    background-color: #f0f0f0;\n    color: #111;\n}")
            (full_path / "src" / "js" / "main.js").write_text("console.log('Project loaded successfully!');")
            
            # Create project config file
            project_config = {"name": project_name, "version": "1.0.0"}
            with open(full_path / "project.bws", "w") as f: json.dump(project_config, f, indent=4)
            
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create project:\n{e}")
            super().reject()

class CreateProjectPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Set Project Details")
        layout = QVBoxLayout(self)
        self.name_label = QLabel("Project Name:"); self.name_edit = QLineEdit()
        layout.addWidget(self.name_label); layout.addWidget(self.name_edit)
        self.path_label = QLabel("Location:"); self.path_edit = QLineEdit(str(Path.home()))
        self.path_button = QPushButton("Browse..."); self.path_button.clicked.connect(self.select_path)
        path_layout = QHBoxLayout(); path_layout.addWidget(self.path_edit); path_layout.addWidget(self.path_button)
        layout.addLayout(path_layout); self.setLayout(layout)
        self.registerField("projectName*", self.name_edit); self.registerField("projectPath*", self.path_edit)

    def select_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Location", self.path_edit.text());
        if path: self.path_edit.setText(path)

# --- The Main Application Window ---
class BasicWebsiteStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Basic Website Studio")
        self.setGeometry(100, 100, 1600, 900)
        self.current_project_path = None
        self.build_process = None

        self._setup_menus()
        self._setup_toolbar()
        self._setup_ui_layout()
        
        self.update_action_states() # Initially disable actions

    def _setup_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        new_proj_action = file_menu.addAction("New Project..."); new_proj_action.triggered.connect(self.create_new_project)
        open_proj_action = file_menu.addAction("Open Project..."); open_proj_action.triggered.connect(self.open_project)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        style = self.style()
        self.play_action = QAction(style.standardIcon(style.StandardPixmap.SP_MediaPlay), "Play (Live Preview)", self)
        self.play_action.triggered.connect(self.play_project)
        toolbar.addAction(self.play_action)

        self.build_action = QAction(style.standardIcon(style.StandardPixmap.SP_DialogApplyButton), "Build Project", self)
        self.build_action.triggered.connect(self.build_project)
        toolbar.addAction(self.build_action)

    def _setup_ui_layout(self):
        self.editor_tabs = QTabWidget(); self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.editor_tabs)

        project_dock = QDockWidget("Project Explorer", self)
        self.project_view = QTreeView(); self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.rootPath()); self.fs_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)
        self.project_view.setModel(self.fs_model)
        for i in range(1, self.fs_model.columnCount()): self.project_view.hideColumn(i)
        self.project_view.doubleClicked.connect(self.open_file_from_tree)
        project_dock.setWidget(self.project_view)
        self.addDockWidget(Qt.LeftDockWidgetArea, project_dock)

        preview_dock = QDockWidget("Live Preview", self)
        self.preview = QWebEngineView()
        self.preview.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.preview.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        preview_dock.setWidget(self.preview)
        self.addDockWidget(Qt.RightDockWidgetArea, preview_dock)

        console_dock = QDockWidget("Output", self)
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setStyleSheet("font-family: Consolas, monospace;")
        console_dock.setWidget(self.output_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, console_dock)

    def create_new_project(self):
        wizard = ProjectWizard(self)
        if wizard.exec() == QWizard.Accepted:
            project_name = wizard.field("projectName"); project_path = wizard.field("projectPath")
            self.load_project(str(Path(project_path) / project_name))

    def open_project(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Open Project")
        if dir_name and (Path(dir_name) / "project.bws").exists():
            self.load_project(dir_name)
        elif dir_name:
            QMessageBox.warning(self, "Error", "This is not a valid project folder (project.bws is missing).")

    def load_project(self, path):
        self.current_project_path = path
        self.project_view.setRootIndex(self.fs_model.index(path))
        self.setWindowTitle(f"Basic Website Studio - {Path(path).name}")
        self.update_action_states() # Enable actions now that a project is loaded
        self.play_project()         # Show a preview immediately

    def open_file_from_tree(self, index):
        file_path = self.fs_model.filePath(index)
        if self.fs_model.isDir(index): return
        for i in range(self.editor_tabs.count()):
            if self.editor_tabs.widget(i).property("file_path") == file_path:
                self.editor_tabs.setCurrentIndex(i); return
        try:
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
            editor = QTextEdit(); editor.setPlainText(content)
            editor.setProperty("file_path", file_path); SimpleSyntaxHighlighter(editor.document())
            self.editor_tabs.addTab(editor, Path(file_path).name)
            self.editor_tabs.setCurrentWidget(editor)
        except Exception as e: QMessageBox.critical(self, "Error", f"Could not open file:\n{e}")

    def close_tab(self, index):
        self.editor_tabs.removeTab(index)
        
    def update_action_states(self):
        """Enables or disables toolbar actions based on whether a project is loaded."""
        project_loaded = self.current_project_path is not None
        self.play_action.setEnabled(project_loaded)
        self.build_action.setEnabled(project_loaded)

    def play_project(self):
        if not self.current_project_path: return
        index_path = Path(self.current_project_path) / "src" / "index.html"
        if index_path.exists():
            self.preview.setUrl(QUrl.fromLocalFile(str(index_path.resolve())))
        else:
            self.output_console.append("Error: 'src/index.html' not found.")
    
    def build_project(self):
        if not self.current_project_path: return
        
        self.output_console.clear()
        self.output_console.append("Starting build process...")
        
        self.build_process = QProcess()
        self.build_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.build_process.readyReadStandardOutput.connect(self.handle_build_output)
        self.build_process.finished.connect(self.on_build_finished)
        
        # IMPORTANT: Set the working directory so npm can find package.json
        self.build_process.setWorkingDirectory(self.current_project_path)

        # Defines the actual command to be run.
        # NOTE: This requires Node.js and npm to be installed, and for the
        # project to have a 'package.json' with a "build" script.
        self.build_process.start("npm", ["run", "build"])
        
        self.build_action.setEnabled(False) # Disable button during build

    def handle_build_output(self):
        data = self.build_process.readAllStandardOutput().data().decode()
        self.output_console.append(data.strip())
        
    def on_build_finished(self):
        exit_code = self.build_process.exitCode()
        if exit_code == 0:
            self.output_console.append("\nBuild completed successfully.")
        else:
            self.output_console.append(f"\nBuild failed with exit code: {exit_code}")
        self.build_process = None
        self.build_action.setEnabled(True) # Re-enable the button

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # A simple stylesheet for a dark look
    app.setStyleSheet("QWidget { background-color: #2b2b2b; color: #f0f0f0; } QMainWindow, QDockWidget, QTabWidget, QMenu, QMenuBar, QToolBar { background-color: #3c3c3c; } QTreeView { background-color: #2b2b2b; border: none; } QTextEdit { background-color: #1e1e1e; font-family: Consolas, monospace; border: none; } QPushButton, QLineEdit { background-color: #555; border: 1px solid #777; padding: 5px; } QPushButton:hover { background-color: #666; } QWizard, QMessageBox { background-color: #3c3c3c; }")
    window = BasicWebsiteStudio()
    window.show()
    sys.exit(app.exec())