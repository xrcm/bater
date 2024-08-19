import tkinter as tk
from tkinter import simpledialog, messagebox, Menu, scrolledtext
import subprocess
import json
import os
import shutil
from datetime import datetime
import uuid
import threading
import logging

# Configuração do logging
logging.basicConfig(filename='command_app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
                logging.error(f"Error loading JSON: {e}")
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
        """Salva os comandos atuais no arquivo JSON."""
        try:
            with open(self.json_file, 'w') as file:
                json.dump(self.commands, file, indent=4)
        except IOError as e:
            logging.error(f"Error saving commands: {e}")
            messagebox.showerror("Error", f"Failed to save commands. Details: {e}")

    def handle_invalid_json(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            backup_file = f"{self.json_file}_old_{timestamp}.json"
            shutil.copy(self.json_file, backup_file)
            self.create_new_json_file()
            messagebox.showinfo("Backup Created", f"Backup of the old file created as '{backup_file}'")
        except (shutil.Error, IOError) as e:
            logging.error(f"Error handling invalid JSON: {e}")
            messagebox.showerror("Error", f"Failed to backup and reset JSON file. Details: {e}")

    def create_new_json_file(self):
        try:
            with open(self.json_file, 'w') as file:
                json.dump({}, file, indent=4)
        except IOError as e:
            logging.error(f"Error creating new JSON file: {e}")
            messagebox.showerror("Error", f"Failed to create a new JSON file. Details: {e}")

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
            if not self.commands[app_name]:  # Remove a aplicação se não tiver mais comandos
                del self.commands[app_name]
            self.save_commands()
            return True
        return False

    def get_command_history(self, app_name, command_id):
        return self.commands.get(app_name, {}).get(command_id, {}).get('history', [])

    def add_command_history(self, app_name, command_id, entry):
        if app_name in self.commands and command_id in self.commands[app_name]:
            history = self.commands[app_name][command_id]['history']
            history.append(entry)
            if len(history) > 1000:
                history.pop(0)  # Mantém apenas os últimos 1000 registros
            self.save_commands()

    def export_commands(self, export_file):
        try:
            with open(export_file, 'w') as file:
                json.dump(self.commands, file, indent=4)
        except IOError as e:
            logging.error(f"Error exporting commands: {e}")
            messagebox.showerror("Error", f"Failed to export commands. Details: {e}")

    def import_commands(self, import_file):
        if os.path.exists(import_file):
            try:
                with open(import_file, 'r') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        self.validate_commands_data(data)
                        self.commands = data
                        self.save_commands()
                        return True
            except (FileNotFoundError, json.JSONDecodeError, ValueError, IOError) as e:
                logging.error(f"Error importing commands: {e}")
                messagebox.showerror("Error", f"Failed to import commands. Details: {e}")
        return False

    def run_command(self, command):
        if command.strip():
            try:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                success = process.returncode == 0
                result = stdout.decode().strip() or stderr.decode().strip()
                return success, result
            except (subprocess.SubprocessError, OSError) as e:
                logging.error(f"Error running command: {e}")
                return False, f"Failed to execute command. Details: {e}"
        return False, "Command is empty."


def extract_placeholders(command_template):
    import re
    return re.findall(r'\{(\w+)}', command_template)


class CommandApp:
    def __init__(self, root):
        try:
            self.root = root
            self.root.title("BATER: Terminal Command Controller")
            self.root.minsize(640, 400)
            self.center_window()

            self.command_manager = CommandManager()

            self.create_menu_bar()
            self.setup_home_frame()
            self.update_home_display()
        except Exception as e:
            logging.error(f"Error initializing the application: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize the application. Details: {e}")

    def center_window(self):
        try:
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            self.root.geometry(f'{width}x{height}+{x}+{y}')
        except ValueError as e:
            logging.error(f"Error centering the window: {e}")
            messagebox.showerror("Window Error", f"Failed to center the window. Details: {e}")

    def create_menu_bar(self):
        try:
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
        except tk.TclError as e:
            logging.error(f"Error creating menu bar: {e}")
            messagebox.showerror("Menu Error", f"Failed to create menu bar. Details: {e}")

    def setup_home_frame(self):
        try:
            self.frame_home = tk.Frame(self.root, bg="#f0f0f0")
            self.canvas = tk.Canvas(self.frame_home, bg="#f0f0f0")
            self.scrollbar = tk.Scrollbar(self.frame_home, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            self.scrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)

            self.frame_home_inner = tk.Frame(self.canvas, bg="#f0f0f0")
            self.canvas.create_window((0, 0), window=self.frame_home_inner, anchor="nw")

            self.frame_home.pack(pady=10, fill=tk.BOTH, expand=True)
            self.frame_home_inner.bind("<Configure>", self.on_frame_home_inner_configure)
        except tk.TclError as e:
            logging.error(f"Error setting up home frame: {e}")
            messagebox.showerror("Frame Error", f"Failed to set up home frame. Details: {e}")

    def update_home_display(self):
        try:
            for widget in self.frame_home_inner.winfo_children():
                widget.destroy()

            row = 0
            col = 0

            for app_name, app_commands in self.command_manager.commands.items():
                if not isinstance(app_commands, dict):
                    continue

                app_frame = tk.LabelFrame(self.frame_home_inner, text=app_name, padx=10, pady=10, bg="#ffffff")
                app_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

                col += 1
                if col > 1:
                    col = 0
                    row += 1

                add_command_button = tk.Button(app_frame, text="Add Cmd",
                                               command=lambda app=app_name: self.open_add_command_window(app))
                add_command_button.pack(pady=5, padx=5)

                for command_id, command_data in app_commands.items():
                    if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                        continue

                    command_name = command_data['name']
                    command = command_data['command']

                    command_frame = tk.Frame(app_frame, bg="#ffffff")
                    command_frame.pack(pady=5, padx=5)

                    command_label = tk.Label(command_frame, text=command_name, bg="#ffffff")
                    command_label.pack(side=tk.LEFT)

                    run_command_button = tk.Button(command_frame, text="Run",
                                                   command=lambda cmd=command: self.open_variable_prompt(cmd))
                    run_command_button.pack(side=tk.LEFT, padx=5)

                    edit_command_button = tk.Button(command_frame, text="Edit", command=lambda cmd_id=command_id,
                                                                                           app=app_name: self.open_edit_command_window(
                        app, cmd_id))
                    edit_command_button.pack(side=tk.LEFT, padx=5)

                    if self.command_manager.get_command_history(app_name, command_id):
                        history_button = tk.Button(command_frame, text="History",
                                                   command=lambda cmd_id=command_id, app=app_name: self.show_command_history(
                                                       app, cmd_id))
                        history_button.pack(side=tk.LEFT, padx=5)

                    delete_command_button = tk.Button(command_frame, text="Delete",
                                                      command=lambda cmd_id=command_id, app=app_name: self.delete_command(
                                                          app, cmd_id))
                    delete_command_button.pack(side=tk.LEFT, padx=5)
        except tk.TclError as e:
            logging.error(f"Error updating home display: {e}")
            messagebox.showerror("Display Error", f"Failed to update home display. Details: {e}")

    def on_frame_home_inner_configure(self, event):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except tk.TclError as e:
            logging.error(f"Error configuring frame: {e}")
            messagebox.showerror("Frame Error", f"Failed to configure frame. Details: {e}")

    def get_command_text(self):
        try:
            command_window = tk.Toplevel(self.root)
            command_window.title("Enter Command Text")

            tk.Label(command_window, text="Enter command text:").pack(pady=5)
            command_text_area = scrolledtext.ScrolledText(command_window, wrap=tk.WORD, width=60, height=10)
            command_text_area.pack(pady=10, padx=10)

            def submit_command():
                command = command_text_area.get("1.0", tk.END).strip()
                command_window.destroy()
                return command

            submit_button = tk.Button(command_window, text="Submit", command=submit_command)
            submit_button.pack(pady=10)

            command_window.grab_set()
            self.root.wait_window(command_window)

            return command_text_area.get("1.0", tk.END).strip()
        except tk.TclError as e:
            logging.error(f"Error getting command text: {e}")
            messagebox.showerror("Command Error", f"Failed to get command text. Details: {e}")

    def open_edit_command_window(self, app_name, command_id):
        try:
            command_data = self.command_manager.commands.get(app_name, {}).get(command_id, {})
            if not command_data:
                messagebox.showwarning("Warning", "Command not found.")
                return

            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edit Command: {command_data['name']}")

            tk.Label(edit_window, text="Command Name:").pack(pady=5)
            name_entry = tk.Entry(edit_window, width=50)
            name_entry.insert(0, command_data['name'])
            name_entry.pack(pady=5)

            tk.Label(edit_window, text="Command Text:").pack(pady=5)
            command_text_area = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, width=60, height=10)
            command_text_area.insert(tk.END, command_data['command'])
            command_text_area.pack(pady=10, padx=10)

            def save_changes():
                new_name = name_entry.get().strip()
                new_command_text = command_text_area.get("1.0", tk.END).strip()
                if new_name and new_command_text:
                    self.command_manager.edit_command(app_name, command_id, new_name, new_command_text)
                    self.update_home_display()

            def execute_command():
                command_text = command_text_area.get("1.0", tk.END).strip()
                self.execute_command(command_text)

            save_button = tk.Button(edit_window, text="Save", command=save_changes)
            save_button.pack(side=tk.LEFT, padx=10, pady=10)

            execute_button = tk.Button(edit_window, text="Execute", command=execute_command)
            execute_button.pack(side=tk.LEFT, padx=10, pady=10)

            close_button = tk.Button(edit_window, text="Close", command=edit_window.destroy)
            close_button.pack(side=tk.RIGHT, padx=10, pady=10)

            edit_window.grab_set()
            self.root.wait_window(edit_window)
        except (tk.TclError, ValueError) as e:
            logging.error(f"Error editing command: {e}")
            messagebox.showerror("Edit Error", f"Failed to edit command. Details: {e}")

    def show_command_history(self, app_name, command_id):
        try:
            history = self.command_manager.get_command_history(app_name, command_id)
            if not history:
                messagebox.showinfo("History", "No history available for this command.")
                return

            history_window = tk.Toplevel(self.root)
            history_window.title("Command History")

            tk.Label(history_window, text=f"History for Command: {self.command_manager.commands[app_name][command_id]['name']}").pack(pady=5)
            history_text = scrolledtext.ScrolledText(history_window, wrap=tk.WORD, width=80, height=20)
            history_text.pack(pady=10, padx=10)

            for entry in history[-1000:]:
                history_text.insert(tk.END, f"Executed on: {entry['timestamp']}\nResult: {entry['result']}\n\n")

            history_text.config(state=tk.DISABLED)

            tk.Button(history_window, text="Close", command=history_window.destroy).pack(pady=10)
        except (tk.TclError, ValueError) as e:
            logging.error(f"Error showing command history: {e}")
            messagebox.showerror("History Error", f"Failed to show command history. Details: {e}")

    def quit_application(self):
        try:
            self.root.quit()
        except tk.TclError as e:
            logging.error(f"Error quitting application: {e}")
            messagebox.showerror("Quit Error", f"Failed to quit application. Details: {e}")

    def open_help_window(self):
        try:
            help_text = (
                "Help:\n\n"
                "1. **Add Application**: Go to 'File' > 'Add Application' or press Ctrl+A to add a new application.\n"
                "2. **Add Command**: Click the 'Add Cmd' button within an application's frame to add a new command.\n"
                "3. **Edit Command**: Use the 'Edit' button next to a command to modify it.\n"
                "4. **Delete Command**: Use the 'Delete' button to remove a command.\n"
                "5. **Run Command**: Click 'Run' to execute a command and see the output.\n"
                "6. **Export/Import**: Commands can be exported and imported via the File menu.\n\n"
                "For further assistance, refer to the documentation or contact support."
            )
            self.show_info_window("Help", help_text)
        except tk.TclError as e:
            logging.error(f"Error opening help window: {e}")
            messagebox.showerror("Help Error", f"Failed to open help window. Details: {e}")

    def open_about_window(self):
        try:
            about_text = (
                "BATER: Terminal Command Controller\n"
                "Version 1.0\n"
                "Developed by Your Name\n"
                "© 2024"
            )
            self.show_info_window("About", about_text)
        except tk.TclError as e:
            logging.error(f"Error opening about window: {e}")
            messagebox.showerror("About Error", f"Failed to open about window. Details: {e}")

    def show_info_window(self, title, message):
        try:
            info_window = tk.Toplevel(self.root)
            info_window.title(title)

            tk.Label(info_window, text=message, justify=tk.LEFT, padx=10, pady=10).pack()
            tk.Button(info_window, text="Close", command=info_window.destroy).pack(pady=10)

            info_window.grab_set()
            self.root.wait_window(info_window)
        except tk.TclError as e:
            logging.error(f"Error showing info window: {e}")
            messagebox.showerror("Info Error", f"Failed to show info window. Details: {e}")

    def open_variable_prompt(self, command_template):
        try:
            variable_window = tk.Toplevel(self.root)
            variable_window.title("Enter Command Variables")

            self.variables = {}

            placeholders = extract_placeholders(command_template)

            for ph in placeholders:
                tk.Label(variable_window, text=f"Enter value for {ph}:").pack()
                entry = tk.Entry(variable_window)
                entry.pack()
                self.variables[ph] = entry

            tk.Button(variable_window, text="Submit", command=lambda: self.submit_variables(command_template)).pack()
        except tk.TclError as e:
            logging.error(f"Error opening variable prompt: {e}")
            messagebox.showerror("Variable Prompt Error", f"Failed to open variable prompt. Details: {e}")

    def submit_variables(self, command_template):
        try:
            command = command_template
            for ph, entry in self.variables.items():
                value = entry.get()
                command = command.replace(f"{{{ph}}}", value)

            messagebox.showinfo("Final Command", f"Executing: {command}")
            self.execute_command(command)
        except (tk.TclError, ValueError) as e:
            logging.error(f"Error submitting variables: {e}")
            messagebox.showerror("Variable Error", f"Failed to submit variables. Details: {e}")

    def execute_command(self, command):
        """
        Executa um comando shell em uma thread separada para evitar congelamento da interface gráfica.

        Args:
            command (str): O comando shell a ser executado.
        """
        def run_command():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                success_message = f"Command executed successfully: {command}\n\nOutput:\n{result.stdout}"
                logging.info(success_message)
                self.command_manager.add_command_history(app_name="Current App", command_id="Current Command",
                                                         entry={
                                                             "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                             "result": result.stdout.strip()})
                messagebox.showinfo("Command Result", success_message)
            except subprocess.CalledProcessError as e:
                error_message = f"Command failed with error: {command}\nError Output:\n{e.stderr}"
                logging.error(error_message)
                messagebox.showerror("Error", error_message)
            except tk.TclError as e:
                logging.error(f"Error displaying command result: {e}")
                messagebox.showerror("Execution Error", f"Failed to display command result. Details: {e}")

        threading.Thread(target=run_command).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()
