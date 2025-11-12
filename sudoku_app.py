#!/usr/bin/env python3
"""
Судоку Решатель - Десктопное приложение с GUI
Распознаёт Судоку из фото и решает их автоматически
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QTextEdit, QTabWidget,
    QProgressBar, QMessageBox, QSplitter
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QScrollArea

from sudoku_solver import SudokuSolver


class SolverThread(QThread):
    """Поток для решения судоку без блокировки UI"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.solver = SudokuSolver()
    
    def run(self):
        try:
            self.progress.emit("📸 Загружаю изображение...")
            board = self.solver.load_board_from_image(self.image_path)
            
            self.progress.emit("🔍 Проверяю конфликты...")
            conflicts = self.solver.find_conflicts(board)
            if conflicts:
                msg = f"⚠ Найдено конфликтов: {len(conflicts)}\n"
                for c in conflicts[:3]:
                    msg += f"  • {c['type']}: число {c['value']}\n"
                self.finished.emit(False, msg)
                return
            
            self.progress.emit("🔄 Решаю судоку...")
            if self.solver.solve():
                self.progress.emit("✅ Решено!")
                self.finished.emit(True, self._format_result())
            else:
                self.finished.emit(False, "❌ Решение не найдено")
        
        except Exception as e:
            self.finished.emit(False, f"❌ Ошибка: {str(e)}")
    
    def _format_result(self):
        """Форматирует результат для вывода"""
        lines = ["📊 СУДОКУ РЕШЕНА!\n"]
        lines.append("=" * 25)
        
        for i, row in enumerate(self.solver.board):
            if i % 3 == 0 and i != 0:
                lines.append("-" * 25)
            
            row_str = ""
            for j, num in enumerate(row):
                if j % 3 == 0 and j != 0:
                    row_str += "| "
                row_str += str(num) + " "
            lines.append(row_str)
        
        lines.append("=" * 25)
        lines.append(f"\nВремя решения: ~{self.solver.solution_steps} шагов")
        
        return "\n".join(lines)


class SudokuApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.solver = None
        self.current_image = None
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Sudoku Solver 🧩")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(self._get_stylesheet())
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Заголовок
        title = QLabel("🧩 SUDOKU SOLVER")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Вкладки
        tabs = QTabWidget()
        
        # Вкладка 1: Загрузка и решение
        tab1 = self._create_solver_tab()
        tabs.addTab(tab1, "📷 Решить из фото")
        
        # Вкладка 2: О приложении
        tab2 = self._create_about_tab()
        tabs.addTab(tab2, "ℹ️ О программе")
        
        main_layout.addWidget(tabs)
    
    def _create_solver_tab(self):
        """Вкладка решения"""
        widget = QWidget()
        layout = QHBoxLayout()
        
        # Левая часть: Загрузка фото
        left_layout = QVBoxLayout()
        
        left_layout.addWidget(QLabel("Загрузить изображение:"))
        
        self.image_label = QLabel("Нет изображения")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px; min-height: 200px;")
        left_layout.addWidget(self.image_label)
        
        btn_load = QPushButton("📁 Выбрать файл")
        btn_load.clicked.connect(self.load_image)
        btn_load.setMinimumHeight(40)
        left_layout.addWidget(btn_load)
        
        btn_camera = QPushButton("📷 С камеры (Ctrl+C)")
        btn_camera.setEnabled(False)  # TODO: добавить поддержку камеры
        btn_camera.setMinimumHeight(40)
        left_layout.addWidget(btn_camera)
        
        btn_solve = QPushButton("🚀 РЕШИТЬ")
        btn_solve.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px;")
        btn_solve.clicked.connect(self.solve_sudoku)
        btn_solve.setMinimumHeight(50)
        left_layout.addWidget(btn_solve)
        
        # Прогресс
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        
        # Правая часть: Результат
        right_layout = QVBoxLayout()
        
        right_layout.addWidget(QLabel("Результат:"))
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Courier", 11))
        self.result_text.setText("Результат будет здесь...")
        right_layout.addWidget(self.result_text)
        
        btn_copy = QPushButton("📋 Копировать результат")
        btn_copy.clicked.connect(self.copy_result)
        btn_copy.setMinimumHeight(35)
        right_layout.addWidget(btn_copy)
        
        btn_export = QPushButton("💾 Сохранить в файл")
        btn_export.clicked.connect(self.export_result)
        btn_export.setMinimumHeight(35)
        right_layout.addWidget(btn_export)
        
        # Сплиттер для левой и правой частей
        splitter = QSplitter(Qt.Horizontal)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        widget.setLayout(layout)
        
        return widget
    
    def _create_about_tab(self):
        """Вкладка информации"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setMarkdown("""
# 🧩 Sudoku Solver

## Возможности:
- ✅ Распознавание Судоку из фотографий (OpenCV + Tesseract OCR)
- ✅ Интеллектуальное решение с эвристиками (MRV)
- ✅ Поддержка изображений любого качества
- ✅ Быстрое решение даже сложных судоку

## Технологии:
- Python 3.7+
- PyQt5 для GUI
- OpenCV для обработки изображений
- MediaPipe для детекции рук (бонус)

## Как использовать:
1. Нажмите "Выбрать файл" и загрузите фото Судоку
2. Нажмите "РЕШИТЬ"
3. Результат появится справа
4. Скопируйте или сохраните результат

## Поддерживаемые форматы:
- PNG, JPG, JPEG, BMP, TIFF

## Автор:
Создано с помощью AI Assistant

## Лицензия:
MIT License - свободен в использовании и модификации
        """)
        layout.addWidget(about_text)
        
        widget.setLayout(layout)
        return widget
    
    def load_image(self):
        """Загрузить изображение"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение Судоку",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.current_image = file_path
            pixmap = QPixmap(file_path)
            
            # Масштабируем для отображения
            scaled_pixmap = pixmap.scaledToWidth(250, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            
            self.status_label.setText(f"📁 Загруженно: {Path(file_path).name}")
    
    def solve_sudoku(self):
        """Решить судоку"""
        if not self.current_image:
            QMessageBox.warning(self, "⚠️ Ошибка", "Сначала загрузите изображение!")
            return
        
        # Запуск в отдельном потоке
        self.solver_thread = SolverThread(self.current_image)
        self.solver_thread.progress.connect(self.update_status)
        self.solver_thread.finished.connect(self.on_solve_finished)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Решаю...")
        self.solver_thread.start()
    
    def update_status(self, message):
        """Обновить статус"""
        self.status_label.setText(message)
    
    def on_solve_finished(self, success, message):
        """Завершение решения"""
        self.progress_bar.setVisible(False)
        self.result_text.setText(message)
        
        if success:
            self.status_label.setText("✅ Решено!")
            QMessageBox.information(self, "✅ Успех", "Судоку успешно решена!")
        else:
            self.status_label.setText("❌ Ошибка при решении")
            QMessageBox.warning(self, "❌ Ошибка", message)
    
    def copy_result(self):
        """Копировать результат"""
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(self.result_text.toPlainText())
        QMessageBox.information(self, "✅ Готово", "Результат скопирован в буфер обмена!")
    
    def export_result(self):
        """Экспортировать результат"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат",
            "",
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.result_text.toPlainText())
            QMessageBox.information(self, "✅ Готово", f"Результат сохранён в {Path(file_path).name}")
    
    def _get_stylesheet(self):
        """CSS стили для приложения"""
        return """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QLabel {
            color: #333;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        QTextEdit {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px;
        }
        QTabWidget::pane {
            border: 1px solid #ddd;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 20px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: white;
        }
        """


def main():
    app = QApplication(sys.argv)
    window = SudokuApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
