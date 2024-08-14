import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext
import subprocess
import json
import os
import shutil
from datetime import datetime
import uuid

class CommandApp:
    def __init__(self, root):
        self.root = root
        self.root.title("bater")
        self.root.minsize(640, 400)

        # Caminho do arquivo JSON
        self.json_file = 'commands.json'

        # Verifica e carrega dados do arquivo JSON
        self.commands = self.load_commands()

        # Cria a barra de menu
        self.create_menu()

        # Frame para a página inicial
        self.frame_home = tk.Frame(self.root)
        self.frame_home.pack(pady=10, fill=tk.BOTH, expand=True)

        # Botão "Sair" fixo no canto inferior direito
        self.quit_button = tk.Button(self.root, text="Sair", command=self.quit_application)
        self.quit_button.pack(side=tk.RIGHT, padx=10, pady=10, anchor=tk.SE)

        # Atualiza a exibição dos comandos
        self.update_home_display()

    def load_commands(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        for app_name, commands in data.items():
                            if isinstance(commands, dict):
                                for command_id, command_data in commands.items():
                                    if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                                        print(f"Invalid command data in app '{app_name}': {command_data}")
                                        raise ValueError("Invalid command structure.")
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

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Application", command=self.open_add_application_window)

    def update_home_display(self):
        for widget in self.frame_home.winfo_children():
            widget.destroy()

        for app_name, app_commands in self.commands.items():
            if not isinstance(app_commands, dict):
                continue

            app_frame = tk.LabelFrame(self.frame_home, padx=10, pady=10)
            app_frame.pack(padx=10, pady=5, fill="x")

            # Barra de ferramentas para a aplicação
            toolbar_frame = tk.Frame(app_frame)
            toolbar_frame.pack(fill="x")

            app_label = tk.Label(toolbar_frame, text=app_name, font=('Arial', 12, 'bold'))
            app_label.pack(side="left", padx=5, pady=5)

            edit_button = tk.Button(toolbar_frame, text="Edit", command=lambda app=app_name: self.open_edit_application_window(app))
            edit_button.pack(side="left", padx=5)
            self.add_tooltip(edit_button, "Edit Application")

            delete_button = tk.Button(toolbar_frame, text="Del", command=lambda app=app_name: self.confirm_delete_application(app))
            delete_button.pack(side="left", padx=5)
            self.add_tooltip(delete_button, "Delete Application")

            separator = tk.Frame(app_frame, height=2, bd=1, relief="sunken")
            separator.pack(fill="x", padx=5, pady=5)

            add_command_button = tk.Button(app_frame, text="Add Cmd", command=lambda app=app_name: self.open_add_command_window(app))
            add_command_button.pack(pady=5)
            self.add_tooltip(add_command_button, "Add New Command")

            for command_id, command_data in app_commands.items():
                if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    continue

                command_name = command_data['name']
                command = command_data['command']

                command_frame = tk.Frame(app_frame)
                command_frame.pack(pady=5, fill="x")

                command_label = tk.Label(command_frame, text=command_name)
                command_label.pack(side="left")

                command_button = tk.Button(command_frame, text="Run", command=lambda cmd=command, frame=command_frame: self.run_command(cmd, frame))
                command_button.pack(side="left", padx=5)
                self.add_tooltip(command_button, "Run Command")

                history_button = tk.Button(command_frame, text="History", command=lambda app=app_name, cid=command_id: self.view_history(app, cid))
                history_button.pack(side="left", padx=5)
                self.add_tooltip(history_button, "View Command History")

                edit_command_button = tk.Button(command_frame, text="Edit", command=lambda app=app_name, cid=command_id: self.open_edit_command_window(app, cid))
                edit_command_button.pack(side="left", padx=5)
                self.add_tooltip(edit_command_button, "Edit Command")

                delete_command_button = tk.Button(command_frame, text="Del", command=lambda app=app_name, cid=command_id: self.confirm_delete_command(app, cid))
                delete_command_button.pack(side="left", padx=5)
                self.add_tooltip(delete_command_button, "Delete Command")

    def open_add_application_window(self):
        app_name = simpledialog.askstring("Application Name", "Enter new application name:")
        if app_name:
            if app_name.lower() not in [key.lower() for key in self.commands.keys()]:
                self.commands[app_name] = {}
                self.save_commands()
                self.update_home_display()
            else:
                messagebox.showwarning("Warning", "Application already exists.")

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
        command_entry.pack(padx=10, pady=10)

        def on_ok():
            command_var.set(command_entry.get("1.0", tk.END).strip())
            dialog_window.destroy()

        tk.Button(dialog_window, text="OK", command=on_ok).pack(pady=5)
        self.root.wait_window(dialog_window)
        return command_var.get()

    def is_valid_command_name(self, command_name):
        return '"' not in command_name and "'" not in command_name

    def run_command(self, command, frame):
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

                self.update_command_history(frame, success)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showwarning("Warning", "Command is empty.")

    def update_command_history(self, frame, success):
        # Implementar a atualização do histórico do comando
        pass

    def open_edit_application_window(self, app_name):
        new_app_name = simpledialog.askstring("Edit Application", "Enter new application name:", initialvalue=app_name)
        if new_app_name:
            if new_app_name.lower() not in [key.lower() for key in self.commands.keys()] or new_app_name.lower() == app_name.lower():
                self.commands[new_app_name] = self.commands.pop(app_name)
                self.save_commands()
                self.update_home_display()
            else:
                messagebox.showwarning("Warning", "Application with this name already exists.")

    def open_edit_command_window(self, app_name, command_id):
        command_data = self.commands.get(app_name, {}).get(command_id, {})
        if command_data:
            new_command_name = simpledialog.askstring("Edit Command", "Enter new command name:", initialvalue=command_data['name'])
            new_command = self.open_command_text_window() if new_command_name else command_data['command']

            if new_command_name and new_command:
                if not self.is_valid_command_name(new_command_name):
                    messagebox.showerror("Error", "Command name cannot contain single or double quotes.")
                    return

                self.commands[app_name][command_id] = {
                    'name': new_command_name,
                    'command': new_command,
                    'history': command_data['history']
                }
                self.save_commands()
                self.update_home_display()

    def confirm_delete_application(self, app_name):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the application '{app_name}'?"):
            del self.commands[app_name]
            self.save_commands()
            self.update_home_display()

    def confirm_delete_command(self, app_name, command_id):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this command?"):
            if app_name in self.commands and command_id in self.commands[app_name]:
                del self.commands[app_name][command_id]
                if not self.commands[app_name]:  # Remove the application if it has no commands left
                    del self.commands[app_name]
                self.save_commands()
                self.update_home_display()

    def add_tooltip(self, widget, text):
        tooltip = tk.Label(self.root, text=text, bg="yellow", relief="solid", padx=5, pady=2)
        tooltip.pack_forget()

        def on_enter(event):
            x = event.x_root - self.root.winfo_rootx() + 10
            y = event.y_root - self.root.winfo_rooty() + 10
            tooltip.place(x=x, y=y)

        def on_leave(event):
            tooltip.place_forget()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def quit_application(self):
        self.root.quit()

def main():
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
