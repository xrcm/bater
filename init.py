import tkinter as tk
from tkinter import simpledialog, messagebox, Menu
import subprocess
import json
import os
import shutil
from datetime import datetime
import uuid
import threading

class CommandManager:
    def __init__(self, json_file='commands.json'):
        self.json_file = json_file
        self.commands = self.load_commands()

    def load_commands(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        self.validate_commands_data(data)
                        return data
                    else:
                        raise ValueError("Invalid data format")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading JSON: {e}")
                self.handle_invalid_json()
                return {}
        else:
            self.create_new_json_file()
            return {}

    def validate_commands_data(self, data):
        for app_name, commands in data.items():
            if not isinstance(commands, dict):
                raise ValueError("Invalid commands format")
            for command_id, command_data in commands.items():
                if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    raise ValueError("Invalid command structure.")

    def save_commands(self):
        with open(self.json_file, 'w') as file:
            json.dump(self.commands, file, indent=4)

    def handle_invalid_json(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_file = f"{self.json_file}_old_{timestamp}.json"
        shutil.copy(self.json_file, backup_file)
        self.create_new_json_file()
        messagebox.showinfo("Backup Created", f"Backup of the old file created as '{backup_file}'")

    def create_new_json_file(self):
        with open(self.json_file, 'w') as file:
            json.dump({}, file, indent=4)

    def add_application(self, app_name):
        if app_name.lower() not in [key.lower() for key in self.commands.keys()]:
            self.commands[app_name] = {}
            self.save_commands()
            return True
        return False

    def add_command(self, app_name, command_name, command_text):
        if app_name in self.commands:
            command_id = str(uuid.uuid4())
            self.commands[app_name][command_id] = {
                'name': command_name,
                'command': command_text,
                'history': []
            }
            self.save_commands()
            return True
        return False

    def edit_command(self, app_name, command_id, new_name, new_command_text):
        if app_name in self.commands and command_id in self.commands[app_name]:
            self.commands[app_name][command_id] = {
                'name': new_name,
                'command': new_command_text,
                'history': self.commands[app_name][command_id]['history']
            }
            self.save_commands()
            return True
        return False

    def delete_command(self, app_name, command_id):
        if app_name in self.commands and command_id in self.commands[app_name]:
            del self.commands[app_name][command_id]
            if not self.commands[app_name]:  # Remove the application if it has no commands left
                del self.commands[app_name]
            self.save_commands()
            return True
        return False

    def get_command_history(self, app_name, command_id):
        return self.commands.get(app_name, {}).get(command_id, {}).get('history', [])

    def add_command_history(self, app_name, command_id, entry):
        if app_name in self.commands and command_id in self.commands[app_name]:
            self.commands[app_name][command_id]['history'].append(entry)
            self.save_commands()

    def export_commands(self, export_file):
        with open(export_file, 'w') as file:
            json.dump(self.commands, file, indent=4)

    def import_commands(self, import_file):
        if os.path.exists(import_file):
            with open(import_file, 'r') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    self.validate_commands_data(data)
                    self.commands = data
                    self.save_commands()
                    return True
        return False

    def run_command(self, command):
        if command.strip():
            try:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                success = process.returncode == 0
                result = stdout.decode().strip() or stderr.decode().strip()
                return success, result
            except Exception as e:
                return False, str(e)
        return False, "Command is empty."


class CommandApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BATER: Terminal Command Controller")
        self.root.minsize(640, 400)
        self.center_window()

        self.command_manager = CommandManager()

        self.create_menu_bar()
        self.setup_home_frame()
        self.update_home_display()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_menu_bar(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add Application", command=self.open_add_application_window)
        file_menu.add_command(label="Exit", command=self.quit_application)
        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.open_help_window)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        about_menu = tk.Menu(menu_bar, tearoff=0)
        about_menu.add_command(label="About", command=self.open_about_window)
        menu_bar.add_cascade(label="About", menu=about_menu)

    def setup_home_frame(self):
        self.frame_home = tk.Frame(self.root)
        self.canvas = tk.Canvas(self.frame_home)
        self.scrollbar = tk.Scrollbar(self.frame_home, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame_home_inner = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_home_inner, anchor="nw")

        self.frame_home.pack(pady=10, fill=tk.BOTH, expand=True)
        self.frame_home_inner.bind("<Configure>", self.on_frame_home_inner_configure)

    def update_home_display(self):
        for widget in self.frame_home_inner.winfo_children():
            widget.destroy()

        row = 0
        col = 0

        for app_name, app_commands in self.command_manager.commands.items():
            if not isinstance(app_commands, dict):
                continue

            app_frame = tk.LabelFrame(self.frame_home_inner, text=app_name, padx=10, pady=10)
            app_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            col += 1
            if col > 1:
                col = 0
                row += 1

            add_command_button = tk.Button(app_frame, text="Add Cmd",
                                           command=lambda app=app_name: self.open_add_command_window(app))
            add_command_button.pack(pady=5, padx=5)

            for command_id, command_data in app_commands.items():
                if not isinstance(command_data,
                                  dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    continue

                command_name = command_data['name']
                command = command_data['command']

                command_frame = tk.Frame(app_frame)
                command_frame.pack(pady=5, padx=5)

                command_label = tk.Label(command_frame, text=command_name)
                command_label.pack(side=tk.LEFT)

                run_command_button = tk.Button(command_frame, text="Run",
                                               command=lambda cmd=command: self.open_variable_prompt(cmd))
                run_command_button.pack(side=tk.LEFT, padx=5)

                edit_command_button = tk.Button(command_frame, text="Edit", command=lambda cmd_id=command_id,
                                                                                           app=app_name: self.open_edit_command_window(
                    app, cmd_id))
                edit_command_button.pack(side=tk.LEFT, padx=5)

                delete_command_button = tk.Button(command_frame, text="Delete",
                                                  command=lambda cmd_id=command_id, app=app_name: self.delete_command(
                                                      app, cmd_id))
                delete_command_button.pack(side=tk.LEFT, padx=5)

    def on_frame_home_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def open_add_application_window(self):
        app_name = simpledialog.askstring("Add Application", "Enter application name:")
        if app_name and self.command_manager.add_application(app_name):
            self.update_home_display()
        else:
            messagebox.showwarning("Warning", "Application already exists or invalid name.")

    def open_add_command_window(self, app_name):
        command_name = simpledialog.askstring("Add Command", "Enter command name:")
        command_text = simpledialog.askstring("Add Command", "Enter command text:")
        if command_name and command_text and self.command_manager.add_command(app_name, command_name, command_text):
            self.update_home_display()
        else:
            messagebox.showwarning("Warning", "Failed to add command or invalid input.")

    def open_edit_command_window(self, app_name, command_id):
        command_data = self.command_manager.commands.get(app_name, {}).get(command_id, {})
        if not command_data:
            messagebox.showwarning("Warning", "Command not found.")
            return

        new_name = simpledialog.askstring("Edit Command", "Enter new command name:", initialvalue=command_data['name'])
        new_command_text = simpledialog.askstring("Edit Command", "Enter new command text:",
                                                  initialvalue=command_data['command'])
        if new_name and new_command_text and self.command_manager.edit_command(app_name, command_id, new_name,
                                                                               new_command_text):
            self.update_home_display()
        else:
            messagebox.showwarning("Warning", "Failed to edit command or invalid input.")

    def delete_command(self, app_name, command_id):
        if self.command_manager.delete_command(app_name, command_id):
            self.update_home_display()
        else:
            messagebox.showwarning("Warning", "Failed to delete command.")

    def quit_application(self):
        self.root.quit()

    def open_help_window(self):
        help_text = (
            "Help:\n\n"
            "1. **Add Application**: Go to 'Applications' > 'Add Application' or press Ctrl+A to add a new application.\n"
            "2. **Add Command**: Click the 'Add Cmd' button within an application's frame to add a new command. You can also access this functionality from 'Applications' > 'Add Command'.\n"
            "3. **View Command History**: Click the 'History' button next to a command to view its execution history.\n"
            "4. **About**: Go to 'About' > 'About' or press Ctrl+B to learn more about this application.\n"
            "5. **Exit**: Quit the application by going to 'Exit' or pressing Ctrl+Q.\n\n"
            "For more information or assistance, please contact support."
        )
        messagebox.showinfo("Help", help_text)

    def open_about_window(self):
        about_text = ("BATER: Terminal Command Controller\n"
                      "Version 1.0\n"
                      "Developed by Your Name\n"
                      "© 2024")
        messagebox.showinfo("About", about_text)

    def open_variable_prompt(self, command_template):
        # Criar uma nova janela para capturar as variáveis
        variable_window = tk.Toplevel(self.root)
        variable_window.title("Enter Command Variables")

        self.variables = {}  # Armazenar os valores das variáveis

        # Analisar placeholders no comando
        placeholders = self.extract_placeholders(command_template)
        variable_entries = {ph: 'text' for ph in placeholders}  # Aqui você pode ajustar os tipos de variáveis

        for ph in placeholders:
            tk.Label(variable_window, text=f"Enter value for {ph}:").pack()
            entry = tk.Entry(variable_window)
            entry.pack()
            self.variables[ph] = entry

        tk.Button(variable_window, text="Submit", command=lambda: self.submit_variables(command_template)).pack()

    def extract_placeholders(self, command_template):
        import re
        return re.findall(r'\{(\w+)\}', command_template)

    def submit_variables(self, command_template):
        command = command_template
        for ph, entry in self.variables.items():
            value = entry.get()
            command = command.replace(f"{{{ph}}}", value)

        # Exibir comando final e execução
        messagebox.showinfo("Final Command", f"Executing: {command}")
        self.execute_command(command)

    def execute_command(self, command):
        def run_command():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                messagebox.showinfo("Command Result", f"Command executed successfully!\n\nOutput:\n{result.stdout}")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Command failed with error:\n{e.stderr}")

        threading.Thread(target=run_command).start()


class CommandManager:
    def __init__(self):
        self.commands = {}
        self.load_commands()

    def load_commands(self):
        if os.path.exists('commands.json'):
            with open('commands.json', 'r') as f:
                self.commands = json.load(f)
        else:
            self.commands = {}

    def save_commands(self):
        with open('commands.json', 'w') as f:
            json.dump(self.commands, f, indent=4)

    def add_application(self, app_name):
        if app_name in self.commands:
            return False
        self.commands[app_name] = {}
        self.save_commands()
        return True

    def add_command(self, app_name, command_name, command_text):
        if app_name not in self.commands:
            return False
        command_id = str(uuid.uuid4())
        self.commands[app_name][command_id] = {
            'name': command_name,
            'command': command_text,
            'history': []
        }
        self.save_commands()
        return True

    def edit_command(self, app_name, command_id, new_name, new_command_text):
        if app_name not in self.commands or command_id not in self.commands[app_name]:
            return False
        self.commands[app_name][command_id]['name'] = new_name
        self.commands[app_name][command_id]['command'] = new_command_text
        self.save_commands()
        return True

    def delete_command(self, app_name, command_id):
        if app_name not in self.commands or command_id not in self.commands[app_name]:
            return False
        del self.commands[app_name][command_id]
        self.save_commands()
        return True


if __name__ == "__main__":
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()

