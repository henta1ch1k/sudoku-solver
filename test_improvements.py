#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенного распознавания и решения Судоку.
Демонстрирует устойчивость к разным вариантам захвата изображения.
"""

import sys
sys.path.insert(0, '/home/mrx/Sudoku')

from sudoku_solver import SudokuSolver
import os

# Список тестовых сценариев (если вы добавите разные скриншоты)
test_images = [
    '/home/mrx/Sudoku/sudoku.png',
    '/home/mrx/Sudoku/Снимок экрана от 2025-11-11 10-46-18.png',
]

print("\n" + "="*60)
print("    ТЕСТИРОВАНИЕ УЛУЧШЕННОГО РАСПОЗНАВАНИЯ СУДОКУ       ")
print("="*60)

for img_path in test_images:
    if not os.path.exists(img_path):
        print(f"\n⚠ Файл не найден: {img_path}")
        continue
    
    print(f"\n📸 Тестирование: {os.path.basename(img_path)}")
    print("-" * 60)
    
    solver = SudokuSolver()
    
    try:
        board = solver.load_board_from_image(img_path)
        
        # Проверяем конфликты
        conflicts = solver.find_conflicts(board)
        if conflicts:
            print(f"⚠ Найдено конфликтов: {len(conflicts)}")
            for c in conflicts[:3]:  # Показываем первые 3
                print(f"   - {c['type']}: число {c['value']} повторяется")
        else:
            print("✓ Конфликтов не найдено")
        
        # Показываем распознанную доску
        print("\n📋 Распознанная доска:")
        solver.print_board(board)
        
        # Пытаемся решить
        if not conflicts:
            print("🔄 Решаю...")
            if solver.solve():
                print(f"✅ Решено! ({solver.solution_steps} шагов)")
            else:
                print("❌ Решение не найдено")
        else:
            print("❗ Пропускаю решение из-за конфликтов")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n" + "="*60)
print("Тестирование завершено")
print("="*60 + "\n")
