#!/usr/bin/env python3
import base64
import json
import pathlib
import subprocess

import click
import keepassxc_proxy_client.protocol
import xdg.BaseDirectory

import gui

ASSOCIATE_FILENAME = (
    pathlib.Path(xdg.BaseDirectory.xdg_config_home) / "pwman" / "associate.json"
)


def find_entry(search_string, entries):
    for entry in entries:
        if search_string in (entry["title"], entry["url"]):
            return entry
    raise ValueError("No such entry: " + search_string)


def load_associate():
    try:
        with open(ASSOCIATE_FILENAME) as fd:
            j = json.loads(fd.read())
            j["public_key"] = base64.b64decode(j["public_key"])
            return j
    except FileNotFoundError:
        return None


def save_associate(data):
    ASSOCIATE_FILENAME.parent.mkdir(parents=True, exist_ok=True)
    with open(ASSOCIATE_FILENAME, "w") as fd:
        encoded = json.dumps(
            {"name": data[0], "public_key": base64.b64encode(data[1]).decode("ASCII")}
        )
        fd.write(encoded)


def keepassxc_connect():
    connection = keepassxc_proxy_client.protocol.Connection()
    connection.connect()
    asscociate = load_associate()
    if asscociate:
        connection.load_associate(**asscociate)
    else:
        connection.associate()
        save_associate(connection.dump_associate())
    connection.test_associate()
    return connection


def rofi(keys):
    result = subprocess.run(
        ["rofi", "-dmenu", "-i", "-sort", "-p", "Service: "],
        capture_output=True,
        input="\n".join(keys).encode("UTF-8"),
    )
    return result.stdout.decode("UTF-8").strip()


@click.command()
@click.argument("key", nargs=1, required=False)
@click.option("--clipboard", "mode", flag_value="clipboard")
@click.option("--type", "mode", flag_value="type")
@click.option("--print", "mode", flag_value="print")
@click.option("--gui", "mode", flag_value="gui", default=True)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "plain", "password"], case_sensitive=False),
    default="plain",
)
def pwman(key, mode, output_format):
    "Simple password manager interface"
    connection = keepassxc_connect()
    all_entries = connection.get_database_entries()["entries"]
    if not key:
        key = rofi(e["title"] for e in all_entries)
    index_entry = find_entry(key, all_entries)
    entry = next(
        iter(connection.get_logins("keepassxc://by-uuid/" + index_entry["uuid"]))
    )
    if index_entry["title"]:
        entry["title"] = index_entry["title"]
    if index_entry["url"]:
        entry["url"] = index_entry["url"]

    if mode == "clipboard":
        gui.clipboard_set(entry["password"])
    elif mode == "type":
        subprocess.run(["xdotool", "type", "--delay", "100", entry["password"]])
    elif mode == "print":
        if output_format == "json":
            print(json.dumps(entry))
        elif output_format == "password":
            print(entry["password"])
        else:
            print(entry["login"] + ":" + entry["password"])
    elif mode == "gui":
        gui.show(entry)


if __name__ == "__main__":
    pwman()
