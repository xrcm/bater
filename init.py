import tkinter as tk
from tkinter import simpledialog, messagebox, Menu
import subprocess
import json
import os
import shutil
from datetime import datetime
import uuid
import threading
import time
import requests

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
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add Application", command=self.open_add_application_window)
        file_menu.add_command(label="Exit", command=self.quit_application)
        menu_bar.add_cascade(label="File", menu=file_menu)

        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.open_help_window)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        about_menu = Menu(menu_bar, tearoff=0)
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

            add_command_button = tk.Button(app_frame, text="Add Cmd", command=lambda app=app_name: self.open_add_command_window(app))
            add_command_button.pack(pady=5, padx=5)

            for command_id, command_data in app_commands.items():
                if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    continue

                command_name = command_data['name']
                command = command_data['command']

                command_frame = tk.Frame(app_frame)
                command_frame.pack(pady=5, padx=5)

                command_label = tk.Label(command_frame, text=command_name)
                command_label.pack(side=tk.LEFT)

                run_command_button = tk.Button(command_frame, text="Run", command=lambda cmd=command: self.run_command(cmd))
                run_command_button.pack(side=tk.LEFT, padx=5)

                edit_command_button = tk.Button(command_frame, text="Edit", command=lambda cmd_id=command_id, app=app_name: self.open_edit_command_window(app, cmd_id))
                edit_command_button.pack(side=tk.LEFT, padx=5)

                delete_command_button = tk.Button(command_frame, text="Delete", command=lambda cmd_id=command_id, app=app_name: self.delete_command(app, cmd_id))
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
        new_command_text = simpledialog.askstring("Edit Command", "Enter new command text:", initialvalue=command_data['command'])
        if new_name and new_command_text and self.command_manager.edit_command(app_name, command_id, new_name, new_command_text):
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
            "1. **Add Application**: Go to 'File' > 'Add Application' to add a new application.\n"
            "2. **Add Command**: Click the 'Add Cmd' button within an application's frame to add a new command.\n"
            "3. **View Command History**: Command history is maintained but not currently displayed.\n"
            "4. **About**: Learn more about this application from 'About'.\n"
            "5. **Exit**: Quit the application by going to 'File' > 'Exit'.\n\n"
            "For more information or assistance, please contact support."
        )
        messagebox.showinfo("Help", help_text)

    def open_about_window(self):
        about_text = ("BATER: Terminal Command Controller\n"
                      "Version 1.0\n"
                      "Developed by Your Name\n"
                      "© 2024")
        messagebox.showinfo("About", about_text)

    def run_command(self, command):
        if command.strip():
            self.root.config(cursor="wait")
            self.root.update_idletasks()

            def execute_command():
                success, result = self.command_manager.run_command(command)
                self.update_command_history(command, result, success)
                self.root.after(0, self.show_result, result, success)
                self.root.config(cursor="")
                self.root.update_idletasks()

            threading.Thread(target=execute_command, daemon=True).start()
        else:
            messagebox.showwarning("Warning", "Command is empty.")

    def update_command_history(self, command, result, success):
        """Atualiza o histórico do comando no JSON e salva."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for app_name, app_commands in self.command_manager.commands.items():
            for command_id, command_data in app_commands.items():
                if command_data['command'] == command:
                    command_data['history'].append(f"{timestamp} - {'Success' if success else 'Error'}: {result}")
                    self.command_manager.save_commands()
                    return

    def show_result(self, result, success):
        """Mostra o resultado da execução do comando."""
        if success:
            messagebox.showinfo("Success", result)
        else:
            messagebox.showerror("Error", result)

def main():
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
