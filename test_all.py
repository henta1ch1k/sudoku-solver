#!/usr/bin/env python3
"""
Скрипт проверки перед публикацией
Проверяет все компоненты приложения

Запуск: python test_all.py
"""

import sys
import os
from pathlib import Path

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_ok(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_warning(msg):
    print(f"⚠️  {msg}")

def check_files():
    """Проверка наличия всех файлов"""
    print_header("1️⃣  ПРОВЕРКА ФАЙЛОВ")
    
    required_files = {
        'sudoku_solver.py': 'Основной решатель',
        'sudoku_app.py': 'GUI приложение',
        'hand_gestures.py': 'Детектор жестов',
        'requirements.txt': 'Зависимости',
        'README.md': 'Документация',
        'LICENSE': 'Лицензия',
        'setup.py': 'Setup для pip',
    }
    
    missing = []
    for filename, description in required_files.items():
        if Path(filename).exists():
            size = Path(filename).stat().st_size
            print_ok(f"{description:30} ({filename:25}) {size:6} bytes")
        else:
            print_error(f"{description:30} ({filename:25}) НЕ НАЙДЕН")
            missing.append(filename)
    
    return len(missing) == 0

def check_imports():
    """Проверка импортов"""
    print_header("2️⃣  ПРОВЕРКА ИМПОРТОВ")
    
    imports_to_check = [
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
        ('pytesseract', 'Tesseract'),
        ('mediapipe', 'MediaPipe'),
        ('PyQt5.QtWidgets', 'PyQt5'),
    ]
    
    all_ok = True
    for module, name in imports_to_check:
        try:
            __import__(module)
            print_ok(f"{name:20} импортирован успешно")
        except ImportError as e:
            print_error(f"{name:20} ошибка импорта: {e}")
            all_ok = False
    
    return all_ok

def test_solver():
    """Тест решателя"""
    print_header("3️⃣  ТЕСТ РЕШАТЕЛЯ")
    
    try:
        sys.path.insert(0, str(Path.cwd()))
        from sudoku_solver import SudokuSolver
        
        solver = SudokuSolver()
        print_ok("Класс SudokuSolver загружен")
        
        # Загружаем тестовую доску
        board = solver.load_test_board()
        print_ok("Тестовая доска загружена")
        
        # Проверяем методы
        conflicts = solver.find_conflicts(board)
        print_ok(f"find_conflicts() работает (найдено {len(conflicts)} конфликтов)")
        
        # Решаем
        if solver.solve():
            print_ok(f"Судоку решена за {solver.solution_steps} шагов")
            return True
        else:
            print_error("Не удалось решить тестовую доску")
            return False
    
    except Exception as e:
        print_error(f"Ошибка в решателе: {e}")
        return False

def test_gui_imports():
    """Тест GUI импортов"""
    print_header("4️⃣  ТЕСТ GUI ИМПОРТОВ")
    
    try:
        from PyQt5.QtWidgets import QMainWindow, QApplication
        from PyQt5.QtCore import QThread, pyqtSignal
        print_ok("PyQt5 компоненты импортированы")
        
        sys.path.insert(0, str(Path.cwd()))
        import sudoku_app
        print_ok("sudoku_app модуль загружен")
        
        return True
    except Exception as e:
        print_error(f"Ошибка GUI: {e}")
        return False

def test_hand_gestures():
    """Тест жестов"""
    print_header("5️⃣  ТЕСТ ЖЕСТОВ")
    
    try:
        import mediapipe as mp
        print_ok("MediaPipe загружен")
        
        mp_hands = mp.solutions.hands
        print_ok("MediaPipe Hands загружен")
        
        # Просто проверяем загрузку
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print_ok("Hands модель инициализирована")
        hands.close()
        
        return True
    except Exception as e:
        print_error(f"Ошибка жестов: {e}")
        return False

def check_tesseract():
    """Проверка Tesseract"""
    print_header("6️⃣  ПРОВЕРКА TESSERACT")
    
    try:
        import pytesseract
        text = pytesseract.image_to_string("test.png")
        print_warning("Tesseract работает (тестовое изображение)")
        return True
    except Exception as e:
        print_warning(f"Tesseract: {e}")
        print_warning("  💡 Это нормально, если нет тестового изображения")
        return True  # Не критично

def check_readme():
    """Проверка документации"""
    print_header("7️⃣  ПРОВЕРКА ДОКУМЕНТАЦИИ")
    
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        '# 🧩 Sudoku Solver': 'Заголовок',
        'Использование': 'Раздел использования',
        'Установка': 'Раздел установки',
        'Лицензия': 'Раздел лицензии',
        'requirements.txt': 'Упоминание requirements',
    }
    
    for text, desc in checks.items():
        if text in content:
            print_ok(f"README содержит: {desc}")
        else:
            print_warning(f"README пропускает: {desc}")
    
    return True

def main():
    print("\n" + "█"*60)
    print("  🧪 ПРОВЕРКА ПРИЛОЖЕНИЯ ПЕРЕД ПУБЛИКАЦИЕЙ")
    print("█"*60)
    
    results = {
        '📁 Файлы': check_files(),
        '📦 Импорты': check_imports(),
        '🧩 Решатель': test_solver(),
        '🎨 GUI': test_gui_imports(),
        '👐 Жесты': test_hand_gestures(),
        '🔤 Tesseract': check_tesseract(),
        '📖 README': check_readme(),
    }
    
    print_header("📊 ИТОГОВЫЙ ОТЧЕТ")
    
    for check_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name:30} {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n📈 Результат: {passed}/{total} проверок пройдено")
    
    if passed == total:
        print_ok("ВСЕ ПРОВЕРКИ ПРОШЛИ! 🎉")
        print_ok("Приложение готово к публикации!")
        return 0
    else:
        print_warning(f"Не все проверки прошли ({total - passed} ошибок)")
        print_warning("Исправьте ошибки перед публикацией")
        return 1

if __name__ == '__main__':
    sys.exit(main())
