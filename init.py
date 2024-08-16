import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import threading
import json
import os
import uuid
import re


class CommandApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BATER: Terminal Command Controller")
        self.root.minsize(640, 400)
        self.center_window()
        self.keep_on_top()

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

    def keep_on_top(self):
        self.root.wm_attributes('-topmost', 1)
        self.root.wm_attributes('-topmost', 0)

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

                history_button = tk.Button(command_frame, text="History",
                                           command=lambda cmd_id=command_id, app=app_name: self.show_command_history(
                                               app, cmd_id))
                history_button.pack(side=tk.LEFT, padx=5)

    def on_frame_home_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def open_add_application_window(self):
        app_name = simpledialog.askstring("Add Application", "Enter application name:")
        if app_name and self.command_manager.add_application(app_name):
            self.update_home_display()
        else:
            messagebox.showwarning("Warning", "Application already exists or invalid name.")

    def open_add_command_window(self, app_name):
        AddCommandWindow(self, app_name)

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
            "4. **About**: Go to 'About' > 'About' for information about the application.\n"
            "5. **Exit**: Go to 'File' > 'Exit' or press Ctrl+Q to quit the application.\n"
        )
        messagebox.showinfo("Help", help_text)

    def open_about_window(self):
        about_text = "BATER: Terminal Command Controller\nVersion 1.0\nCreated by Your Name"
        messagebox.showinfo("About", about_text)

    def open_variable_prompt(self, command_template):
        def on_submit():
            self.submit_variables(command_template)
            prompt_window.destroy()

        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("Enter Variables")
        prompt_window.geometry("300x200")

        tk.Label(prompt_window, text="Enter values for the following placeholders:").pack(pady=10)

        self.variables = {}
        placeholders = self.extract_placeholders(command_template)

        for placeholder in placeholders:
            tk.Label(prompt_window, text=f"{placeholder}:").pack(pady=5)
            entry = tk.Entry(prompt_window)
            entry.pack(pady=5)
            self.variables[placeholder] = entry

        tk.Button(prompt_window, text="Submit", command=on_submit).pack(pady=10)

    def extract_placeholders(self, command):
        return list(set(re.findall(r'{(\w+)}', command)))

    def submit_variables(self, command_template):
        command = command_template
        for ph, entry in self.variables.items():
            value = entry.get()
            command = command.replace(f"{{{ph}}}", value)

        messagebox.showinfo("Final Command", f"Executing: {command}")
        self.execute_command(command)

    def execute_command(self, command):
        def run_command():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                self.root.after(0, lambda: messagebox.showinfo("Command Result",
                                                               f"Command executed successfully!\n\nOutput:\n{result.stdout}"))
                self.command_manager.add_to_history(command, result.stdout)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Execution Error", str(e)))

        threading.Thread(target=run_command).start()

    def show_command_history(self, app_name, command_id):
        command = self.command_manager.commands.get(app_name, {}).get(command_id, {})
        if not command:
            messagebox.showwarning("Warning", "Command not found.")
            return

        history = command.get('history', [])
        history_text = "\n".join(history) if history else "No history available."

        history_window = tk.Toplevel(self.root)
        history_window.title("Command History")
        history_window.geometry("400x300")

        tk.Label(history_window, text="Command History:").pack(pady=10)
        history_text_box = tk.Text(history_window, wrap=tk.WORD)
        history_text_box.insert(tk.END, history_text)
        history_text_box.pack(pady=10, fill=tk.BOTH, expand=True)
        history_text_box.config(state=tk.DISABLED)


class AddCommandWindow:
    def __init__(self, parent_app, app_name):
        self.parent_app = parent_app
        self.app_name = app_name

        self.window = tk.Toplevel(parent_app.root)
        self.window.title("Add New Command")
        self.window.geometry("400x300")

        tk.Label(self.window, text="Command Name:").pack(pady=5)
        self.command_name_entry = tk.Entry(self.window)
        self.command_name_entry.pack(pady=5)

        tk.Label(self.window, text="Command Text:").pack(pady=5)
        self.command_text_entry = tk.Entry(self.window)
        self.command_text_entry.pack(pady=5)

        tk.Label(self.window, text="Enter variables below:").pack(pady=5)

        self.variables_frame = tk.Frame(self.window)
        self.variables_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.add_variable_button = tk.Button(self.window, text="Add Variable", command=self.add_variable_entry)
        self.add_variable_button.pack(pady=5)

        tk.Button(self.window, text="Save Command", command=self.save_command).pack(pady=10)

        self.variable_entries = []

    def add_variable_entry(self):
        variable_frame = tk.Frame(self.variables_frame)
        variable_frame.pack(pady=5, fill=tk.X)

        tk.Label(variable_frame, text="Variable Name:").pack(side=tk.LEFT, padx=5)
        variable_name_entry = tk.Entry(variable_frame)
        variable_name_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(variable_frame, text="Default Value:").pack(side=tk.LEFT, padx=5)
        default_value_entry = tk.Entry(variable_frame)
        default_value_entry.pack(side=tk.LEFT, padx=5)

        self.variable_entries.append((variable_name_entry, default_value_entry))

    def save_command(self):
        command_name = self.command_name_entry.get().strip()
        command_text = self.command_text_entry.get().strip()

        if not command_name or not command_text:
            messagebox.showwarning("Warning", "Command name and command text cannot be empty.")
            return

        variables = {}
        for var_name_entry, default_value_entry in self.variable_entries:
            var_name = var_name_entry.get().strip()
            default_value = default_value_entry.get().strip()
            if var_name:
                variables[var_name] = default_value

        if self.parent_app.command_manager.add_command(self.app_name, command_name, command_text, variables):
            self.parent_app.update_home_display()
            self.window.destroy()
        else:
            messagebox.showwarning("Warning", "Failed to add command. The command may already exist.")


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

    def add_command(self, app_name, command_name, command_text, variables):
        if app_name not in self.commands:
            return False
        command_id = str(uuid.uuid4())
        self.commands[app_name][command_id] = {
            'name': command_name,
            'command': command_text,
            'variables': variables,
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

    def add_to_history(self, command, output):
        for app, commands in self.commands.items():
            for cmd_id, cmd_data in commands.items():
                if cmd_data['command'] == command:
                    cmd_data['history'].append(output)
                    self.save_commands()
                    return


if __name__ == "__main__":
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()
