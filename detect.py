import cv2
import numpy as np

class RangeHSV:
    def __init__(self, hmin, hmax, smin, smax, vmin, vmax):
        self.lower = np.array([hmin, smin, vmin])
        self.upper = np.array([hmax, smax, vmax])

    def get_lower(self):
        return self.lower

    def get_upper(self):
        return self.upper

class Detect:
    def __init__(self, border_color, label, range_hsv):
        self.border_color = border_color
        self.label = label
        self.range_hsv = range_hsv

    def get_bounds(self, img):
        # Преобразование изображения в цветовое пространство HSV
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # Создание маски по диапазону HSV
        mask = cv2.inRange(img_hsv, self.range_hsv.get_lower(), self.range_hsv.get_upper())
        # Размытие по Гауссу с ядром 3x3
        blurred = cv2.GaussianBlur(mask, (3, 3), 0)
        # Определение границ с помощью Canny
        edges = cv2.Canny(blurred, 25, 75)
        # Увеличение размеров объектов на изображении
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel)

        # Нахождение контуров
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Определение координат прямоугольников вокруг контуров
        bounds = [cv2.boundingRect(contour) for contour in contours if cv2.contourArea(contour) > 20]
        return bounds

    def draw_bounds(self, img):
        # Получение координат объектов
        bounds = self.get_bounds(img)
        # Рисование рамок вокруг объектов
        for rect in bounds:
            cv2.rectangle(img, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), self.border_color, 2)
            label_rect = (rect[0], rect[1] - 8, 34, 10)
            cv2.rectangle(img, (label_rect[0], label_rect[1]), 
                          (label_rect[0] + label_rect[2], label_rect[1] + label_rect[3]), (255, 255, 255), cv2.FILLED)
            cv2.putText(img, self.label, (rect[0], rect[1]), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.5, (0, 0, 0), 1)

# Пример использования
if __name__ == "__main__":
    # Настройки диапазонов HSV для распознавания объектов
    blum_hsv = RangeHSV(39, 67, 57, 255, 74, 255)
    detect_blum = Detect((0, 69, 255), "Blum", blum_hsv)

    bomb_hsv = RangeHSV(0, 179, 0, 24, 85, 149)
    detect_bomb = Detect((0, 0, 255), "Bomb", bomb_hsv)

    # Захват изображения (замените этот код на реальный захват изображения)
    img = cv2.imread('/home/georgii/Изображения/BIMBIMBAMBAM.png')  # Замените на путь к вашему изображению

    detect_blum.draw_bounds(img)
    detect_bomb.draw_bounds(img)

    # Показать результат
    cv2.imshow('Detected', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
