# Triki OmeTV Remote

Use the Żabka **Triki** BLE controller as a tiny remote for OmeTV on desktop.

* short press → Skip / Next
* long press → Stop

This is a small 4fun project. Not affiliated with Żabka, Żappka, Triki or OmeTV.

## How it works

Triki does not show up as a normal gamepad on Windows, so tools like JoyToKey do not see it.

This script connects to Triki over Bluetooth Low Energy, reads button state notifications, and turns them into mouse clicks at saved screen positions.

It does not modify OmeTV. It only clicks where you tell it to click.

## Requirements

* Windows 10/11
* Python 3.10+
* Bluetooth
* Żabka Triki controller

## Install

```powershell
git clone https://github.com/sk1lek/triki-ometv-remote.git
cd triki-ometv-remote

py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe .\triki_ometv_skip.py
```

The script will ask you to save two mouse positions:

1. Skip / Next button
2. Stop button

Move your cursor over the requested button, switch back to the terminal with `Alt + Tab`, and press `Enter`.

## Configuration

Long press duration:

```python
LONG_PRESS_SECONDS = 0.7
```

Increase it if Stop triggers too easily. Decrease it if long press feels too slow.

## Troubleshooting

If Triki is not detected:

* make sure Bluetooth is enabled,
* press the Triki button before scanning,
* restart the script,
* remove Triki from Windows Bluetooth settings and pair it again,
* make sure no other app is connected to it.

If clicks hit the wrong place, restart the script and save the button positions again.
