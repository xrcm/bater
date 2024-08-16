import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext, Menu
import subprocess
import json
import os
import shutil
from datetime import datetime
import uuid

class CommandApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BATER: Terminal Command Controller")
        self.root.minsize(640, 400)
        self.center_window()

        # Caminho do arquivo JSON
        self.json_file = 'commands.json'

        # Verifica e carrega dados do arquivo JSON
        self.commands = self.load_commands()

        # Cria a barra de menus
        self.create_menu_bar()

        # Frame para a página inicial com rolagem
        self.frame_home = tk.Frame(self.root)
        self.canvas = tk.Canvas(self.frame_home)
        self.scrollbar = tk.Scrollbar(self.frame_home, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.frame_home_inner = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_home_inner, anchor="nw")

        self.frame_home.pack(pady=10, fill=tk.BOTH, expand=True)
        self.frame_home_inner.bind("<Configure>", self.on_frame_home_inner_configure)

        # Atualiza a exibição dos comandos
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
        # Criando a barra de menu
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu Applications
        applications_menu = Menu(menu_bar, tearoff=0)
        applications_menu.add_command(label="Add Application", command=self.open_add_application_window)
        menu_bar.add_cascade(label="Applications", menu=applications_menu)

        # Menu Help
        help_menu = Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Help", command=self.open_help_window)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        # Menu About
        about_menu = Menu(menu_bar, tearoff=0)
        about_menu.add_command(label="About", command=self.open_about_window)
        menu_bar.add_cascade(label="About", menu=about_menu)

        # Botão "Sair" fixo no canto inferior direito
        self.quit_button = tk.Button(self.root, text="Sair", command=self.quit_application)
        self.quit_button.pack(side=tk.RIGHT, padx=10, pady=10, anchor=tk.SE)

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
                print(f"Invalid data for application '{app_name}': {commands}")
                raise ValueError("Invalid commands format")
            for command_id, command_data in commands.items():
                if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    print(f"Invalid command data in app '{app_name}': {command_data}")
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

    def open_add_application_window(self):
        app_name = simpledialog.askstring("Application Name", "Enter new application name:")
        if app_name:
            if app_name.lower() not in [key.lower() for key in self.commands.keys()]:
                self.commands[app_name] = {}
                self.save_commands()
                self.update_home_display()
            else:
                messagebox.showwarning("Warning", "Application already exists.")

    def open_help_window(self):
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")
        help_window.geometry("400x300")
        help_text = """\
        Welcome to BATER!

        1. **Add Application**: Click on 'Add Application' to create a new application.
        2. **Add Command**: Within an application, click 'Add Cmd' to add a new command.
        3. **Run Command**: Execute commands by clicking 'Run' next to the command name.
        4. **Edit/Delete**: Use the 'Edit' and 'Del' buttons to modify or remove commands and applications.
        5. **View History**: Check the history of command executions using the 'History' button.

        For more information or issues, visit: https://github.com/xrcm/bater
        """
        tk.Label(help_window, text=help_text, justify="left").pack(pady=10, padx=10, anchor="nw")

    def open_about_window(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("400x200")
        about_text = """\
        BATER: Terminal Command Controller

        Description: A modern interface for managing and executing commands efficiently.

        For questions or more details, visit: https://github.com/xrcm/bater
        """
        tk.Label(about_window, text=about_text, justify="left").pack(pady=10, padx=10, anchor="nw")

    def update_home_display(self):
        for widget in self.frame_home_inner.winfo_children():
            widget.destroy()

        column_count = 2
        col_width = self.root.winfo_width() // column_count

        for index, (app_name, app_commands) in enumerate(self.commands.items()):
            if not isinstance(app_commands, dict):
                continue

            app_frame = tk.LabelFrame(self.frame_home_inner, text=app_name, padx=10, pady=10)
            row = index // column_count
            col = index % column_count
            app_frame.place(x=col * col_width, y=row * 250, width=col_width - 20, height=240)

            # Barra de ferramentas para a aplicação
            toolbar_frame = tk.Frame(app_frame)
            toolbar_frame.pack(fill="x")

            add_command_button = tk.Button(app_frame, text="Add Cmd", command=lambda app=app_name: self.open_add_command_window(app))
            add_command_button.pack(pady=5, padx=5)

            for command_id, command_data in app_commands.items():
                if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    continue

                command_name = command_data['name']
                command = command_data['command']

                command_frame = tk.Frame(app_frame)
                command_frame.pack(pady=5, fill="x")

                tk.Label(command_frame, text=command_name).pack(side="left")
                tk.Button(command_frame, text="Run", command=lambda cmd=command: self.run_command(cmd)).pack(side="left", padx=5)
                tk.Button(command_frame, text="History", command=lambda app=app_name, cid=command_id: self.view_history(app, cid)).pack(side="left", padx=5)
                tk.Button(command_frame, text="Edit", command=lambda app=app_name, cid=command_id: self.open_edit_command_window(app, cid)).pack(side="left", padx=5)
                tk.Button(command_frame, text="Del", command=lambda app=app_name, cid=command_id: self.confirm_delete_command(app, cid)).pack(side="left", padx=5)

    def on_frame_home_inner_configure(self, event):
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def run_command(self, command):
        if command.strip():
            try:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                success = process.returncode == 0
                result = stdout.decode().strip() or stderr.decode().strip()

                if success:
                    messagebox.showinfo("Success", result)
                else:
                    messagebox.showerror("Error", result)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showwarning("Warning", "Command is empty.")

    def open_add_command_window(self, app_name):
        command_name = simpledialog.askstring("Command Name", "Enter the name for the command:")
        if command_name:
            if not self.is_valid_command_name(command_name):
                messagebox.showerror("Error", "Command name cannot contain single or double quotes.")
                return

            command = self.open_command_text_window()
            if command:
                if app_name in self.commands:
                    command_id = str(uuid.uuid4())
                    self.commands[app_name][command_id] = {
                        'name': command_name,
                        'command': command,
                        'history': []
                    }
                    self.save_commands()
                    self.update_home_display()
                else:
                    messagebox.showerror("Error", "Application does not exist.")

    def open_command_text_window(self):
        command_var = tk.StringVar()
        dialog_window = tk.Toplevel(self.root)
        dialog_window.title("Enter Command")
        dialog_window.geometry("500x300")

        tk.Label(dialog_window, text="Enter the command:").pack(pady=5)
        command_entry = scrolledtext.ScrolledText(dialog_window, height=10)
        command_entry.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        def on_ok():
            command_var.set(command_entry.get("1.0", tk.END).strip())
            dialog_window.destroy()

        tk.Button(dialog_window, text="OK", command=on_ok).pack(pady=5)
        self.root.wait_window(dialog_window)
        return command_var.get()

    def is_valid_command_name(self, command_name):
        return '"' not in command_name and "'" not in command_name

    def confirm_delete_command(self, app_name, command_id):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this command?"):
            if app_name in self.commands and command_id in self.commands[app_name]:
                del self.commands[app_name][command_id]
                if not self.commands[app_name]:  # Remove the application if it has no commands left
                    del self.commands[app_name]
                self.save_commands()
                self.update_home_display()

    def quit_application(self):
        self.root.quit()

def main():
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
