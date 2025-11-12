#!/usr/bin/env python3
"""
Скрипт для автоматической загрузки на GitHub
Этот скрипт поможет вам загрузить проект на GitHub за один раз

Использование:
    python publish_to_github.py
"""

import subprocess
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Запускает команду и показывает результат"""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print(f"{'='*60}")
    
    print(f"▶️  {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"❌ Ошибка при выполнении команды!")
        return False
    return True

def main():
    print("\n" + "█"*60)
    print("  🚀 ЗАГРУЗКА СУДОКУ РЕШАТЕЛЯ НА GITHUB")
    print("█"*60)
    
    # Предварительные проверки
    print("\n" + "="*60)
    print("  📋 ПРЕДВАРИТЕЛЬНЫЕ ПРОВЕРКИ")
    print("="*60)
    
    if not Path('.git').exists():
        print("❌ Git репозиторий не инициализирован!")
        print("\nВыполните первый раз:")
        print("  git init")
        print("  git remote add origin https://github.com/yourusername/sudoku-solver.git")
        print("\nЗатем запустите этот скрипт снова.")
        return
    
    print("✅ Git репозиторий найден")
    
    # Проверка remote
    result = subprocess.run("git remote get-url origin", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Remote URL: {result.stdout.strip()}")
    else:
        print("❌ Remote URL не установлен!")
        return
    
    # Шаг 1: Добавить все файлы
    run_command("git add .", "📁 ШАГ 1: ДОБАВЛЕНИЕ ФАЙЛОВ")
    
    # Шаг 2: Создать коммит
    print("\n" + "="*60)
    print("  💾 ШАГ 2: СОЗДАНИЕ КОММИТА")
    print("="*60)
    
    commit_msg = input("Введите сообщение коммита (по умолчанию 'Initial commit'): ").strip()
    if not commit_msg:
        commit_msg = "Initial commit: Sudoku Solver with GUI and hand gesture recognition"
    
    run_command(f'git commit -m "{commit_msg}"', f"Коммит: {commit_msg}")
    
    # Шаг 3: Переименовать главную ветку
    run_command("git branch -M main", "🌿 ШАГ 3: ПЕРЕИМЕНОВАНИЕ ВЕТКИ В MAIN")
    
    # Шаг 4: Загрузить на GitHub
    run_command("git push -u origin main", "🚀 ШАГ 4: ЗАГРУЗКА НА GITHUB")
    
    # Готово
    print("\n" + "█"*60)
    print("  ✅ УСПЕШНО ЗАГРУЖЕНО НА GITHUB!")
    print("█"*60)
    
    # Показываем информацию
    result = subprocess.run("git remote get-url origin", shell=True, capture_output=True, text=True)
    github_url = result.stdout.strip().replace(".git", "")
    
    print(f"""
📦 Ваш репозиторий: {github_url}

Что дальше:
1️⃣  Откройте ссылку выше в браузере
2️⃣  Добавьте описание проекта (Settings → About)
3️⃣  Добавьте теги (topics):
     - sudoku, solver, opencv, python, pyqt5, gui
4️⃣  Создайте первый Release (Releases → Create a new release)
5️⃣  Поделитесь в Reddit/соцсетях!

Смотрите GITHUB_GUIDE.md для подробной инструкции.
    """)

if __name__ == '__main__':
    main()
