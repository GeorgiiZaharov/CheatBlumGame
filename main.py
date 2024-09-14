import cv2
import pickle
import os
import pyautogui
import numpy as np
import random
import time
import sys

from detect import *

import mss

# Настройки pyautogui для ускорения кликов
pyautogui.PAUSE = 0  # Отключаем паузу между действиями
DEBUG_MODE = False # Отключаем отладку

# Взаимодействие с системой
def take_screenshot(x, y, w, h):
    with mss.mss() as sct:
        monitor = {"top": y, "left": x, "width": w, "height": h}
        screenshot = np.array(sct.grab(monitor))
        return cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
def click_left_mouse_button(x, y, offset_x, offset_y):
    pyautogui.moveTo(x + offset_x, y + offset_y, duration=0)
    pyautogui.click()

class Cheat:
    def __init__(self, debug_mode=False):
        # Настройка диапазонов HSV для распознавания объектов
        self.detect_blum = Detect((0, 69, 255), "Blum", RangeHSV(39, 67, 57, 255, 74, 255))
        self.detect_bomb = Detect((0, 0, 255), "Bomb", RangeHSV(0, 179, 0, 24, 85, 149))
        self.blum_hit_probability = 400
        # Формат {time: --, l: --, r: --, top: --, bottom: --}
        self.was_press = []
        self.bombs = []

        self.x = None
        self.y = None

        self.border = 10
        self.recharge_time = 800
        self.bomb_track_time = 300
        self.time_for_recharge = self.recharge_time
        self.debug_mode = debug_mode

    def need_hit(self, probability: int) -> bool:
        return random.randint(0, 1000) < probability

    def is_intersects_or_touches(self, note, dot) -> bool:
        return note["l"] <= dot[0] <= note["r"] and note["top"] <= dot[1] <= note["bottom"] 

    def is_intersects(self, note, dot) -> bool:
        return note["l"] <= dot[0] <= note["r"] and note["top"] <= dot[1] <= note["bottom"] 
    
    # Проверка столкновений
    def collision_with_bombs(self, dot) -> bool:
        return any(self.is_intersects_or_touches(bomb_note, dot) for bomb_note in self.bombs)

    def collision_with_taps(self, dot) -> bool:
        return any(self.is_intersects_or_touches(tap_note, dot) for tap_note in self.was_press)
    
    def may_tap(self, dot) -> bool:
        return not self.collision_with_bombs(dot) and not self.collision_with_taps(dot)


    def click_on_obj(self, rect):
        preemption = random.randint(10, 15)
        aim_x = rect[0] + rect[2] // 2
        aim_y = rect[1] + rect[3] // 2 + preemption # Берем упреждение

        current_time_ms = time.time_ns() // 1_000_000

        # Проверка безопасности нажатия
        # Первая часть нужна, чтобы дать объектам спуститься
        if aim_y > 42 and self.may_tap([aim_x, aim_y]):
            note = {
                    "time": current_time_ms,
                    "l": aim_x - self.border,
                    "r": aim_x + self.border,
                    "top": aim_y - self.border,
                    "bottom": aim_y + 5 * self.border
                    }
            self.was_press.append(note)
            click_left_mouse_button(self.x, self.y, aim_x, aim_y)

    def run(self, x, y, w, h):
        self.x = x
        self.y = y
        if self.debug_mode:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter('output.avi', fourcc, 8.0, (w, h))
            start_time = time.time()
        
        start_iteration_time = time.time()
        iteration_count = 0
        
        while True:
            iteration_count += 1
            
            img = take_screenshot(x, y, w, h)
            self.detect_blum.draw_bounds(img)
            self.detect_bomb.draw_bounds(img)

            detected_blums = self.detect_blum.get_bounds(img)
            detected_bombs = self.detect_bomb.get_bounds(img)
            
            for bomb in detected_bombs:
                note = {
                        "time": current_time_ms,
                        "l": bomb[0] - self.border,
                        "r": bomb[0] + bomb[2] + self.border,
                        "top": bomb[1] - self.border,
                        "bottom": bomb[1] + bomb[3] + 5 * self.border
                        }
                self.bombs.append(note)
            
            # Сортируем снизу вверх, чтобы сначала тыкать те, что пониже
            detected_blums = sorted(detected_blums, key=lambda rect: rect[1], reverse=True)

            for blum in detected_blums:
                if self.need_hit(self.blum_hit_probability) or blum[1] >= 500:
                    self.click_on_obj(blum)

            # Обновляем данные
            current_time_ms = time.time_ns() // 1_000_000
            self.was_press = list(filter(lambda note: current_time_ms - note["time"] < self.time_for_recharge, self.was_press))

            self.bombs = list(filter(lambda note: current_time_ms - note["time"] < self.bomb_track_time, self.bombs))
            if self.debug_mode:
                if time.time() - start_time < 30:
                    out.write(img)
                else:
                    out.release()
                    self.debug_mode = False

            # Измерение и вывод количества итераций в секунду
            if time.time() - start_iteration_time >= 1:
                print(f"\rIterations per second: {iteration_count}", end="")
                start_iteration_time = time.time()
                iteration_count = 0

def main():
    file_path = 'config.pkl'
    # Проверка, существует ли файл с конфигурацией
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            x, y, w, h = pickle.load(file)
    else:
        # Установка значений по умолчанию
        x, y, w, h = 0, 0, 800, 600

    print(f"Текущие значения: x={x}, y={y}, w={w}, h={h}")
    update = input("Хотите обновить значения? (Введите 'да' для обновления, Enter для использования текущих): ").strip().lower()

    if update == 'да':
        x = int(input("Введите значение x: "))
        y = int(input("Введите значение y: "))
        w = int(input("Введите значение w: "))
        h = int(input("Введите значение h: "))

        with open(file_path, 'wb') as file:
            pickle.dump((x, y, w, h), file)

    cheat = Cheat(DEBUG_MODE)
    cheat.run(x, y, w, h)

if __name__ == "__main__":
    main()
