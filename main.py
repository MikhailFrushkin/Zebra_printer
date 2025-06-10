import os
import sys

import qdarkstyle
from PyQt5.QtCore import Qt, QSizeF
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QLabel, QComboBox, QDoubleSpinBox, QFileDialog,
                             QWidget, QMessageBox, QGroupBox, QSpinBox, QSplitter)


class PrintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Printer")
        self.setGeometry(100, 100, 1000, 700)

        self.initUI()
        self.update_printers_list()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # Левая панель (настройки печати)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Группа выбора принтера
        printer_group = QGroupBox("Принтер")
        printer_layout = QVBoxLayout()

        self.printer_combo = QComboBox()
        self.refresh_printers_btn = QPushButton("Обновить список")
        self.refresh_printers_btn.clicked.connect(self.update_printers_list)

        printer_layout.addWidget(self.printer_combo)
        printer_layout.addWidget(self.refresh_printers_btn)
        printer_group.setLayout(printer_layout)
        left_layout.addWidget(printer_group)

        # Группа параметров печати
        params_group = QGroupBox("Параметры печати")
        params_layout = QVBoxLayout()

        # Размеры изображения (в мм)
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Ширина (мм):"))
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 1000)
        self.width_spin.setValue(105)
        size_layout.addWidget(self.width_spin)

        size_layout.addWidget(QLabel("Высота (мм):"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 1000)
        self.height_spin.setValue(55)
        size_layout.addWidget(self.height_spin)
        params_layout.addLayout(size_layout)

        # Отступы (в мм)
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Отступ слева (мм):"))
        self.margin_left_spin = QDoubleSpinBox()
        self.margin_left_spin.setRange(0, 100)
        self.margin_left_spin.setValue(0)
        margin_layout.addWidget(self.margin_left_spin)

        margin_layout.addWidget(QLabel("Отступ сверху (мм):"))
        self.margin_top_spin = QDoubleSpinBox()
        self.margin_top_spin.setRange(0, 100)
        self.margin_top_spin.setValue(0)
        margin_layout.addWidget(self.margin_top_spin)
        params_layout.addLayout(margin_layout)

        # Количество копий
        copies_layout = QHBoxLayout()
        copies_layout.addWidget(QLabel("Количество копий:"))
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 99)
        self.copies_spin.setValue(1)
        copies_layout.addWidget(self.copies_spin)
        params_layout.addLayout(copies_layout)

        # Плотность печати (DPI)
        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("Плотность (DPI):"))
        self.dpi_spin = QDoubleSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(300)
        dpi_layout.addWidget(self.dpi_spin)
        params_layout.addLayout(dpi_layout)

        # Плотность печати для Zebra (только для Zebra)
        self.darkness_layout = QHBoxLayout()
        self.darkness_layout.addWidget(QLabel("Плотность печати (Zebra):"))
        self.darkness_spin = QSpinBox()
        self.darkness_spin.setRange(0, 30)
        self.darkness_spin.setValue(15)
        self.darkness_layout.addWidget(self.darkness_spin)
        params_layout.addLayout(self.darkness_layout)

        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)

        # Кнопки управления
        self.add_images_btn = QPushButton("Добавить изображения")
        self.add_images_btn.clicked.connect(self.add_images)
        left_layout.addWidget(self.add_images_btn)

        self.templates_btn = QPushButton("Добавить шаблоны")
        self.templates_btn.clicked.connect(self.add_templates)
        left_layout.addWidget(self.templates_btn)

        self.remove_image_btn = QPushButton("Удалить выбранное")
        self.remove_image_btn.clicked.connect(self.remove_selected_image)
        left_layout.addWidget(self.remove_image_btn)

        # Кнопка печати всех изображений
        self.print_all_btn = QPushButton("Печать всех")
        self.print_all_btn.clicked.connect(lambda: self.print_images(print_all=True))
        left_layout.addWidget(self.print_all_btn)

        # Кнопка печати выбранного изображения
        self.print_selected_btn = QPushButton("Печать выбранного")
        self.print_selected_btn.clicked.connect(lambda: self.print_images(print_all=False))
        left_layout.addWidget(self.print_selected_btn)

        left_layout.addStretch()

        # Правая панель (список изображений и превью)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Список изображений
        self.images_list = QListWidget()
        self.images_list.setSelectionMode(QListWidget.SingleSelection)
        self.images_list.currentItemChanged.connect(self.show_preview)
        right_layout.addWidget(QLabel("Список изображений:"))
        right_layout.addWidget(self.images_list)

        # Превью изображения
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 400)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        right_layout.addWidget(QLabel("Превью:"))
        right_layout.addWidget(self.preview_label)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        self.printer_combo.currentTextChanged.connect(self.update_zebra_settings_visibility)

    def add_templates(self):
        """Добавляет шаблоны из папки templates в список изображений"""
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")

        if not os.path.exists(templates_dir):
            QMessageBox.warning(self, "Ошибка", "Папка с шаблонами 'templates' не найдена!")
            return

        # Получаем список уже добавленных изображений
        existing_images = [self.images_list.item(i).text() for i in range(self.images_list.count())]

        added_count = 0
        for file_name in os.listdir(templates_dir):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                file_path = os.path.join(templates_dir, file_name)

                # Проверяем, не добавлен ли уже этот шаблон
                if file_path not in existing_images:
                    self.images_list.addItem(file_path)
                    added_count += 1

        if added_count == 0:
            QMessageBox.information(self, "Информация", "Все шаблоны уже добавлены или папка пуста")
        else:
            QMessageBox.information(self, "Успех", f"Добавлено {added_count} шаблонов")

    def update_zebra_settings_visibility(self):
        """Показывает/скрывает настройки плотности для Zebra"""
        printer_name = self.printer_combo.currentText()
        is_zebra = "zebra" in printer_name.lower()
        self.darkness_layout.parent().setVisible(is_zebra)

    def show_preview(self, current_item, previous_item):
        """Показывает превью выбранного изображения"""
        if current_item is None:
            self.preview_label.clear()
            return

        image_path = current_item.text()
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            self.preview_label.setText("Не удалось загрузить изображение")
            return

        scaled_pixmap = pixmap.scaled(
            self.preview_label.width() - 20,
            self.preview_label.height() - 20,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.preview_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.images_list.currentItem():
            self.show_preview(self.images_list.currentItem(), None)

    def update_printers_list(self):
        self.printer_combo.clear()
        printers = QPrinterInfo.availablePrinters()

        if not printers:
            QMessageBox.warning(self, "Ошибка", "Не найдено ни одного принтера!")
            return

        for printer in printers:
            self.printer_combo.addItem(printer.printerName(), printer)

        default_printer = QPrinterInfo.defaultPrinter()
        if default_printer:
            index = self.printer_combo.findText(default_printer.printerName())
            if index >= 0:
                self.printer_combo.setCurrentIndex(index)

        self.update_zebra_settings_visibility()

    def add_images(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)

        if file_dialog.exec_():
            file_names = file_dialog.selectedFiles()
            for file_name in file_names:
                self.images_list.addItem(file_name)

    def remove_selected_image(self):
        for item in self.images_list.selectedItems():
            self.images_list.takeItem(self.images_list.row(item))

    def print_images(self, print_all=True):
        if self.images_list.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет изображений для печати!")
            return

        if not print_all and not self.images_list.selectedItems():
            QMessageBox.warning(self, "Ошибка", "Не выбрано изображение для печати!")
            return

        if self.printer_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Не выбран принтер!")
            return

        printer_info = self.printer_combo.currentData()
        if not printer_info:
            QMessageBox.warning(self, "Ошибка", "Не удалось получить информацию о принтере!")
            return

        printer = QPrinter(printer_info)
        printer.setFullPage(True)

        width_mm = self.width_spin.value()
        height_mm = self.height_spin.value()
        margin_left_mm = self.margin_left_spin.value()
        margin_top_mm = self.margin_top_spin.value()
        dpi = int(self.dpi_spin.value())
        copies = self.copies_spin.value()

        printer_name = self.printer_combo.currentText()
        if "zebra" in printer_name.lower():
            darkness = self.darkness_spin.value()

        printer.setPaperSize(QSizeF(width_mm, height_mm), QPrinter.Millimeter)
        printer.setResolution(dpi)
        printer.setCopyCount(copies)

        painter = None
        try:
            items_to_print = []
            if print_all:
                items_to_print = [self.images_list.item(i) for i in range(self.images_list.count())]
            else:
                items_to_print = self.images_list.selectedItems()

            for item in items_to_print:
                image_path = item.text()
                image = QImage(image_path)

                if image.isNull():
                    QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить изображение: {image_path}")
                    continue

                scaled_image = image.scaled(
                    int(width_mm * dpi / 25.4),
                    int(height_mm * dpi / 25.4),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )

                if not painter:
                    painter = QPainter()
                    if not painter.begin(printer):
                        QMessageBox.warning(self, "Ошибка", "Не удалось начать печать!")
                        return

                x_offset = int(margin_left_mm * dpi / 25.4)
                y_offset = int(margin_top_mm * dpi / 25.4)
                painter.drawImage(x_offset, y_offset, scaled_image)

                if item != items_to_print[-1]:
                    printer.newPage()

            if painter:
                painter.end()

            QMessageBox.information(self, "Успех", "Печать завершена!")
        except Exception as e:
            if painter:
                painter.end()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при печати: {str(e)}")


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = PrintApp()
    window.show()
    sys.exit(app.exec_())
