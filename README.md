# Basic Website Studio (Tkinter Edition)

A simple, lightweight code editor for basic web development, written in
Python using the standard Tkinter GUI toolkit. This application is
designed to run without any external Python libraries (like PySide6 or
PyQt), making it ideal for easy distribution on Linux systems, such as
in a `.deb` package.



*(This is a representative screenshot of what the application might look
like)*

## ✨ Key Features

-   **Project Wizard**: Create new projects with a standard directory
    structure (`src/css`, `src/js`, `assets`).
-   **File Explorer**: View project files and folders in a tree view.
-   **Tabbed Editor**: Open and edit multiple files in separate tabs.
-   **Simple Syntax Highlighting**: Basic highlighting for HTML tags,
    attributes, and strings.
-   **Live Preview**: Opens the project\'s `index.html` file in the
    system\'s default web browser.
-   **Build Integration**: A \"Build\" button that executes
    `npm run build` in the project directory (requires Node.js/npm).
-   **Dependency-Free (Python)**: Uses only the Python standard library,
    making it highly portable.
-   **Dark Theme**: A pleasant, dark user interface for focused work.
  <img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/89597080-41d9-4b2c-8a97-7d2bb7f2f994" />


## 🎯 Project Goal

The original version of this application was developed using PySide6.
This version has been completely ported to **Tkinter** to meet a crucial
requirement: **maximum portability and ease of packaging on Linux**.

By exclusively using Python\'s built-in modules, the need to install
heavy GUI frameworks via `pip` is eliminated. This significantly
simplifies the creation of a standalone Debian package (`.deb`), as the
only core system dependency is `python3-tk`, which is readily available
on most desktop Linux systems.

## 🛠️ Requirements

No `pip` installations are needed for the Python code itself. However, a
few system packages are required.

### Mandatory (for basic functionality)

1.  **Python 3**: Should be pre-installed on most Linux systems.
2.  **Tkinter Library**: Python\'s interface to the Tk GUI toolkit.

### Optional (for the \"Build Project\" feature)

1.  **Node.js and npm**: Required to run JavaScript-based build
    processes.

## 🚀 Installation & Usage

Follow these steps to get the application running.

**1. Install System Dependencies (for Debian/Ubuntu-based systems):**

    # Update your system's package list
    sudo apt-get update

    # Install Tkinter for Python 3 (required)
    sudo apt-get install python3-tk

    # Install Node.js and npm (optional, for the build feature)
    sudo apt-get install nodejs npm

**2. Download the Application:**

Download the `main.py` file or clone the repository if it\'s available
in one.

    # Example for cloning a repository
    git clone https://example.com/your-repo.git
    cd your-repo

**3. Launch the Application:**

Run the Python script from your terminal.

    python3 main.py

The application window should now appear.

## 📝 How It Works

### Project Creation

The \"New Project\...\" wizard creates the following structure and
populates it with default files:

    YourProjectName/
    ├── project.bws          # Editor configuration file
    ├── src/
    │   ├── index.html
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── main.js
    └── assets/
        └── images/

### Build Process

The \"Build Project\" button is a simple shortcut for the
`npm run build` command. For this to work, your project must contain a
`package.json` file in its root directory that defines a script named
`"build"`.

**Example `package.json`:**

    {
      "name": "my-project",
      "version": "1.0.0",
      "scripts": {
        "build": "echo 'Building...' && rm -rf dist && mkdir dist && cp -r src/* dist/"
      }
    }

The output from the build process will be displayed in the \"Output\"
panel at the bottom of the application.

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file
for more details.
