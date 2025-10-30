import sys
import os
import json
import subprocess
import threading
from pathlib import Path
import webbrowser

# Import necessary Tkinter modules
from tkinter import (
    Tk, Frame, Menu, Text, Scrollbar, messagebox,
    StringVar, Label, Entry, Button, filedialog, PanedWindow, Toplevel
)
from tkinter import ttk

# --- Simple Syntax Highlighter for Tkinter Text Widget ---
class SimpleSyntaxHighlighter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.rules = [
            (r'<[/?!]?\w+', 'tag'),
            (r'>', 'tag'),
            (r'\b\w+(?=\=)', 'attribute'),
            (r'"[^"]*"', 'string'),
            (r"'[^']*'", 'string'),
        ]
        self.text_widget.tag_configure('tag', foreground='#569CD6')
        self.text_widget.tag_configure('attribute', foreground='#9CDCFE')
        self.text_widget.tag_configure('string', foreground='#CE9178')
        
        self.text_widget.bind('<KeyRelease>', self.on_key_release)

    def on_key_release(self, event=None):
        self.highlight()

    def highlight(self):
        # Remove all existing tags to avoid overlaps
        for tag in ['tag', 'attribute', 'string']:
            self.text_widget.tag_remove(tag, '1.0', 'end')
        
        # Apply new tags
        content = self.text_widget.get('1.0', 'end-1c')
        for pattern, tag_name in self.rules:
            import re
            for match in re.finditer(pattern, content):
                start_index = f"1.0+{match.start()}c"
                end_index = f"1.0+{match.end()}c"
                self.text_widget.tag_add(tag_name, start_index, end_index)

# --- Project Creation Wizard ---
class ProjectWizard(object):
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        
        self.top = Toplevel(parent)
        self.top.title("Create New Project")
        
        # Simple layout
        main_frame = ttk.Frame(self.top, padding=10)
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Project Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.name_edit = ttk.Entry(main_frame, width=50)
        self.name_edit.grid(row=1, column=0, columnspan=2, sticky='ew')

        ttk.Label(main_frame, text="Location:").grid(row=2, column=0, sticky='w', pady=2)
        self.path_edit = ttk.Entry(main_frame)
        self.path_edit.insert(0, str(Path.home()))
        self.path_edit.grid(row=3, column=0, sticky='ew')
        
        self.browse_button = ttk.Button(main_frame, text="Browse...", command=self.select_path)
        self.browse_button.grid(row=3, column=1, sticky='ew', padx=(5,0))

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10,0), sticky='e')
        ttk.Button(button_frame, text="Create", command=self.accept).pack(side='left')
        ttk.Button(button_frame, text="Cancel", command=self.top.destroy).pack(side='left', padx=(5,0))

        self.top.transient(parent)
        self.top.grab_set()
        self.parent.wait_window(self.top)

    def select_path(self):
        path = filedialog.askdirectory(title="Select Location", initialdir=self.path_edit.get())
        if path:
            self.path_edit.delete(0, 'end')
            self.path_edit.insert(0, path)

    def accept(self):
        project_name = self.name_edit.get().strip()
        project_path = self.path_edit.get().strip()
        if not project_name or not project_path:
            messagebox.showerror("Error", "Project name and location cannot be empty.", parent=self.top)
            return

        full_path = Path(project_path) / project_name
        try:
            # Create directory structure
            os.makedirs(full_path / "src" / "js", exist_ok=True)
            os.makedirs(full_path / "src" / "css", exist_ok=True)
            os.makedirs(full_path / "assets" / "images", exist_ok=True)
            
            # Create default files
            (full_path / "src" / "index.html").write_text(f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{project_name}</title>\n    <link rel=\"stylesheet\" href=\"css/style.css\">\n</head>\n<body>\n    <h1>Welcome to {project_name}</h1>\n    <script src=\"js/main.js\"></script>\n</body>\n</html>", encoding='utf-8')
            (full_path / "src" / "css" / "style.css").write_text("body {\n    font-family: sans-serif;\n    background-color: #f0f0f0;\n    color: #111;\n}", encoding='utf-8')
            (full_path / "src" / "js" / "main.js").write_text("console.log('Project loaded successfully!');", encoding='utf-8')
            
            # Create project config file
            project_config = {"name": project_name, "version": "1.0.0"}
            with open(full_path / "project.bws", "w", encoding='utf-8') as f: json.dump(project_config, f, indent=4)
            
            self.result = str(full_path)
            self.top.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create project:\n{e}", parent=self.top)

# --- The Main Application Window ---
class BasicWebsiteStudio(Tk):
    def __init__(self):
        super().__init__()
        self.title("Basic Website Studio")
        self.geometry("1600x900")
        self.current_project_path = None
        self.build_process = None
        self.open_tabs = {} # To track file paths and their corresponding tabs

        self._setup_styles()
        self._setup_menus()
        self._setup_ui_layout()
        
        self.update_action_states() # Initially disable actions

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        # Dark theme configuration
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TLabel", background="#2b2b2b", foreground="#f0f0f0")
        style.configure("TButton", background="#555", foreground="#f0f0f0", borderwidth=1)
        style.map("TButton", background=[('active', '#666')])
        style.configure("TEntry", fieldbackground="#555", foreground="#f0f0f0", borderwidth=1, insertbackground="#f0f0f0")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="#f0f0f0", borderwidth=0)
        style.map("Treeview", background=[('selected', '#555')])
        style.configure("TNotebook", background="#3c3c3c", borderwidth=0)
        style.configure("TNotebook.Tab", background="#3c3c3c", foreground="#f0f0f0", borderwidth=0, padding=[5, 2])
        style.map("TNotebook.Tab", background=[('selected', '#2b2b2b')])

    def _setup_menus(self):
        self.menubar = Menu(self, bg="#3c3c3c", fg="#f0f0f0", activebackground="#555", activeforeground="#f0f0f0", borderwidth=0)
        self.config(menu=self.menubar)
        
        file_menu = Menu(self.menubar, tearoff=0, bg="#3c3c3c", fg="#f0f0f0")
        file_menu.add_command(label="New Project...", command=self.create_new_project)
        file_menu.add_command(label="Open Project...", command=self.open_project)
        self.menubar.add_cascade(label="File", menu=file_menu)

    def _setup_ui_layout(self):
        # Toolbar
        toolbar = ttk.Frame(self, style="TFrame")
        self.play_button = ttk.Button(toolbar, text="▶ Play (Preview)", command=self.play_project)
        self.play_button.pack(side='left', padx=2, pady=2)
        self.build_button = ttk.Button(toolbar, text="✓ Build Project", command=self.build_project)
        self.build_button.pack(side='left', padx=2, pady=2)
        toolbar.pack(side='top', fill='x')

        # Main layout using PanedWindow
        main_pane = PanedWindow(self, orient='horizontal', sashrelief='raised', bg='#3c3c3c')
        main_pane.pack(fill='both', expand=True)

        # Project Explorer
        project_frame = ttk.Frame(main_pane) # Removed width for better auto-sizing
        self.project_view = ttk.Treeview(project_frame)
        self.project_view.pack(fill='both', expand=True)
        self.project_view.bind("<Double-1>", self.on_tree_double_click)
        main_pane.add(project_frame)

        # Right pane (Editor + Console)
        right_pane = PanedWindow(main_pane, orient='vertical', sashrelief='raised', bg='#3c3c3c')
        main_pane.add(right_pane)

        # Editor Tabs
        self.editor_tabs = ttk.Notebook(right_pane)
        # KORRIGIERTE ZEILE HIER:
        right_pane.add(self.editor_tabs)

        # Output Console
        console_frame = ttk.Frame(right_pane)
        self.output_console = Text(console_frame, wrap='word', state='disabled', bg="#1e1e1e", fg="#f0f0f0", font=("Consolas", 10), borderwidth=0)
        console_scroll = Scrollbar(console_frame, command=self.output_console.yview)
        self.output_console['yscrollcommand'] = console_scroll.set
        console_scroll.pack(side='right', fill='y')
        self.output_console.pack(side='left', fill='both', expand=True)
        # KORRIGIERTE ZEILE HIER:
        right_pane.add(console_frame)

    def create_new_project(self):
        wizard = ProjectWizard(self)
        if wizard.result:
            self.load_project(wizard.result)

    def open_project(self):
        dir_name = filedialog.askdirectory(title="Open Project")
        if dir_name and (Path(dir_name) / "project.bws").exists():
            self.load_project(dir_name)
        elif dir_name:
            messagebox.showwarning("Error", "This is not a valid project folder (project.bws is missing).")

    def load_project(self, path):
        self.current_project_path = path
        self.title(f"Basic Website Studio - {Path(path).name}")
        self.populate_project_view(path)
        self.update_action_states()
        self.play_project()

    def populate_project_view(self, path):
        for item in self.project_view.get_children():
            self.project_view.delete(item)
        
        abspath = os.path.abspath(path)
        root_node = self.project_view.insert('', 'end', text=os.path.basename(path), open=True, values=[abspath])
        self.process_directory(root_node, abspath)

    def process_directory(self, parent, path):
        for p in sorted(Path(path).iterdir()):
            abspath = os.path.abspath(p)
            isdir = os.path.isdir(abspath)
            node = self.project_view.insert(parent, 'end', text=p.name, open=False, values=[abspath])
            if isdir:
                self.process_directory(node, abspath)

    def on_tree_double_click(self, event):
        item_id = self.project_view.focus()
        if not item_id: return
        
        file_path = self.project_view.item(item_id)['values'][0]
        if not os.path.isfile(file_path): return

        if file_path in self.open_tabs:
            self.editor_tabs.select(self.open_tabs[file_path])
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
            
            tab_frame = ttk.Frame(self.editor_tabs)
            editor = Text(tab_frame, wrap='word', bg="#1e1e1e", fg="#f0f0f0", font=("Consolas", 11), insertbackground="white", borderwidth=0, undo=True)
            editor_scroll = Scrollbar(tab_frame, command=editor.yview)
            editor['yscrollcommand'] = editor_scroll.set
            editor_scroll.pack(side='right', fill='y')
            editor.pack(fill='both', expand=True)
            editor.insert('1.0', content)
            
            SimpleSyntaxHighlighter(editor)
            
            self.editor_tabs.add(tab_frame, text=os.path.basename(file_path))
            self.open_tabs[file_path] = tab_frame
            self.editor_tabs.select(tab_frame)
            editor.focus_set()

        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def update_action_states(self):
        project_loaded = self.current_project_path is not None
        state = 'normal' if project_loaded else 'disabled'
        self.play_button.config(state=state)
        self.build_button.config(state=state)

    def play_project(self):
        if not self.current_project_path: return
        index_path = Path(self.current_project_path) / "src" / "index.html"
        if index_path.exists():
            webbrowser.open(index_path.resolve().as_uri())
        else:
            self.log_to_console("Error: 'src/index.html' not found.")

    def build_project(self):
        if not self.current_project_path: return
        
        self.log_to_console("Starting build process...")
        self.build_button.config(state='disabled')
        
        thread = threading.Thread(target=self._run_build_process, daemon=True)
        thread.start()

    def _run_build_process(self):
        try:
            command = ["npm", "run", "build"]
            # Hide the console window on Windows
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                command,
                cwd=self.current_project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                startupinfo=startupinfo
            )

            for line in iter(process.stdout.readline, ''):
                self.log_to_console(line.strip())

            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                self.log_to_console("\nBuild completed successfully.")
            else:
                self.log_to_console(f"\nBuild failed with exit code: {return_code}")

        except FileNotFoundError:
            self.log_to_console("\nError: 'npm' command not found. Is Node.js installed and in your PATH?")
        except Exception as e:
            self.log_to_console(f"\nAn unexpected error occurred during build: {e}")
        finally:
            self.after(100, lambda: self.build_button.config(state='normal'))

    def log_to_console(self, message):
        def append():
            self.output_console.config(state='normal')
            self.output_console.insert('end', message + '\n')
            self.output_console.see('end')
            self.output_console.config(state='disabled')
        # Schedule the GUI update on the main thread
        self.after(0, append)

if __name__ == "__main__":
    app = BasicWebsiteStudio()
    app.mainloop()
