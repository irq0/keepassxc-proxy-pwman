#!/usr/bin/env python3
import datetime
import json
import os.path
import re
import subprocess
import sys
import tkinter
from tkinter import Button
from tkinter import E
from tkinter import Entry
from tkinter import Label
from tkinter import mainloop
from tkinter import N
from tkinter import S
from tkinter import StringVar
from tkinter import Text
from tkinter import Tk
from tkinter import W

import dbus


def plumb_string(s):
    bus = dbus.SessionBus()
    plumber = bus.get_object("org.irq0.cathica", "/org/irq0/cathica/Plumb")
    plumber.string(s)


def clipboard_set(s):
    subprocess.run(["xclip", "-in", "-selection", "primary"], input=s.encode("UTF-8"))
    subprocess.run(["xclip", "-in", "-selection", "clipboard"], input=s.encode("UTF-8"))


def notify(title, body):
    bus = dbus.SessionBus()
    notif = bus.get_object(
        "org.freedesktop.Notifications", "/org/freedesktop/Notifications"
    )
    notify = dbus.Interface(notif, "org.freedesktop.Notifications")
    notify.Notify("pwman", 0, "", "[pwman] " + title, body, "", "", 5000)


class PwmanGui:
    def __init__(self, root):
        root.title("pwman")

        root.bind("<Escape>", lambda _: root.destroy())

        root.wm_attributes("-topmost", 1)
        root.wm_attributes("-type", "dialog")
        root.lift()

        root.columnconfigure(0, weight=2)
        root.columnconfigure(1, weight=3)
        root.columnconfigure(2, weight=1)
        root.columnconfigure(3, weight=1)

        root.rowconfigure(0, weight=1)

        self.widget_fn = [
            (re.compile(r"(iconname|resource_uri|id)"), None),
            (re.compile(r"(url|username|created|modified)"), self.add_plumbable_widget),
            (re.compile(r"^ssh_key$"), self.add_save_to_file_widget),
            (re.compile(r"(password)"), self.add_password_widget),
            (re.compile(r".*"), self.add_default_widget),
        ]
        self.root = root
        self.current_row = 2

    def copy_x_to_clipboard(self, x):
        def copy_to_clipboard():
            clipboard_set(x)

        return copy_to_clipboard

    def plumb_x(self, x):
        return lambda: plumb_string(x)

    def add_password_widget(self, key, passwd, data):
        row_num = self.current_row
        self.root.rowconfigure(row_num, weight=2)

        label = Label(self.root, text=key)
        label.grid(row=row_num, column=0, sticky=N + E + S + W)

        v_password = StringVar()
        v_password.set("*" * len(passwd))
        entry = Entry(self.root, textvariable=v_password, width=42)
        entry.grid(row=row_num, column=1)

        b = Button(self.root, text="Copy", command=self.copy_x_to_clipboard(passwd))
        b.grid(row=row_num, column=2)

        v_password.revealed = False

        def cmd_reveal_toggle():
            if v_password.revealed:
                v_password.set("*" * len(passwd))
            else:
                v_password.set(passwd)

            v_password.revealed = not v_password.revealed

        b = Button(self.root, text="Reveal", command=cmd_reveal_toggle)
        b.grid(row=row_num, column=3)

        self.current_row += 1

    def determine_filename(self, key, data):
        if key == "ssh_key":
            return data["ssh_key_name"]
        else:
            return re.sub(r"[^\w]", "_", data["title"])

    def add_save_to_file_widget(self, key, passwd, data):
        row_num = self.current_row
        self.root.rowconfigure(row_num, weight=2)

        label = Label(self.root, text=key)
        label.grid(row=row_num, column=0, sticky=N + E + S + W)

        v_password = StringVar()
        v_password.set("_" * len(passwd))
        entry = Entry(self.root, textvariable=v_password, width=42)
        entry.grid(row=row_num, column=1)

        b = Button(self.root, text="Copy", command=self.copy_x_to_clipboard(passwd))
        b.grid(row=row_num, column=2)

        def cmd_save():
            filename = (
                self.determine_filename(key, data)
                + "_"
                + datetime.datetime.now().replace(microsecond=0).isoformat()
            )

            p = os.path.expanduser("~/tmp/" + filename)
            with open(p, "w") as fd:
                fd.write(passwd)

            notify("Saved to " + filename, p)

        b = Button(self.root, text="Save", command=cmd_save)
        b.grid(row=row_num, column=3)

        self.current_row += 1

    def add_default_widget(self, key, value, data):
        row_num = self.current_row
        self.root.rowconfigure(row_num, weight=2)

        label = Label(self.root, text=key)
        label.grid(row=row_num, column=0, sticky=N + E + S + W)

        if isinstance(value, str) and "\n" in value:
            txt = Text(self.root, height=value.count("\n"), width=48)
            txt.grid(row=row_num, column=1)
            txt.insert(tkinter.END, value.replace("\r", ""))
        else:
            v_value = StringVar()
            v_value.set(value)
            e = Entry(self.root, textvariable=v_value, width=42)
            e.grid(row=row_num, column=1)

        b = Button(self.root, text="Copy", command=self.copy_x_to_clipboard(value))
        b.grid(row=row_num, column=2)
        self.current_row += 1

    def add_plumbable_widget(self, key, value, data):
        row_num = self.current_row
        self.root.rowconfigure(row_num, weight=2)
        label = Label(self.root, text=key)
        label.grid(row=row_num, column=0)

        v_value = StringVar()
        v_value.set(value)
        e = Entry(self.root, textvariable=v_value, width=42)
        e.grid(row=row_num, column=1)

        b = Button(self.root, text="Copy", command=self.copy_x_to_clipboard(value))
        b.grid(row=row_num, column=2)

        b = Button(self.root, text="Plumb", command=self.plumb_x(value))
        b.grid(row=row_num, column=3)
        self.current_row += 1

    def create_widgets(self, data):
        label = Label(self.root, text=data["title"])
        label.grid(row=0, column=0, columnspan=3, sticky=tkinter.W)

        for k, v in data.items():
            if v:
                for k_re, fn in self.widget_fn:
                    if k_re.search(k):
                        if fn:
                            fn(k, v, data)
                        break

        b = Button(self.root, text="Quit", command=lambda: sys.exit())
        b.grid(row=self.current_row, column=3)
        self.root.rowconfigure(self.current_row, weight=1)


def show(args):
    root = Tk()
    gui = PwmanGui(root)
    gui.create_widgets(args)
    mainloop()


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    show(args)
