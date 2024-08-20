# Bater

**Bater** is a graphical application for managing and executing terminal commands. Developed in Python with wxPython, this tool allows you to add, edit, and delete commands, as well as view their execution history.

## Features

- **Manage Applications:** Add and organize applications for which you want to create commands.
- **Execute Commands:** Run commands directly from the graphical interface.
- **View Command History:** Access a detailed history of command executions, edits, and creations.
- **Edit and Delete Commands:** Modify or remove applications and commands as needed.
- **Command Safety:** Built-in checks to warn about potentially dangerous commands.

## Requirements

- Python 3.x
- wxPython (`pip install wxPython`)

## Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/xrcm/bater.git
   ```

2. Navigate to the project directory:
   ```sh
   cd bater
   ```

3. Run the application:
   ```sh
   python init.py
   ```

## Usage

- **Add an Application:** Click on "BATER" > "Add APP" and enter the name of the application.
- **Add a Command:** Select the application and click "Add Cmd" to add a new command.
- **Run a Command:** Click "Run" next to the desired command to execute it.
- **View History:** Click "History" to view the execution history of a command.
- **Edit/Delete Applications and Commands:** Use the "Edit" and "Del" options in the application frames to modify or remove items.
- **Restart Application:** Click "Restart" under "BATER" to restart the application.
- **Exit Application:** Click "Exit" under "BATER" to quit the application.

## Contribution

1. Fork the repository.
2. Create a branch for your feature:
   ```sh
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```sh
   git commit -am 'Description of your changes'
   ```
4. Push to the branch:
   ```sh
   git push origin feature/your-feature-name
   ```
5. Create a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
