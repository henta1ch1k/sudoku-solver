#!/usr/bin/env python3
"""
Скрипт сборки для PyInstaller
Собирает приложение в один exe/app/bin файл

Использование:
    python build.py

Результат будет в папке 'dist/'
"""

import PyInstaller.__main__
import sys
import os

# Параметры сборки
APP_NAME = "Sudoku Solver"
MAIN_SCRIPT = "sudoku_app.py"

# Путь к иконке (если есть)
ICON_PATH = None  # Укажите путь к .ico файлу если хотите

def build_app():
    """Собрать приложение"""
    
    args = [
        MAIN_SCRIPT,
        f'--name={APP_NAME}',
        '--onefile',  # Один exe файл
        '--windowed',  # Без окна консоли
        '--add-data=.:.',  # Включить текущую папку
    ]
    
    if ICON_PATH and os.path.exists(ICON_PATH):
        args.append(f'--icon={ICON_PATH}')
    
    # На Linux/Mac может потребоваться
    if sys.platform in ['linux', 'darwin']:
        args.append('--collect-all=cv2')
        args.append('--collect-all=mediapipe')
    
    print(f"🔨 Собираю {APP_NAME}...")
    print(f"   Параметры: {args}")
    print("-" * 60)
    
    PyInstaller.__main__.run(args)
    
    print("-" * 60)
    print("✅ Сборка завершена!")
    print(f"📦 Результат в папке: ./dist/")

if __name__ == '__main__':
    build_app()
