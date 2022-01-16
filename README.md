# Simple keepassxc proxy interface

Simple commandline interface to KeePassXC. Query by key or
select with [rofi](https://github.com/davatorium/rofi). Output
KeePassXC entry as JSON, key value pair, directly to clipboard,
simulate key events or show a GUI.

## Warning
Currently needs a not upstream proxy command in KeePassXC and
`keepassxc_proxy_client`

- https://github.com/irq0/keepassxc-proxy-client/tree/wip/get-database-entries
- https://github.com/irq0/keepassxc/tree/wip/get-database-entries_request

## Dependencies
 - [rofi](https://github.com/davatorium/rofi)
 - `xdotool`
 - `xclip`
 - See `requirements.txt`
