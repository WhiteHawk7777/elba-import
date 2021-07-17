import glob
import os
import shutil
import re
import tkinter as tk
import tkinter.messagebox
from datetime import date
from os import rename
from pathlib import Path
from tkinter import filedialog

font_size = 15


def match_iban(search_str: str):
    m = re.search("AT[0-9]+", search_str)

    if m is None:
        return None

    return m.group(0)


def change_font_size(increase, root, frame):
    global font_size
    if increase:
        font_size += 1
    else:
        if font_size < 10:
            tkinter.messagebox.showerror(title="Fehler", message="Schriftgröße kann nicht weiter reduziert werden.")
            return
        font_size -= 1

    frame.destroy()

    # root.iconbitmap("example/path/file.ico")
    root.option_add("*Font", ('Arial', font_size))

    MainWindow(root)


class MainWindow:
    def __init__(self, master):
        self.log_messages = ""
        self.error_messages = ""
        self.folder_path = ""
        self.target_folder_path = ""

        self.master = master

        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.frame = tk.Frame(self.master)
        self.frame.grid(row=0, column=0, padx=50, pady=50, sticky="NSEW")

        self.frame.columnconfigure((0, 1, 2, 3), weight=1)
        self.frame.rowconfigure((0, 1, 2, 3, 4), weight=1)

        # directory input field
        self.dLabel = tk.Label(self.frame, text="Verzeichnis:  ").grid(column=0, row=0, sticky="NSEW")
        self.directoryEntry = tk.Entry(self.frame, width=80)
        self.directoryEntry.grid(column=1, row=0, sticky="")
        self.dirSelectButton = tk.Button(self.frame, text="...", command=self.select_directory)
        self.dirSelectButton.grid(column=2, row=0, sticky="")

        # output directory input field for move mode
        self.move_directory_label = tk.Label(self.frame, text="Zielverzeichnis:  ").grid(column=0, row=1, sticky="")
        self.move_directory_entry = tk.Entry(self.frame, width=80)
        self.move_directory_entry.grid(column=1, row=1, sticky="")
        self.move_dir_select_button = tk.Button(self.frame, text="...", command=self.select_move_directory)
        self.move_dir_select_button.grid(column=2, row=1, sticky="")

        # checkbox for rename mode
        self.rename_var = tk.IntVar(self.master)
        self.rename_var.set(0)
        self.rename_box = tk.Checkbutton(self.frame, text="Umbenennen", variable=self.rename_var, command=self.rename_button_action)
        self.rename_box.grid(column=0, row=2, sticky="")

        # checkbox for move mode
        self.move_var = tk.IntVar(self.master)
        self.move_var.set(1)
        self.move_box = tk.Checkbutton(self.frame, text="Kopieren", variable=self.move_var, command=self.move_button_action)
        self.move_box.grid(column=1, row=2, sticky="")

        self.move_button_action()

        # confirm button
        self.confirm = tk.Button(self.frame, text="Bestätigen", command=self.submit)
        self.confirm.grid(column=1, row=3, sticky="NSEW")

        # close button
        self.close = tk.Button(self.frame, text="Schließen", command=self.master.destroy)
        self.close.grid(column=2, row=3, sticky="")

        # increase font size
        self.increase_size_button = tk.Button(self.frame, text="+", command=lambda: change_font_size(True, self.master, self.frame))
        self.increase_size_button.grid(column=2, row=4, sticky="NSEW", padx=50, pady=10)

        # reduce font size
        self.reduce_size_button = tk.Button(self.frame, text="-", command=lambda: change_font_size(False, self.master, self.frame))
        self.reduce_size_button.grid(column=1, row=4, sticky="NSEW", padx=50, pady=10)

    def rename_button_action(self):
        self.move_var.set(0)

        self.rename_box.config(state="disabled")
        self.move_box.config(state="normal")

        self.move_directory_entry.config(state="disabled")
        self.move_dir_select_button.config(state="disabled")

        self.master.update()

    def move_button_action(self):
        self.rename_var.set(0)

        self.rename_box.config(state="normal")
        self.move_box.config(state="disabled")

        self.move_directory_entry.config(state="normal")
        self.move_dir_select_button.config(state="normal")

        self.master.update()

    def select_directory(self):
        self.folder_path = filedialog.askdirectory()
        self.directoryEntry.delete(0, "end")
        self.directoryEntry.insert(0, self.folder_path)

    def select_move_directory(self):
        self.target_folder_path = filedialog.askdirectory()
        self.move_directory_entry.delete(0, "end")
        self.move_directory_entry.insert(0, self.target_folder_path)

    def show_result_window(self):
        self.log_messages = self.log_messages.replace("/", "\\")
        self.error_messages = self.error_messages.replace("/", "\\")

        result_window = tk.Tk()
        result_window.option_add("*Font", ('Arial', font_size))
        ResultWindow(result_window, self.log_messages, self.error_messages)

        self.master.destroy()

        result_window.mainloop()

    def submit(self):
        if self.folder_path == "" or self.folder_path is None:
            tkinter.messagebox.showerror(title="Fehler", message="Verzeichnis kann nicht leer sein.")
            return

        if self.rename_var.get() == 1:

            self.iterate_rename_files(".pdf")
            self.iterate_rename_files(".xml")

        else:
            if self.target_folder_path == "" or self.target_folder_path is None:
                tkinter.messagebox.showerror(title="Fehler", message="Zielverzeichnis kann nicht leer sein.")
                return

            self.copy_files()

        self.show_result_window()

    def iterate_rename_files(self, file_ending: str):

        all_files = glob.glob(self.folder_path + "/*" + file_ending)

        if not all_files:
            self.error_messages += "No files with the ending " + file_ending + " found in the selected folder.\n"

        for file_ in all_files:
            self.rename_file(file_, file_ending)

    def rename_file(self, file_name: str, file_ending: str):
        today = date.today()
        datestamp = today.strftime("%Y%m%d")
        file_name = re.sub(pattern=".*\\\\", repl="", string=file_name)

        iban = match_iban(file_name)

        if iban is None:
            self.error_messages += "Die Datei '" + file_name + "' enthält keinen IBAN und wird nicht umbenannt.\n"

        else:
            new_name = iban + "_" + datestamp + file_ending
            try:
                rename(self.folder_path + "/" + file_name, self.folder_path + "/" + new_name)
                self.log_messages += "Die Datei '" + file_name + "' wurde in '" + new_name + "' umbenannt.\n"
            except FileExistsError:
                self.error_messages += "Die Datei '" + self.folder_path + "\\" + file_name + "' kann nicht umbenannt werden. Der resultierende Dateiname existiert bereits.\n"

    def copy_files(self):
        all_files = glob.glob(self.folder_path + "/*.pdf")

        for file in all_files:
            iban = match_iban(file)
            if iban is None:
                self.error_messages += str(file) + " wurde übersprungen.\n"
                continue
            else:
                folder_name = self.target_folder_path + "/" + iban
                if not Path(folder_name).is_dir():
                    os.mkdir(folder_name)
                shutil.copy2(file, folder_name)
                self.log_messages += str(file) + " wurde kopiert nach " + folder_name + "\n"


class ResultWindow:
    def __init__(self, master, log_messages, error_messages):
        # window definitions
        self.master = master
        self.res = tk.Frame(self.master)
        self.master.title("Nachrichten")
        self.res.pack()

        # label for error entry
        self.error_label = tk.Label(self.master, text="Fehler")
        self.error_label.pack()

        # entry to show errors and warnings
        self.error_text = tk.Text(self.master, width=200, height=10)
        self.error_text.pack()
        self.error_text.insert("end", error_messages)
        # read-only
        self.error_text.bind("<Key>", lambda e: "break")

        # label for log entry
        self.log_label = tk.Label(self.master, text="Log")
        self.log_label.pack()

        # entry to show logs
        self.log_text = tk.Text(self.master, width=200, height=10)
        self.log_text.pack()
        self.log_text.insert("end", log_messages)
        # read-only
        self.log_text.bind("<Key>", lambda e: "break")

        # close button
        self.close = tk.Button(self.master, text="Schließen", command=self.master.destroy)
        self.close.pack()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("File Renamer")

    # root.iconbitmap("example/path/file.ico")
    root.option_add("*Font", ('Arial', font_size))

    main_page = MainWindow(root)

    root.mainloop()
