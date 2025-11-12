#!/usr/bin/env python3
"""
Программа для распознавания и решения Судоку из изображений
Автор: AI Assistant
"""

import cv2
import numpy as np
import pytesseract
import os
import sys
import gc
import time
import argparse
from pathlib import Path

# Очистка кэша для обновления данных
gc.collect()


class SudokuSolver:
    """Класс для распознавания и решения Судоку"""
    
    def __init__(self, image_path=None):
        """
        Инициализация решателя Судоку
        
        Args:
            image_path: путь к изображению Судоку (опционально)
        """
        self.board = None
        self.image_path = image_path
        self.solution_steps = 0
        # Очищаем кэш при создании нового экземпляра
        gc.collect()
        
    # ========== РАСПОЗНАВАНИЕ ИЗОБРАЖЕНИЯ ==========
    
    def load_board_from_image(self, image_path):
        """
        Загружает Судоку из изображения с умной обработкой контуров.
        Ищет квадратный контур и использует морфологическую обработку.
        
        Args:
            image_path: путь к фа4йлу изображения
            
        Returns:
            board: матрица 9x9 с распознанными цифрами
        """
        # Очищаем старые данные
        gc.collect()
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл не найден: {image_path}")
        
        # Читаем изображение напрямую из файла (без кэширования)
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise ValueError(f"Не удалось прочитать изображение: {image_path}")
        
        # Предварительная обработка
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Адаптивная пороговая обработка
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Морфологическая обработка для очистки шума и дефектов
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Поиск контуров
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            raise ValueError("Контуры сетки Судоку не найдены")
        
        # Умный поиск контура сетки (не просто самый большой, а близкий к квадрату)
        grid_contour = self._find_grid_contour(contours)
        if grid_contour is None:
            raise ValueError("Не удалось найти квадратный контур сетки Судоку")
        
        # Получаем приблизительный контур
        peri = cv2.arcLength(grid_contour, True)
        approx = cv2.approxPolyDP(grid_contour, 0.02 * peri, True)
        
        if len(approx) != 4:
            raise ValueError("Сетка Судоку должна иметь 4 угла")
        
        # Извлекаем точки углов и сортируем их
        pts = np.float32([p[0] for p in approx])
        pts = self._order_points(pts)
        
        # Перспективное преобразование
        side = 450
        dst_pts = np.float32([
            [0, 0], [side, 0], [0, side], [side, side]
        ])
        
        matrix = cv2.getPerspectiveTransform(pts, dst_pts)
        warped = cv2.warpPerspective(image, matrix, (side, side))
        
        # Распознавание цифр
        self.board = self._recognize_digits(warped)
        return self.board
    
    def _find_grid_contour(self, contours):
        """
        Ищет контур сетки Судоку, отдавая предпочтение близким к квадратам.
        Это помогает игнорировать внешние рамки и посторонние элементы.
        
        Args:
            contours: список найденных контуров
            
        Returns:
            grid_contour: найденный контур сетки или None
        """
        best_contour = None
        best_score = -1
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Пропускаем очень маленькие и слишком большие контуры
            if area < 10000 or area > 1000000:
                continue
            
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            # Ищем четырёхугольники
            if len(approx) != 4:
                continue
            
            # Проверяем, похож ли контур на квадрат
            pts = np.array([p[0] for p in approx])
            
            # Вычисляем расстояния между углами (длины сторон)
            dists = []
            for i in range(4):
                d = np.linalg.norm(pts[i] - pts[(i + 1) % 4])
                dists.append(d)
            
            # Идеальный квадрат: все стороны примерно равны
            mean_dist = np.mean(dists)
            std_dist = np.std(dists)
            
            # Чем ближе std_dist к 0, тем лучше квадрат
            # squareness: 1.0 для идеального квадрата, близко к 0 для вытянутых фигур
            squareness = 1.0 / (1.0 + std_dist / (mean_dist + 1e-6))
            
            # Предпочитаем контуры с большей площадью и лучшей квадратностью
            score = area * squareness
            
            if score > best_score:
                best_score = score
                best_contour = contour
        
        return best_contour
    
    def _order_points(self, pts):
        """
        Упорядочивает точки в порядке: верхний-левый, верхний-правый,
        нижний-левый, нижний-правый
        """
        # Находим верхние и нижние точки
        sorted_y = sorted(pts, key=lambda p: p[1])
        top_points = sorted(sorted_y[:2], key=lambda p: p[0])
        bottom_points = sorted(sorted_y[2:], key=lambda p: p[0])
        
        return np.array([
            top_points[0],      # верхний-левый
            top_points[1],      # верхний-правый
            bottom_points[0],   # нижний-левый
            bottom_points[1]    # нижний-правый
        ])
    
    def _recognize_digits(self, grid_image):
        """
        Распознаёт цифры в каждой клетке сетки
        
        Args:
            grid_image: изображение выпрямленной сетки
            
        Returns:
            board: матрица 9x9 с распознанными цифрами
        """
        board = []
        cell_size = grid_image.shape[0] // 9
        
        for row in range(9):
            row_data = []
            for col in range(9):
                # Извлекаем клетку
                y1 = row * cell_size
                y2 = (row + 1) * cell_size
                x1 = col * cell_size
                x2 = (col + 1) * cell_size
                
                cell = grid_image[y1:y2, x1:x2]
                
                # Обработка изображения клетки
                gray_cell = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
                _, thresh_cell = cv2.threshold(gray_cell, 150, 255, cv2.THRESH_BINARY)
                
                # Находим контуры цифр
                contours, _ = cv2.findContours(
                    thresh_cell, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                
                digit = 0
                if contours:
                    # Находим наибольший контур (саму цифру)
                    largest_contour = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest_contour)
                    
                    # Если контур достаточно большой - это цифра
                    if area > 100:
                        # Выделяем прямоугольник вокруг цифры
                        x, y, w, h = cv2.boundingRect(largest_contour)
                        digit_roi = gray_cell[y:y+h, x:x+w]
                        
                        # Масштабируем до стандартного размера
                        digit_roi = cv2.resize(digit_roi, (28, 28))
                        
                        # Распознавание с помощью OCR
                        text = pytesseract.image_to_string(
                            digit_roi, config='--psm 10 digits'
                        ).strip()
                        
                        try:
                            digit = int(text) if text else 0
                            if digit < 0 or digit > 9:
                                digit = 0
                        except ValueError:
                            digit = 0
                
                row_data.append(digit)
            board.append(row_data)
        
        return board
    
    # ========== РЕШЕНИЕ СУДОКУ ==========
    
    def is_valid(self, board, row, col, num):
        """Проверяет, можно ли поместить число в позицию"""
        
        # Проверка строки
        if num in board[row]:
            return False
        
        # Проверка столбца
        if num in [board[i][col] for i in range(9)]:
            return False
        
        # Проверка 3x3 блока
        box_row, box_col = (row // 3) * 3, (col // 3) * 3
        for i in range(box_row, box_row + 3):
            for j in range(box_col, box_col + 3):
                if board[i][j] == num:
                    return False
        
        return True
    
    def find_empty(self, board):
        """Находит первую пустую клетку (для совместимости)"""
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    return (i, j)
        return None
    
    def get_candidates(self, board, row, col):
        """Возвращает список возможных значений для клетки (для MRV)"""
        candidates = []
        for num in range(1, 10):
            if self.is_valid(board, row, col, num):
                candidates.append(num)
        return candidates
    
    def find_empty_mrv(self, board):
        """
        Находит пустую клетку с минимумом оставшихся значений (MRV).
        Это значительно уменьшает дерево поиска.
        """
        best_cell = None
        min_candidates = 10
        
        for i in range(9):
            for j in range(9):
                if board[i][j] == 0:
                    candidates = self.get_candidates(board, i, j)
                    if len(candidates) < min_candidates:
                        min_candidates = len(candidates)
                        best_cell = (i, j, candidates)
                        
                        # Ранний выход: если нет доступных значений, эта ветка невалидна
                        if min_candidates == 0:
                            return None
        
        return best_cell
    
    def solve(self, board=None):
        """
        Оптимизированный решатель Судоку с эвристиками:
        - Minimum Remaining Values (MRV)
        - Ранний отсев невалидных ветвей
        
        Args:
            board: матрица Судоку (используется текущая, если не указана)
            
        Returns:
            True если решение найдено, False в противном случае
        """
        if board is None:
            board = self.board
        
        # Используем MRV для выбора клетки
        result = self.find_empty_mrv(board)
        
        if result is None:
            # Проверяем, является ли это завершением или неудачей
            empty = self.find_empty(board)
            if empty is None:
                return True  # Судоку решена
            else:
                return False  # Нет доступных значений — ветка невалидна
        
        row, col, candidates = result
        
        # Пробуем каждое доступное значение в порядке от 1 до 9
        for num in candidates:
            board[row][col] = num
            self.solution_steps += 1
            
            if self.solve(board):
                return True
            
            board[row][col] = 0
        
        return False
    
    # ========== УТИЛИТЫ ==========
    
    def load_test_board(self):
        """Загружает тестовую доску Судоку"""
        self.board = [
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9]
        ]
        return self.board
    
    def print_board(self, board=None):
        """Красиво печатает доску Судоку"""
        if board is None:
            board = self.board
        
        print("\n" + "=" * 25)
        for i, row in enumerate(board):
            if i % 3 == 0 and i != 0:
                print("-" * 25)
            
            row_str = ""
            for j, num in enumerate(row):
                if j % 3 == 0 and j != 0:
                    row_str += "| "
                row_str += (str(num) if num != 0 else ".") + " "
            
            print(row_str)
        print("=" * 25 + "\n")
    
    def get_statistics(self):
        """Возвращает статистику решения"""
        return {
            "steps": self.solution_steps,
            "filled_cells": sum(1 for row in self.board for cell in row if cell != 0)
        }

    def find_conflicts(self, board=None):
        """Ищет явные конфликты в доске (повторы в строках/столбцах/блоках).

        Возвращает список словарей с полями: type ('row'/'col'/'box'),
        index (номер строки/столбца/блока), value (повторяющееся число),
        positions (список (r,c) координат).
        """
        if board is None:
            board = self.board
        conflicts = []

        # Строки
        for i in range(9):
            counts = {}
            for j in range(9):
                v = board[i][j]
                if v == 0:
                    continue
                counts.setdefault(v, []).append((i, j))
            for val, poses in counts.items():
                if len(poses) > 1:
                    conflicts.append({
                        'type': 'row', 'index': i, 'value': val, 'positions': poses
                    })

        # Столбцы
        for j in range(9):
            counts = {}
            for i in range(9):
                v = board[i][j]
                if v == 0:
                    continue
                counts.setdefault(v, []).append((i, j))
            for val, poses in counts.items():
                if len(poses) > 1:
                    conflicts.append({
                        'type': 'col', 'index': j, 'value': val, 'positions': poses
                    })

        # 3x3 блоки
        for br in range(3):
            for bc in range(3):
                counts = {}
                for i in range(br * 3, br * 3 + 3):
                    for j in range(bc * 3, bc * 3 + 3):
                        v = board[i][j]
                        if v == 0:
                            continue
                        counts.setdefault(v, []).append((i, j))
                for val, poses in counts.items():
                    if len(poses) > 1:
                        conflicts.append({
                            'type': 'box', 'index': (br, bc), 'value': val, 'positions': poses
                        })

        return conflicts


def main():
    """Основная функция программы"""
    
    # Очищаем все кэши перед началом
    gc.collect()
    
    print("\n" + "=" * 50)
    print("       РЕШАТЕЛЬ СУДОКУ С РАСПОЗНАВАНИЕМ        ")
    print("=" * 50)
    
    # Создаём новый экземпляр решателя
    solver = SudokuSolver()
    
    # Получаем путь к изображению (поддержка аргумента командной строки)
    parser = argparse.ArgumentParser(description='Sudoku solver with optional image input')
    parser.add_argument('-i', '--image', help='Путь к изображению Судоку', default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    if args.image:
        image_path = Path(args.image)
    else:
        image_path = script_dir / "sudoku.png"

    # Если стандартного файла нет, попробуем выбрать самый новый png/jpg в директории
    if not image_path.exists():
        patterns = ["*.png", "*.jpg", "*.jpeg"]
        candidates = []
        for pat in patterns:
            candidates.extend(list(script_dir.glob(pat)))
        if candidates:
            # выбираем файл с максимально поздним временем изменения
            image_path = max(candidates, key=lambda p: p.stat().st_mtime)
            print(f"   Найден файл для использования: {image_path}")

    print(f"\n🔍 Используемый файл изображения: {image_path}")
    print(f"   Существует: {image_path.exists()}")

    if image_path.exists():
        # Проверяем время последнего изменения файла
        mod_time = os.path.getmtime(image_path)
        mod_time_str = time.ctime(mod_time)
        print(f"   Последнее изменение: {mod_time_str}")

        try:
            print(f"\n📸 Загружаю изображение: {image_path}")
            solver.load_board_from_image(str(image_path))
            print("✓ Изображение успешно загружено и распознано")
        except Exception as e:
            print(f"⚠ Ошибка при загрузке изображения: {e}")
            print("📋 Использую тестовую Судоку...\n")
            solver.load_test_board()
    else:
        print(f"\n⚠ Файл {image_path} не найден")
        print("📋 Использую тестовую Судоку для демонстрации...\n")
        solver.load_test_board()
    
    # Показываем исходную доску
    print("📌 Исходная Судоку:")
    solver.print_board()

    # Диагностика: проверим явные конфликты
    conflicts = solver.find_conflicts(solver.board)
    if conflicts:
        print("⚠ Найдены явные конфликты в распознанной доске:")
        for c in conflicts:
            if c['type'] in ('row', 'col'):
                print(f" - {c['type']} {c['index']}: число {c['value']} повторяется в позициях {c['positions']}")
            else:
                print(f" - box {c['index']}: число {c['value']} повторяется в позициях {c['positions']}")
        print("\n❗ OCR, возможно, ошибся при распознавании. Рекомендую вручную исправить доску или использовать опцию --image с другим файлом.")
        return
    
    # Решаем
    print("🔄 Решаю Судоку...")
    if solver.solve():
        print("\n✅ СУДОКУ РЕШЕНА!")
        print("\n📊 Решённая Судоку:")
        solver.print_board()
        
        stats = solver.get_statistics()
        print(f"📈 Статистика:")
        print(f"   • Шагов решения: {stats['steps']}")
        print(f"   • Заполнено клеток: {stats['filled_cells']}")
    else:
        print("\n❌ Решение не найдено (возможно, некорректная Судоку)")


if __name__ == "__main__":
    main()
