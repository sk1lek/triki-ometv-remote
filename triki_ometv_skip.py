import asyncio
import time

import pyautogui
from bleak import BleakClient, BleakScanner


NUS_WRITE = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
NUS_NOTIFY = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

CMD_START_MAIN = bytes.fromhex("201000D007680003")
CMD_START_ALT = bytes.fromhex("201000D007680001")
CMD_STOP = bytes.fromhex("20000000000000")

FRAME_LEN = 14

LONG_PRESS_SECONDS = 0.7
ACTION_COOLDOWN = 0.4

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


def score_device(name, uuids):
    name_l = (name or "").lower()
    uuids_l = " ".join(uuids or []).lower()

    score = 0

    if "triki" in name_l:
        score += 50

    if "controller" in name_l or "game" in name_l or "pad" in name_l:
        score += 10

    if "6e400001" in uuids_l or "6e400002" in uuids_l or "6e400003" in uuids_l:
        score += 40

    return score


async def pick_device():
    print("Scanning for BLE devices for 8 seconds...")
    print("Press the Triki button if the device is sleeping.")

    found_raw = await BleakScanner.discover(timeout=8.0, return_adv=True)

    devices = []

    for device, adv in found_raw.values():
        name = getattr(adv, "local_name", None) or getattr(device, "name", None) or "Unknown"
        uuids = getattr(adv, "service_uuids", None) or []

        devices.append(
            {
                "device": device,
                "name": name,
                "address": device.address,
                "uuids": uuids,
                "score": score_device(name, uuids),
            }
        )

    devices.sort(key=lambda d: d["score"], reverse=True)

    print("\nFound devices:")

    for i, d in enumerate(devices[:15]):
        print(f"[{i}] score={d['score']:>2}  {d['name']}  {d['address']}")

    if not devices:
        raise RuntimeError("No BLE devices found.")

    choice = input("\nSelect device number [Enter = 0]: ").strip()
    index = int(choice) if choice else 0

    return devices[index]["address"]


async def write_cmd(client, cmd):
    try:
        await client.write_gatt_char(NUS_WRITE, cmd, response=False)
    except Exception:
        await client.write_gatt_char(NUS_WRITE, cmd, response=True)


def capture_position(label):
    print()
    print(f"Move your cursor over the {label} button.")
    print("Switch back to this terminal with Alt + Tab without moving the mouse.")
    input("Press Enter to save the position... ")

    pos = pyautogui.position()

    print(f"{label}: x={pos.x}, y={pos.y}")

    return pos.x, pos.y


async def main():
    print("Triki OmeTV Remote")
    print("==================")
    print()

    skip_x, skip_y = capture_position("Skip / Next")
    stop_x, stop_y = capture_position("Stop")

    address = await pick_device()

    stash = bytearray()
    last_button = False
    press_started_at = None
    long_action_done = False
    last_action_at = 0.0
    frame_count = 0

    def do_click(label, x, y):
        nonlocal last_action_at

        now = time.time()

        if now - last_action_at < ACTION_COOLDOWN:
            return

        last_action_at = now

        pyautogui.click(x, y)

        print(label)

    def do_skip():
        do_click("SKIP", skip_x, skip_y)

    def do_stop():
        do_click("STOP", stop_x, stop_y)

    def handle_notify(sender, data):
        nonlocal last_button
        nonlocal press_started_at
        nonlocal long_action_done
        nonlocal frame_count

        stash.extend(data)

        while len(stash) >= FRAME_LEN:
            header_at = -1

            for i in range(len(stash) - 1):
                if stash[i] == 0x22 and stash[i + 1] in (0x00, 0x01):
                    header_at = i
                    break

            if header_at == -1:
                del stash[:-1]
                return

            if header_at > 0:
                del stash[:header_at]

            if len(stash) < FRAME_LEN:
                return

            frame = bytes(stash[:FRAME_LEN])
            del stash[:FRAME_LEN]

            frame_count += 1

            button_pressed = frame[1] == 0x01
            now = time.time()

            if button_pressed and not last_button:
                press_started_at = now
                long_action_done = False

            if button_pressed and press_started_at is not None and not long_action_done:
                held_for = now - press_started_at

                if held_for >= LONG_PRESS_SECONDS:
                    do_stop()
                    long_action_done = True

            if not button_pressed and last_button:
                if press_started_at is not None:
                    held_for = now - press_started_at

                    if not long_action_done and held_for < LONG_PRESS_SECONDS:
                        do_skip()

                press_started_at = None
                long_action_done = False

            last_button = button_pressed

    print(f"\nConnecting to {address}...")

    async with BleakClient(address) as client:
        print("Connected.")
        print("Subscribing to notifications...")

        await client.start_notify(NUS_NOTIFY, handle_notify)

        print("Starting data stream...")

        await write_cmd(client, CMD_START_MAIN)

        await asyncio.sleep(2.0)

        if frame_count == 0:
            print("No frames received. Trying alternative start command...")
            await write_cmd(client, CMD_START_ALT)

        print()
        print("Ready.")
        print("Short press = Skip / Next")
        print(f"Long press ({LONG_PRESS_SECONDS}s) = Stop")
        print("Press Ctrl+C to exit.")

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            try:
                await write_cmd(client, CMD_STOP)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")