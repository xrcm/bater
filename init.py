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
        self.root.title("Command Executor")

        # Caminho do arquivo JSON
        self.json_file = 'commands.json'

        # Verifica e carrega dados do arquivo JSON
        self.commands = self.load_commands()

        # Frame para a página inicial
        self.frame_home = tk.Frame(self.root)
        self.frame_home.pack(pady=10)

        # Botão para abrir a janela de adicionar nova aplicação
        self.add_app_button = tk.Button(self.frame_home, text="Add App", command=self.open_add_application_window)
        self.add_app_button.pack(pady=10)
        self.add_tooltip(self.add_app_button, "Add New Application")

        # Atualiza a exibição dos comandos
        self.update_home_display()

    def load_commands(self):
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r') as file:
                    data = json.load(file)
                    if isinstance(data, dict):
                        # Verificar a estrutura de cada aplicação e seus comandos
                        for app_name, commands in data.items():
                            if isinstance(commands, dict):
                                for command_id, command_data in commands.items():
                                    if not isinstance(command_data, dict) or 'name' not in command_data:
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
        # Faz backup do arquivo JSON existente
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_file = f"{self.json_file}_old_{timestamp}.json"
        shutil.copy(self.json_file, backup_file)

        # Cria um novo arquivo JSON vazio
        self.create_new_json_file()

        # Informa o usuário sobre o backup criado
        messagebox.showinfo("Backup Created", f"Backup of the old file created as '{backup_file}'")

    def create_new_json_file(self):
        with open(self.json_file, 'w') as file:
            json.dump({}, file, indent=4)

    def update_home_display(self):
        # Limpa o frame
        for widget in self.frame_home.winfo_children():
            widget.destroy()

        # Botão para adicionar novas aplicações
        self.add_app_button = tk.Button(self.frame_home, text="Add App", command=self.open_add_application_window)
        self.add_app_button.pack(pady=10)
        self.add_tooltip(self.add_app_button, "Add New Application")

        # Exibe aplicações e comandos
        for app_name, app_commands in self.commands.items():
            if not isinstance(app_commands, dict):
                # Se app_commands não for um dicionário, ignora esta aplicação
                continue

            app_frame = tk.LabelFrame(self.frame_home, padx=10, pady=10)
            app_frame.pack(padx=10, pady=5, fill="x")

            # Cabeçalho da aplicação com nome e labels clicáveis
            header_frame = tk.Frame(app_frame)
            header_frame.pack(fill="x")

            # Label do nome da aplicação
            app_label = tk.Label(header_frame, text=app_name, font=('Arial', 12, 'bold'))
            app_label.pack(side="left", padx=5, pady=5)

            # Botões Edit e Del como labels clicáveis
            edit_app_label = tk.Label(header_frame, text="Edit", fg="blue", cursor="hand2", font=('Arial', 10, 'italic'))
            edit_app_label.pack(side="left", padx=5)
            edit_app_label.bind("<Button-1>", lambda e, app=app_name: self.open_edit_application_window(app))
            self.add_tooltip(edit_app_label, "Edit Application")

            delete_app_label = tk.Label(header_frame, text="Del", fg="red", cursor="hand2", font=('Arial', 10, 'italic'))
            delete_app_label.pack(side="left", padx=5)
            delete_app_label.bind("<Button-1>", lambda e, app=app_name: self.confirm_delete_application(app))
            self.add_tooltip(delete_app_label, "Delete Application")

            # Separador entre cabeçalho e lista de comandos
            separator = tk.Frame(app_frame, height=2, bd=1, relief="sunken")
            separator.pack(fill="x", padx=5, pady=5)

            # Botão para adicionar novos comandos
            add_command_button = tk.Button(app_frame, text="Add Cmd", command=lambda app=app_name: self.open_add_command_window(app))
            add_command_button.pack(pady=5)
            self.add_tooltip(add_command_button, "Add New Command")

            # Lista de comandos
            for command_id, command_data in app_commands.items():
                if not isinstance(command_data, dict) or 'command' not in command_data or 'history' not in command_data:
                    # Se o comando não for um dict ou não tiver 'command' e 'history', ignora este comando
                    continue

                command_name = command_data['name']
                command = command_data['command']
                history = command_data['history']

                command_frame = tk.Frame(app_frame)
                command_frame.pack(pady=5, fill="x")

                command_label = tk.Label(command_frame, text=command_name)
                command_label.pack(side="left")

                command_button = tk.Button(command_frame, text="Run", command=lambda cmd=command: self.run_command(cmd, command_frame))
                command_button.pack(side="left", padx=5)
                self.add_tooltip(command_button, "Run Command")

                history_button = tk.Button(command_frame, text="History", command=lambda app=app_name, cid=command_id: self.view_history(app, cid))
                history_button.pack(side="left", padx=5)
                self.add_tooltip(history_button, "View Command History")

                edit_command_label = tk.Label(command_frame, text="Edit", fg="blue", cursor="hand2", font=('Arial', 8, 'italic'))
                edit_command_label.pack(side="left", padx=5)
                edit_command_label.bind("<Button-1>", lambda e, app=app_name, cid=command_id: self.open_edit_command_window(app, cid))
                self.add_tooltip(edit_command_label, "Edit Command")

                delete_command_label = tk.Label(command_frame, text="Del", fg="red", cursor="hand2", font=('Arial', 8, 'italic'))
                delete_command_label.pack(side="left", padx=5)
                delete_command_label.bind("<Button-1>", lambda e, app=app_name, cid=command_id: self.confirm_delete_command(app, cid))
                self.add_tooltip(delete_command_label, "Delete Command")

    def open_add_application_window(self):
        app_name = simpledialog.askstring("Application Name", "Enter new application name:")
        if app_name:
            if app_name.lower() not in map(str.lower, self.commands.keys()):
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
                        'history': []  # Inicializa a lista de histórico vazia
                    }
                    self.save_commands()
                    self.update_home_display()
                else:
                    messagebox.showerror("Error", "Application does not exist.")

    def open_command_text_window(self):
        # Usando uma variável para armazenar o comando digitado
        command_var = tk.StringVar()

        # Criando uma janela de diálogo personalizada
        dialog_window = tk.Toplevel(self.root)
        dialog_window.title("Enter Command")
        dialog_window.geometry("500x300")

        tk.Label(dialog_window, text="Enter the command:").pack(pady=5)
        command_entry = scrolledtext.ScrolledText(dialog_window, height=10)
        command_entry.pack(padx=10, pady=10)

        # Função que será chamada ao clicar no botão "OK"
        def on_ok():
            command_var.set(command_entry.get("1.0", tk.END).strip())
            dialog_window.destroy()

        tk.Button(dialog_window, text="OK", command=on_ok).pack(pady=5)

        # Aguardar até que a janela seja fechada
        self.root.wait_window(dialog_window)

        return command_var.get()

    def is_valid_command_name(self, command_name):
        return '"' not in command_name and "'" not in command_name

    def run_command(self, command, command_frame):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                messagebox.showinfo("Success", f"Command executed successfully:\n{result.stdout}")
            else:
                messagebox.showerror("Error", f"Command failed with error:\n{result.stderr}")

            # Atualizar histórico
            self.update_command_history(command_frame, command, success=result.returncode == 0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to run command: {str(e)}")

    def update_command_history(self, command_frame, command, success=True):
        # Encontrar o comando na estrutura de dados e adicionar o histórico
        for app_name, app_commands in self.commands.items():
            for command_id, command_data in app_commands.items():
                if command_data['command'] == command:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    command_data['history'].append({
                        'timestamp': timestamp,
                        'success': success
                    })

                    # Limitar o histórico a 100 entradas
                    command_data['history'] = command_data['history'][-100:]
                    self.save_commands()

                    return  # Saímos assim que atualizamos o histórico

    def view_history(self, app_name, command_id):
        command_data = self.commands.get(app_name, {}).get(command_id)
        if command_data:
            history_window = tk.Toplevel(self.root)
            history_window.title(f"History for {command_data['name']}")
            history_window.geometry("400x300")

            history_text = scrolledtext.ScrolledText(history_window, wrap=tk.WORD)
            history_text.pack(expand=True, fill="both")

            # Preenche o histórico
            for entry in command_data['history']:
                timestamp = entry['timestamp']
                success = "Success" if entry['success'] else "Failed"
                history_text.insert(tk.END, f"{timestamp}: {success}\n")

            # Botão para executar o comando novamente
            rerun_button = tk.Button(history_window, text="Rerun Command", command=lambda: self.run_command(command_data['command'], None))
            rerun_button.pack(pady=5)

    def open_edit_application_window(self, app_name):
        new_app_name = simpledialog.askstring("Edit Application Name", "Enter new application name:", initialvalue=app_name)
        if new_app_name and new_app_name != app_name:
            if new_app_name.lower() not in map(str.lower, self.commands.keys()):
                self.commands[new_app_name] = self.commands.pop(app_name)
                self.save_commands()
                self.update_home_display()
            else:
                messagebox.showwarning("Warning", "Application with this name already exists.")

    def open_edit_command_window(self, app_name, command_id):
        command_data = self.commands.get(app_name, {}).get(command_id)
        if command_data:
            new_command_name = simpledialog.askstring("Edit Command Name", "Enter new command name:", initialvalue=command_data['name'])
            if new_command_name:
                if not self.is_valid_command_name(new_command_name):
                    messagebox.showerror("Error", "Command name cannot contain single or double quotes.")
                    return

                new_command = self.open_command_text_window()
                if new_command:
                    command_data['name'] = new_command_name
                    command_data['command'] = new_command
                    self.save_commands()
                    self.update_home_display()

    def confirm_delete_application(self, app_name):
        if messagebox.askyesno("Delete Application", f"Are you sure you want to delete the application '{app_name}'?"):
            del self.commands[app_name]
            self.save_commands()
            self.update_home_display()

    def confirm_delete_command(self, app_name, command_id):
        command_data = self.commands.get(app_name, {}).get(command_id)
        if command_data and messagebox.askyesno("Delete Command", f"Are you sure you want to delete the command '{command_data['name']}'?"):
            del self.commands[app_name][command_id]
            self.save_commands()
            self.update_home_display()

    def add_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget, bg="yellow", padx=5, pady=5)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        tooltip_label = tk.Label(tooltip, text=text, bg="yellow")
        tooltip_label.pack()

        def show_tooltip(event):
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)


if __name__ == "__main__":
    root = tk.Tk()
    app = CommandApp(root)
    root.mainloop()
