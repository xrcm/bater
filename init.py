import wx
import wx.lib.scrolledpanel as scrolled
import subprocess
import json
import os
import shutil
from datetime import datetime
import uuid
import threading
import logging
from logging.handlers import RotatingFileHandler
import shlex

# Configure logging with rotation to avoid large log files.
handler = RotatingFileHandler('command_app.log', maxBytes=10000, backupCount=3)
logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_placeholders(command_template):
    """Extract placeholders from a command template."""
    import re
    return re.findall(r'\{(\w+)}', command_template)

def is_dangerous_command(command):
    """Check if a command contains potentially dangerous operations."""
    dangerous_keywords = ['rm', 'shutdown', 'reboot', 'dd', 'mkfs']
    tokens = shlex.split(command)
    for token in tokens:
        if token in dangerous_keywords:
            return True
    return False

class CommandManager:
    """
    Class responsible for managing the storage, loading, and saving of commands in a JSON file.
    """

    def __init__(self, json_file='commands.json'):
        """Initialize the CommandManager with a specified JSON file."""
        self.json_file = json_file
        self.commands = self.load_commands()

    def add_application(self, app_name):
        """Add a new application to the commands list."""
        if app_name.lower() not in [key.lower() for key in self.commands.keys()]:
            self.commands[app_name] = {}
            self.save_commands()
            return True
        return False

    def add_command(self, app_name, command_name, command_text):
        """Add a new command to the specified application."""
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

    def add_command_history(self, app_name, command_id, entry):
        """Add a history entry to a specific command."""
        if app_name in self.commands and command_id in self.commands[app_name]:
            history = self.commands[app_name][command_id]['history']
            history.append(entry)
            if len(history) > 1000:
                history.pop(0)  # Keep only the last 1000 records
            self.save_commands()

    def create_new_json_file(self):
        """Create a new, empty JSON file for storing commands."""
        try:
            with open(self.json_file, 'w') as file:
                json.dump({}, file, indent=4)
        except IOError as e:
            logging.error(f"Error creating new JSON file: {e}")
            wx.MessageBox(f"Failed to create a new JSON file. Details: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def delete_command(self, app_name, command_id):
        """Delete a specific command from an application."""
        if app_name in self.commands and command_id in self.commands[app_name]:
            del self.commands[app_name][command_id]
            if not self.commands[app_name]:  # Remove the application if there are no more commands
                del self.commands[app_name]
            self.save_commands()
            return True
        return False

    def edit_command(self, app_name, command_id, new_name, new_command_text):
        """Edit an existing command's name and text."""
        if app_name in self.commands and command_id in self.commands[app_name]:
            self.commands[app_name][command_id] = {
                'name': new_name,
                'command': new_command_text,
                'history': self.commands[app_name][command_id]['history']
            }
            self.save_commands()
            return True
        return False

    def export_commands(self, export_file):
        """Export all commands to an external JSON file."""
        try:
            with open(export_file, 'w') as file:
                json.dump(self.commands, file, indent=4)
        except IOError as e:
            logging.error(f"Error exporting commands: {e}")
            wx.MessageBox(f"Failed to export commands. Details: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def get_command_history(self, app_name, command_id):
        """Retrieve the history of a specific command."""
        return self.commands.get(app_name, {}).get(command_id, {}).get('history', [])

    def handle_invalid_json(self):
        """Handle invalid JSON data by creating a backup and resetting the JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            backup_file = f"{self.json_file}_old_{timestamp}.json"
            shutil.copy(self.json_file, backup_file)
            self.create_new_json_file()
            wx.MessageBox(f"Backup of the old file created as '{backup_file}'", "Backup Created", wx.OK | wx.ICON_INFORMATION)
        except (shutil.Error, IOError) as e:
            logging.error(f"Error handling invalid JSON: {e}")
            wx.MessageBox(f"Failed to backup and reset JSON file. Details: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def import_commands(self, import_file):
        """Import commands from an external JSON file."""
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
                wx.MessageBox(f"Failed to import commands. Details: {e}", "Error", wx.OK | wx.ICON_ERROR)
        return False

    def load_commands(self):
        """Load commands from the JSON file."""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r') as file:
                    file_content = file.read().strip()
                    if not file_content:
                        return {}
                    data = json.loads(file_content)
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

    def save_commands(self):
        """Save the current state of commands to the JSON file."""
        try:
            with open(self.json_file, 'w') as file:
                json.dump(self.commands, file, indent=4)
        except IOError as e:
            logging.error(f"Error saving commands: {e}")
            wx.MessageBox(f"Failed to save commands. Details: {e}", "Error", wx.OK | wx.ICON_ERROR)

    def validate_commands_data(self, data):
        """Validate the structure of the commands data."""
        for app_name, commands in data.items():
            if not isinstance(commands, dict):
                raise ValueError("Invalid commands format")
            for command_id, command_data in commands.items():
                if not isinstance(command_data, dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    raise ValueError("Invalid command structure.")

class CommandExecutor(threading.Thread):
    """
    Class responsible for executing shell commands in a separate thread to avoid freezing the UI.
    """

    def __init__(self, command, callback):
        """Initialize the thread with a command and a callback function."""
        super().__init__()
        self.command = command
        self.callback = callback

    def run(self):
        """Run the command and return the result to the callback."""
        success, result = self.run_command(self.command)
        wx.CallAfter(self.callback, success, result)

    @staticmethod
    def run_command(command):
        """Static method to execute the command and capture the output."""
        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            success = process.returncode == 0
            result = stdout.decode().strip() or stderr.decode().strip()
            return success, result
        except (subprocess.SubprocessError, OSError) as e:
            logging.error(f"Error running command: {e}")
            return False, f"Failed to execute command. Details: {e}"

class CommandApp(wx.Frame):
    """
    The main application class responsible for the UI and user interaction.
    """

    def __init__(self, parent, title):
        """Initialize the main application window and its components."""
        # Set initial size to 1280x720 if screen resolution is 1920x1080 or higher
        screen_width, screen_height = wx.GetDisplaySize()
        initial_size = (1280, 720) if screen_width >= 1920 and screen_height >= 1080 else (640, 480)
        super(CommandApp, self).__init__(parent, title=title, size=initial_size)

        self.command_manager = CommandManager()

        self.panel = scrolled.ScrolledPanel(self)
        self.panel.SetAutoLayout(1)
        self.panel.SetupScrolling()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.create_menu_bar()
        self.setup_home_frame()
        self.panel.SetSizer(self.sizer)

    def create_menu_bar(self):
        """Create the main menu bar with File, Help, and About menus."""
        menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        add_app = file_menu.Append(wx.ID_ANY, "Add Application")
        file_menu.AppendSeparator()
        help_item = file_menu.Append(wx.ID_ANY, "Help")
        about_item = file_menu.Append(wx.ID_ABOUT, "About")
        file_menu.AppendSeparator()
        exit_app = file_menu.Append(wx.ID_EXIT, "Exit")
        menu_bar.Append(file_menu, "File")

        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.open_add_application_window, add_app)
        self.Bind(wx.EVT_MENU, self.quit_application, exit_app)
        self.Bind(wx.EVT_MENU, self.open_help_window, help_item)
        self.Bind(wx.EVT_MENU, self.open_about_window, about_item)

    def setup_home_frame(self):
        """Set up the main home frame, including the canvas and scrollbars."""
        self.update_home_display()

    def open_add_application_window(self, event=None):
        """Open a dialog to add a new application."""
        dialog = wx.TextEntryDialog(self, "Enter application name:", "Add Application")
        if dialog.ShowModal() == wx.ID_OK:
            app_name = dialog.GetValue()
            if app_name:
                if self.command_manager.add_application(app_name):
                    self.update_home_display()
                else:
                    wx.MessageBox(f"Application '{app_name}' already exists.", "Warning", wx.OK | wx.ICON_WARNING)

    def open_add_command_window(self, app_name):
        """Open a dialog to add a new command to an application."""
        command_name = wx.GetTextFromUser(f"Enter command name for application '{app_name}':", "Add Command")
        if command_name:
            command_text = wx.GetTextFromUser(f"Enter command text for '{command_name}':", "Add Command Text")
            if command_text:
                if self.command_manager.add_command(app_name, command_name, command_text):
                    self.update_home_display()
                else:
                    wx.MessageBox(f"Failed to add command '{command_name}' to application '{app_name}'.", "Warning", wx.OK | wx.ICON_WARNING)

    def edit_application_name(self, app_name):
        """Edit the name of the application."""
        dialog = wx.TextEntryDialog(self, f"Enter new name for the application '{app_name}':", "Edit Application Name")
        if dialog.ShowModal() == wx.ID_OK:
            new_name = dialog.GetValue()
            if new_name and new_name != app_name:
                # Rename the application
                self.command_manager.commands[new_name] = self.command_manager.commands.pop(app_name)
                self.command_manager.save_commands()
                self.update_home_display()

    def delete_application(self, app_name):
        """Delete an entire application and all its commands."""
        if app_name in self.command_manager.commands:
            confirm = wx.MessageBox(f"Are you sure you want to delete '{app_name}'?", "Delete Application", wx.YES_NO | wx.ICON_QUESTION)
            if confirm == wx.YES:
                del self.command_manager.commands[app_name]
                self.command_manager.save_commands()
                self.update_home_display()
        else:
            wx.MessageBox(f"Application '{app_name}' not found.", "Warning", wx.OK | wx.ICON_WARNING)

    def open_edit_command_window(self, app_name, command_id):
        """Open a window to edit an existing command."""
        command_data = self.command_manager.commands.get(app_name, {}).get(command_id, {})
        if not command_data:
            wx.MessageBox("Command not found.", "Warning", wx.OK | wx.ICON_WARNING)
            return

        dialog = wx.Dialog(self, title=f"Edit Command: {command_data['name']}", size=(400, 300))
        vbox = wx.BoxSizer(wx.VERTICAL)

        name_label = wx.StaticText(dialog, label="Command Name:")
        vbox.Add(name_label, 0, wx.ALL | wx.EXPAND, 5)
        name_entry = wx.TextCtrl(dialog, value=command_data['name'])
        vbox.Add(name_entry, 0, wx.ALL | wx.EXPAND, 5)

        command_label = wx.StaticText(dialog, label="Command Text:")
        vbox.Add(command_label, 0, wx.ALL | wx.EXPAND, 5)
        command_entry = wx.TextCtrl(dialog, value=command_data['command'], style=wx.TE_MULTILINE)
        vbox.Add(command_entry, 1, wx.ALL | wx.EXPAND, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_button = wx.Button(dialog, label="Save")
        save_button.Bind(wx.EVT_BUTTON, lambda event: self.save_command_changes(dialog, app_name, command_id, name_entry.GetValue(), command_entry.GetValue()))
        button_sizer.Add(save_button, 0, wx.ALL, 5)

        execute_button = wx.Button(dialog, label="Execute")
        execute_button.Bind(wx.EVT_BUTTON, lambda event: self.execute_command(command_entry.GetValue()))
        button_sizer.Add(execute_button, 0, wx.ALL, 5)

        close_button = wx.Button(dialog, label="Close")
        close_button.Bind(wx.EVT_BUTTON, lambda event: dialog.Destroy())
        button_sizer.Add(close_button, 0, wx.ALL, 5)

        vbox.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        dialog.SetSizer(vbox)
        dialog.ShowModal()

    def save_command_changes(self, dialog, app_name, command_id, new_name, new_command_text):
        """Save the edited command changes."""
        if new_name and new_command_text:
            self.command_manager.edit_command(app_name, command_id, new_name, new_command_text)
            self.update_home_display()
            dialog.Destroy()

    def show_command_history(self, app_name, command_id):
        """Show the history of a specific command in a new window."""
        history = self.command_manager.get_command_history(app_name, command_id)
        if not history:
            wx.MessageBox("No history available for this command.", "History", wx.OK | wx.ICON_INFORMATION)
            return

        dialog = wx.Dialog(self, title=f"History for Command: {self.command_manager.commands[app_name][command_id]['name']}", size=(600, 400))
        vbox = wx.BoxSizer(wx.VERTICAL)

        history_text = wx.TextCtrl(dialog, style=wx.TE_MULTILINE | wx.TE_READONLY)
        for entry in history[-1000:]:
            if isinstance(entry, dict):
                # Handle case where history is stored as a dictionary
                timestamp = entry.get('timestamp', 'Unknown time')
                result = entry.get('result', 'No result')
                history_text.AppendText(f"Executed on: {timestamp}\nResult: {result}\n\n")
            else:
                # Handle case where history is stored as a string
                history_text.AppendText(f"Executed command result: {entry}\n\n")

        vbox.Add(history_text, 1, wx.ALL | wx.EXPAND, 10)
        close_button = wx.Button(dialog, label="Close")
        close_button.Bind(wx.EVT_BUTTON, lambda event: dialog.Destroy())
        vbox.Add(close_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        dialog.SetSizer(vbox)
        dialog.ShowModal()

    def execute_command(self, command):
        """Execute a command, with a warning if it's potentially dangerous."""
        if is_dangerous_command(command):
            wx.MessageBox("This command may be dangerous. Please confirm its safety.", "Dangerous Command", wx.OK | wx.ICON_WARNING)
            return

        def on_command_finished(success, result):
            if success:
                wx.MessageBox(result, "Command Output", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox(result, "Command Error", wx.OK | wx.ICON_ERROR)

        CommandExecutor(command, on_command_finished).start()

    def delete_command(self, app_name, command_id):
        """Delete a specific command from an application."""
        if self.command_manager.delete_command(app_name, command_id):
            self.update_home_display()
        else:
            wx.MessageBox("Failed to delete command.", "Warning", wx.OK | wx.ICON_WARNING)

    def open_about_window(self, event):
        """Open the About window with application details."""
        about_text = (
            "BATER: Terminal Command Controller\n"
            "Version 1.0\n"
            "Developed by Rafael Martins\n"
            "© 2024"
        )
        wx.MessageBox(about_text, "About", wx.OK | wx.ICON_INFORMATION)

    def open_help_window(self, event):
        """Open the Help window with usage instructions."""
        help_text = (
            "Help:\n\n"
            "1. **Add Application**: Use 'File > Add Application' to add a new application.\n\n"
            "2. **Add Command**: Click 'Add Cmd' under an application's frame to add a new command.\n\n"
            "3. **Edit Command**: Use the 'Edit' button next to a command to modify it.\n\n"
            "4. **Delete Command**: Use the 'Delete' button to remove a command.\n\n"
            "5. **Run Command**: Click 'Run' to execute a command.\n\n"
            "6. **View History**: Click 'History' next to a command to see its past executions.\n\n"
            "7. **Edit Application**: Use the 'Edit' button to modify the name of an application.\n\n"
            "8. **Delete Application**: Use the 'Delete' button to remove an entire application and its commands.\n\n"
            "9. **Exit**: Use 'File > Exit' to quit the application.\n\n"
            "For further assistance, refer to the documentation or contact support."
        )
        wx.MessageBox(help_text, "Help", wx.OK | wx.ICON_INFORMATION)

    def quit_application(self, event):
        """Quit the application."""
        self.Close()

    def update_home_display(self):
        """Update the home display dynamically based on the window size."""
        self.sizer.Clear(True)
        num_columns = 2
        column_width = 300  # Minimum width for each column (adjustable)

        row = 0
        col = 0
        flex_sizer = wx.FlexGridSizer(cols=num_columns, hgap=10, vgap=10)
        flex_sizer.AddGrowableCol(0, 1)
        flex_sizer.AddGrowableCol(1, 1)

        for app_name, app_commands in self.command_manager.commands.items():
            if not isinstance(app_commands, dict):
                continue

            # Create a StaticBox for each application
            app_box = wx.StaticBox(self.panel, label=app_name)
            app_sizer = wx.StaticBoxSizer(app_box, wx.VERTICAL)

            # Create the command entries under the app section
            for command_id, command_data in app_commands.items():
                if not isinstance(command_data,
                                  dict) or 'name' not in command_data or 'command' not in command_data or 'history' not in command_data:
                    continue

                command_name = command_data['name']
                command = command_data['command']

                command_panel = wx.Panel(self.panel)
                command_sizer = wx.BoxSizer(wx.HORIZONTAL)

                command_label = wx.StaticText(command_panel, label=command_name)
                command_sizer.Add(command_label, 1, wx.ALL | wx.EXPAND, 5)

                run_button = wx.Button(command_panel, label="Run")
                run_button.Bind(wx.EVT_BUTTON, lambda event, cmd=command: self.execute_command(cmd))
                command_sizer.Add(run_button, 0, wx.ALL, 5)

                edit_button = wx.Button(command_panel, label="Edit")
                edit_button.Bind(wx.EVT_BUTTON,
                                 lambda event, cmd_id=command_id, app=app_name: self.open_edit_command_window(app,
                                                                                                              cmd_id))
                command_sizer.Add(edit_button, 0, wx.ALL, 5)

                history_button = wx.Button(command_panel, label="History")
                history_button.Bind(wx.EVT_BUTTON,
                                    lambda event, cmd_id=command_id, app=app_name: self.show_command_history(app,
                                                                                                             cmd_id))
                if not self.command_manager.get_command_history(app_name, command_id):
                    history_button.Disable()
                command_sizer.Add(history_button, 0, wx.ALL, 5)

                delete_button = wx.Button(command_panel, label="Delete")
                delete_button.Bind(wx.EVT_BUTTON,
                                   lambda event, cmd_id=command_id, app=app_name: self.delete_command(app, cmd_id))
                command_sizer.Add(delete_button, 0, wx.ALL, 5)

                command_panel.SetSizer(command_sizer)
                app_sizer.Add(command_panel, 0, wx.ALL | wx.EXPAND, 5)

            # Clickable labels for "Add Cmd", "Edit", and "Del" at the bottom-right of the app block
            label_panel = wx.Panel(self.panel)
            label_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # "Add Cmd" label, green, aligned to the left
            add_cmd_label = wx.StaticText(label_panel, label="Add Cmd")
            add_cmd_label.SetForegroundColour(wx.Colour(0, 128, 0))  # Green color
            add_cmd_label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            add_cmd_label.Bind(wx.EVT_LEFT_DOWN, lambda event, app=app_name: self.open_add_command_window(app))
            label_sizer.Add(add_cmd_label, 0, wx.ALL | wx.ALIGN_LEFT, 5)

            # Spacer to push the "Edit" and "Del" labels to the right
            label_sizer.AddStretchSpacer(1)

            # "Edit" label, default color
            edit_label = wx.StaticText(label_panel, label="Edit")
            edit_label.SetForegroundColour(wx.BLUE)
            edit_label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            edit_label.Bind(wx.EVT_LEFT_DOWN, lambda event, app=app_name: self.edit_application_name(app))
            label_sizer.Add(edit_label, 0, wx.ALL, 5)

            # "Del" label, red
            del_label = wx.StaticText(label_panel, label="Del")
            del_label.SetForegroundColour(wx.RED)  # Red color
            del_label.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            del_label.Bind(wx.EVT_LEFT_DOWN, lambda event, app=app_name: self.delete_application(app))
            label_sizer.Add(del_label, 0, wx.ALL, 5)

            label_panel.SetSizer(label_sizer)
            app_sizer.Add(label_panel, 0, wx.ALL | wx.EXPAND, 5)

            flex_sizer.Add(app_sizer, 1, wx.ALL | wx.EXPAND, 10)
            col += 1
            if col >= num_columns:
                col = 0
                row += 1

        self.sizer.Add(flex_sizer, 1, wx.EXPAND | wx.ALL, 10)
        self.panel.SetupScrolling(scrollToTop=False)
        self.Layout()


if __name__ == "__main__":
    app = wx.App(False)
    frame = CommandApp(None, "BATER: Terminal Command Controller")
    frame.Show(True)
    app.MainLoop()
