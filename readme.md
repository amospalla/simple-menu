# simple-menu

## Description

This program allows composable menu and menu item generation from user scripts, by using
a simple text format.

It works around the _item_ attributes, which are:

- its _menu entry text_.
- its _action_, when selected.

Simple-menu provides several item types. Their _menu entry text_ and _action_ are
defined by the chosen item _type_, and the user defined _value_ (a string). Some items
execute commands on selection and other items show a menu when selected.

Menus are built by specyfing items, specifying pairs of _type_ and _value_. This
can be done by either:

- specifying pairs of `--type` and `--value` arguments on the command line.
- specifying an item _type_ that instead of using its _value_ to define
  _menu_entry_text_/_action_, delegates their definition to an external command.

There are examples on the _examples_ folder.

## Usage

Menu keys:

- Escape: go back one menu.
- Enter: select item.
- Control+r: refresh menu.
- Control+q: quit menu.

Environment variables:

- RAW: if set (to any value) do not substitute icons.
- INTERFACE: use it to override interface ("auto", "fzf" or "rofi").

### Global parameters

- `--config-file`: path to configuration file. Defaults to
  ~/.config/simple-menu/simple-menu.toml or /etc/simple-menu/simple-menu.toml, whatever
  is find first.
- `--interface`: choices are _fzf_, _rofi_ or _auto_. Defaults to auto. Auto selects
  rofi or fzf depending on wether WAYLAND_DISPLAY or DISPLAY environment variables are
  set.
- `--token-separator`: specify the token separators, use multiple times to set nested
  tokens.
- `--verbose`: increase logging levels, can be used twice to increase the verbosity.

### Menu mode

In menu mode a menu is built and shown to the user by specifying its items.

Parameters:

- `--title`: title to show on the menu.
  - Menu can run in loop until a user presses `Esc` or `Enter` (first time Enter is
    pressed the item is not executed). Use this mode to show data in real-time.
- `--run-once`: do not wait for user to explicitly quit the menu, exit after first
  selection.
- `--loop <float>`: run the menu continuously until the user makes a selection or
  explicitly exits the menu; then run the menu one more time. Note that when running in
  loop selecting an item does not execute it, only makes the loop stop.
- `--type/--value`: pairs of item type and item value to show on the menu.

Example:

```bash
simple-menu menu --title "My Menu" \
    --type item --value "action :: :: :: :: launch terminal::xterm" \
    --type item --value "action :: :: :: :: say hi::notify-send::hi"
```

### Item mode

The item mode executes an item directly.

The program expects a single item to be specified, that is, a single `--type`/`--value`
pair.

Because the item is directly executed there is no need to specify the five _menu entry
text_ tokens on the _value_, only the command to be run.

```bash
simple-menu item --type item --value "xterm"
simple-menu item --type audiomenu --value ""
```

### Helper mode

There are certain actions that need root permissions to execute.

To help with these cases the program includes a helper command.

It currently allows to start/stop a systemd unit, and start/stop a zerotier registered
network.

1. Allow the user running simple-menu to execute the helper mode with sudo without
   password. Add a line to sudoers like:

```text
myuser ALL=(ALL) NOPASSWD: /usr/local/bin/simple-menu helper *
```

2. Specify what systemd units, and what zerotier networks the user can toggle on
   /etc/simple-menu/simple-menu.toml.

```bash
simple-menu helper --systemd-unit-toggle cron.service
simple-menu helper --zerotier-network-get aabbccddeeffgghh
simple-menu helper --zerotier-network-toggle aabbccddeeffgghh
```

## Items

There are 4 basic item _types_:

- item: its _value_ defines the menu entry text and the command to execute.
- item*external: its \_value* defines an external command that will be launched to query
  for the menu entry text and the program and its arguments to execute when selected.
- menu*external: its \_value* defines an external command that will be launched to query
  for the menu entry text and the menu items.
- menu*inline: its \_value* defines the menu entry text and the menu items.

| name          | use case                                     | gets _menu-entry-text_ from | gets action from         |
| ------------- | -------------------------------------------- | --------------------------- | ------------------------ |
| item          | execute a command                            | first 5 tokens from _value_ | remaining _value_ tokens |
| menu_inline   | define menu from _value_                     | first 5 tokens from _value_ | remaining _value_ tokens |
| item_external | delegate item definition to external command | `command get_text` output   | `command execute` output |
| menu_external | delegate menu definition to external command | `command get_text` output   | `command execute` output |

### Item

This item type executes an external command when selected.

Can be used to show an informative item without an associated command, by either:

- setting its menu entry text type to notification.
- skipping setting a command on its value.

Examples:

- `--type text --value "notification :: :: :: :: some informative text"`.
- `--type text --value "action :: :: :: :: say hi ::notify-send::hi"`.

### Item External

This item type delegates to an external program both, setting the menu entry text, and
the item action.

`--value`: program and its arguments.

Example: `--type item_external --value my_script.sh::arg 1::arg 2`.

In the example, the script _my_script.sh_ will be called at different stages:

- `my_script.sh "get_text" "arg 1" "arg 2`: this is executed at menu build time. Its
  output will be used to format the menu entry text. Example output:
  - `action :: :: :: :: menu item text`

- `my_script.sh "execute" "arg 1" "arg 2"`: this is executed if the item is selected.

### Menu Inline

This item type generates a menu from its text value. It can embed itself, by using
nested token separators.

It is built using the following tokens:

- 5 tokens for _menu entry text_
- (optional) "title"
- (optional) value to use for title, which defaults to "Menu"
- (optional) "keep-opened"
- (optional) "0" or "1", which defaults to "1"
- (optional) "loop-timeout"
- (optional) float number, which defaults to 0.0
- item 1 _type_ + _value_ (using nested separator)
- item 2 _type_ + _value_ (using nested separator)
- ...
- item n _type_ + _value_ (using nested separator)

Example:

```bash
simple-menu menu \
    --type menu_inline \
    --value "menu::::::::MyMenu::title::MyTitle::item,,action,,,,,,,,say hi,,notify-send,,hi::item,,action,,,,,,,,say bye,,notify-send,,bye"
```

Nested tokens are read in this order:

- command line arguments: `simple-menu -s "token level1" -s "token level2" -s ...`
- configuration file, where token_separators can be set to a list of strings.
- default value, which defaults to:
  - "::" (level 1 token)
  - ",," (level 2 token)
  - ";;" (level 3 token)

_Some characters that are contained in the ascii characters table not widely used: ¤¦¶§._

### Menu External

This item type delegates to an external program both, setting the menu entry text, and
the menu items.

`--value`: program and its arguments.

Example: `--type menu_external --value my_script.sh::arg 1::arg 2`.

In the example, the script _my_script.sh_ will be called at different stages:

- `my_script.sh "get_text" "arg 1" "arg 2`: this is executed at menu build time. Its
  output will be used to format the menu entry text. Example output:
  - `menu :: :: :: :: My Menu`

- `my_script.sh "execute" "arg 1" "arg 2"`: this is executed if the item is selected and
  returns the menu definition.

The menu definition text is read line by line:

- first line contains the 5 menu entry text tokens.
- second line contains the menu options.
- following lines define a single item each one.

Example:

```text
menu :: :: :: :: My Menu
title :: My Menu
item :: action:: :: :: :: say hi ::notify-send::hi
item :: action:: :: :: :: open terminal ::xterm
```

### Audio Menu

Open a menu with audio controls.

`--value`: unused.

Example: `--type audiomenu --value ""`

### Syncthing Menu

Open a menu with syncthing controls.

`--value`: unused

Example: `--type syncthingmenu --value ""`

Check the configuration sample file to see how to configure this item.

### Systemd Unit

Start/stop a systemd unit.

`--value`: unit name, prefixed with "user:" for user units.

Examples:

- `--type systemdunit --value my_service.service`.
- `--type systemdunit --value user:my_service.service`.

Needs helper configured to toggle system level units.

### Zerotier Network

Start/stop a registered Zerotier network.

`--value`: identifier for the Zerotier network.

Example: `--type zerotiernetwork --value aabbccddeeffgghh:my alias`.

Needs helper configured.

## Menu entry text

The text shown by an item on a menu is defined by 5 tokens:

`<type> :: <category> :: <subcategory> :: <status> :: <text>`.

**Type**

- allowed values are _action_, _menu_, _notification_ and _raw_.
- _menu_, _action_ and _notification_ show an indicator icon on the menu.
- _notification_ type can not be executed, on selection it won't do anything.
- _raw_ type allows for a free line to be defined. Only the _text_ component is used,
  category, subcategory and status are ignored and menu item text is not formatted.

**Category, subcategory and status**

- These are optional.

**Text**

- Must be set. If not set the item is not shown.

Certain strings can be used and will be replaced by an icon. These can be checked on
_src/simple_menu/constants.py_ file.

This program expects to be used with a monospace font.
