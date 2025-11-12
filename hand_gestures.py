#!/usr/bin/env python3
"""
Распознавание жестов (камень/ножницы/бумага, OK) через веб-камеру ноутбука.
Использует MediaPipe Hands + OpenCV и простые эвристики по landmark.

Запуск:
    python3 hand_gestures.py

Нажмите q для выхода.
"""

import cv2
import time
import numpy as np
import mediapipe as mp

# Параметры стабильности
STABLE_FRAMES = 6  # число последовательных кадров для подтверждения жеста

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Индексы ключевых точек (MediaPipe)
TIP_IDS = [4, 8, 12, 16, 20]


def distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def get_hand_size(landmarks):
    # Оценка размера руки: расстояние между запястьем и средней точкой кончиков
    wrist = np.array([landmarks[0].x, landmarks[0].y])
    middle_tip = np.array([landmarks[12].x, landmarks[12].y])
    return np.linalg.norm(wrist - middle_tip)


def classify_gesture(landmarks, img_w, img_h):
    """
    Эвристическая классификация жестов:
    - paper: все 5 пальцев раскрыты
    - rock: все пальцы согнуты (кроме, возможно, большого)
    - scissors: только указательный и средний пальцы раскрыты
    - ok: кончик большого пальца и указательного близко друг к другу

    Возвращает метку: 'paper', 'rock', 'scissors', 'ok' или None
    """
    # Перевод координат в пиксели
    pts = [(int(lm.x * img_w), int(lm.y * img_h)) for lm in landmarks]

    # Базовая длина для нормализации
    hand_size = get_hand_size(landmarks)
    if hand_size == 0:
        hand_size = 1e-6

    # Проверяем близость большого пальца и указательного для OK
    d_thumb_index = distance(pts[4], pts[8]) / hand_size
    if d_thumb_index < 0.35:
        # убедимся, что остальные пальцы не все согнуты (иначе это может быть кулак с пальцем и большим вместе)
        # проверим среднюю высоту кончиков остальных пальцев относительно pip
        middle_extended = pts[12][1] < pts[10][1]
        ring_extended = pts[16][1] < pts[14][1]
        pinky_extended = pts[20][1] < pts[18][1]
        if middle_extended or ring_extended or pinky_extended:
            return 'ok'

    # Для остальных жестов определим, какие пальцы раскрыты.
    # Для каждого пальца (кроме большого) проверяем: tip_y < pip_y => палец раскрыт (в вертикальной ориентации)
    fingers = []
    # Index finger
    fingers.append(landmarks[8].y < landmarks[6].y)
    # Middle
    fingers.append(landmarks[12].y < landmarks[10].y)
    # Ring
    fingers.append(landmarks[16].y < landmarks[14].y)
    # Pinky
    fingers.append(landmarks[20].y < landmarks[18].y)

    # Большой палец: проверим в горизонтальной проекции (x), для правой руки tip.x > ip.x если раскрыт
    thumb_is_open = abs(landmarks[4].x - landmarks[3].x) > 0.03
    # Возможно, определить направление руки (левая/правая) не обязательно для наших жестов

    opened_count = sum(fingers) + (1 if thumb_is_open else 0)

    # Paper: большинство пальцев раскрыты
    if opened_count >= 4:
        return 'Bumaga'

    # Rock: почти все пальцы согнуты
    if opened_count <= 1:
        return 'Kamen'

    # Scissors: только index и middle раскрыты
    if fingers[0] and fingers[1] and (not fingers[2]) and (not fingers[3]):
        return 'Noznicy'

    return None


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('Не удалось открыть камеру. Проверьте подключение.')
        return

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)

    prev_label = None
    label_count = 0
    confirmed_label = None
    last_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img_h, img_w = frame.shape[:2]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        label = None
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            label = classify_gesture(hand_landmarks.landmark, img_w, img_h)

        # Стабилизация: подтверждаем жест, если он держится несколько кадров
        if label == prev_label and label is not None:
            label_count += 1
        else:
            label_count = 0
        prev_label = label

        if label_count >= STABLE_FRAMES:
            if confirmed_label != label:
                confirmed_label = label
                print(f'[INFO] Gesture confirmed: {confirmed_label} at {time.ctime()}')
        # Показ метки на кадре
        display_text = confirmed_label if confirmed_label is not None else (label if label is not None else '')
        cv2.putText(frame, f'Start: {display_text}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        cv2.imshow('Hand Gestures (rps+ok)', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    hands.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()