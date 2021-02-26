import cv2.cv2 as cv2
import numpy as np
import pyautogui
import requests
import rgbxy
import json
import time
import os


def get_bridge_ip(number=0):
    return requests.get("https://discovery.meethue.com/").json()[number]["internalipaddress"]


if os.path.isfile("testconfig.json"):
    CONFIG = json.loads(open("testconfig.json", "r").read())
else:
    CONFIG = json.loads(open("config.json", "r").read())

if CONFIG["adress"].lower() == "auto":
    adress = get_bridge_ip()
else:
    adress = CONFIG["adress"]
username = CONFIG["user"]
baseURL = f"http://{adress}/api/{username}/"
lURL = f"{baseURL}lights/"

sync_lamps = CONFIG["lamps"]


def add_lamps_in_room(room: str):
    for lamp in requests.get(f"{baseURL}groups/{room}/").json()["lights"]:
        sync_lamps.append(lamp)


for group in CONFIG["groups"]:
    add_lamps_in_room(group)


def set_all_xyb(x, y, bri, transtime=0) -> list[requests.models.Response]:
    res: list[requests.models.Response] = []
    for lamp in sync_lamps:
        res.append(set_xyb(lamp, x, y, bri, transtime=transtime))
    return res


def set_xyb(lamp: str, x, y, bri, transtime=0) -> requests.models.Response:
    return requests.put(f"{lURL}{lamp}/state/", json={"xy": [x, y], "bri": bri, "transitiontime": transtime})


def screenshot():
    return np.array(pyautogui.screenshot())[:, :, ::-1].copy()


def bgr_to_rgb(bgr) -> tuple[int, int, int]:
    return bgr[2], bgr[1], bgr[0]


def get_main_color_on_screen():
    sc = screenshot()
    data = np.reshape(sc, (-1, 3))
    data = np.float32(data)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_RANDOM_CENTERS
    compactness, labels, centers = cv2.kmeans(data, 1, None, criteria, 10, flags)

    rgb = bgr_to_rgb(centers[0].astype(np.int32))

    return tuple(rgb)


def main():
    while True:
        try:
            # Get Values
            r, g, b = get_main_color_on_screen()
            x, y = rgbxy.Converter().rgb_to_xy(r, g, b)
            bri = min(CONFIG["maxbri"], int(abs(100 - (r + g + b))))

            set_all_xyb(x, y, bri, transtime=CONFIG["transitiontime"])

            time.sleep(1000 / CONFIG["updatespermillisecond"])
        except Exception as ex:
            print(ex)


if __name__ == "__main__":
    main()
