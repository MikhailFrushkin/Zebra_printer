import os
import sys

import qdarkstyle
from PyQt5.QtCore import Qt, QSizeF
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QLabel, QComboBox, QDoubleSpinBox, QFileDialog,
                             QWidget, QMessageBox, QGroupBox, QSpinBox, QSplitter, QProgressDialog)
from loguru import logger

from utils.ratio_image_file import add_padding_to_aspect_ratio


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
        self.setup_shortcuts()
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

        # Количество копий (вынесено отдельно вверх)
        copies_group = QGroupBox("Количество копий")
        copies_layout = QHBoxLayout()
        copies_layout.addWidget(QLabel("Копий:"))
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 99)
        self.copies_spin.setValue(1)
        copies_layout.addWidget(self.copies_spin)
        copies_group.setLayout(copies_layout)
        left_layout.addWidget(copies_group)

        # Группа параметров печати
        params_group = QGroupBox("Пользовательские параметры печати")
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

        # Кнопка печати выбранного изображения (перенесена в эту группу)
        self.print_selected_btn = QPushButton("Печать")
        self.print_selected_btn.clicked.connect(lambda: self.print_images())
        params_layout.addWidget(self.print_selected_btn)

        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)

        # Блок 1: Печать по соотношению сторон
        aspect_group = QGroupBox("Печать по соотношению сторон")
        aspect_layout = QVBoxLayout()

        # Выбор соотношения сторон
        aspect_ratio_layout = QHBoxLayout()
        aspect_ratio_layout.addWidget(QLabel("Соотношение:"))
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["16:9", "4:3", "1:1", "9:16", "3:4", "21:9", "custom"])
        aspect_ratio_layout.addWidget(self.aspect_combo)
        aspect_layout.addLayout(aspect_ratio_layout)

        # Поля для пользовательского соотношения
        self.custom_aspect_frame = QWidget()
        custom_aspect_layout = QHBoxLayout(self.custom_aspect_frame)
        custom_aspect_layout.addWidget(QLabel("Ширина:"))
        self.custom_aspect_width = QSpinBox()
        self.custom_aspect_width.setRange(1, 100)
        self.custom_aspect_width.setValue(16)
        custom_aspect_layout.addWidget(self.custom_aspect_width)

        custom_aspect_layout.addWidget(QLabel("Высота:"))
        self.custom_aspect_height = QSpinBox()
        self.custom_aspect_height.setRange(1, 100)
        self.custom_aspect_height.setValue(9)
        custom_aspect_layout.addWidget(self.custom_aspect_height)
        aspect_layout.addWidget(self.custom_aspect_frame)
        self.custom_aspect_frame.hide()

        # Кнопка печати по соотношению сторон
        self.print_aspect_btn = QPushButton("Печать по соотношению")
        self.print_aspect_btn.clicked.connect(self.print_by_aspect_ratio)
        aspect_layout.addWidget(self.print_aspect_btn)

        aspect_group.setLayout(aspect_layout)
        left_layout.addWidget(aspect_group)

        # Блок 2: Печать по конкретным размерам
        size_group = QGroupBox("Печать по размерам")
        size_layout = QVBoxLayout()

        # Поля для ввода размеров
        size_input_layout = QHBoxLayout()
        size_input_layout.addWidget(QLabel("Ширина:"))
        self.size_width = QSpinBox()
        self.size_width.setRange(1, 10000)
        self.size_width.setValue(800)
        size_input_layout.addWidget(self.size_width)

        size_input_layout.addWidget(QLabel("Высота:"))
        self.size_height = QSpinBox()
        self.size_height.setRange(1, 10000)
        self.size_height.setValue(600)
        size_input_layout.addWidget(self.size_height)
        size_layout.addLayout(size_input_layout)

        # Кнопка печати по размерам
        self.print_size_btn = QPushButton("Печать по размерам")
        self.print_size_btn.clicked.connect(self.print_by_size)
        size_layout.addWidget(self.print_size_btn)

        size_group.setLayout(size_layout)
        left_layout.addWidget(size_group)

        # Кнопки управления изображениями
        self.add_images_btn = QPushButton("Добавить изображения")
        self.add_images_btn.clicked.connect(self.add_images)
        left_layout.addWidget(self.add_images_btn)

        self.remove_image_btn = QPushButton("Удалить выбранное")
        self.remove_image_btn.clicked.connect(self.remove_selected_image)
        left_layout.addWidget(self.remove_image_btn)

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
        self.aspect_combo.currentTextChanged.connect(self.on_aspect_combo_changed)

    def on_aspect_combo_changed(self, text):
        """Показывает/скрывает поля для пользовательского соотношения"""
        if text == "custom":
            self.custom_aspect_frame.show()
        else:
            self.custom_aspect_frame.hide()

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

    def get_aspect_ratio(self):
        """Получает выбранное соотношение сторон"""
        aspect_text = self.aspect_combo.currentText()
        if aspect_text == "custom":
            width = self.custom_aspect_width.value()
            height = self.custom_aspect_height.value()
            return f"{width}:{height}"
        return aspect_text

    def print_by_aspect_ratio(self):
        """Печать с учетом соотношения сторон с прогресс-баром"""
        try:
            if not self.images_list.selectedItems():
                QMessageBox.warning(self, "Ошибка", "Не выбрано изображение для печати!")
                return

            items_to_print = self.images_list.selectedItems()
            total = len(items_to_print)

            progress = QProgressDialog("Печать изображений...", "Отмена", 0, total, self)
            progress.setWindowTitle("Печать")
            progress.setWindowModality(Qt.WindowModal)

            aspect_ratio = self.get_aspect_ratio()

            for i, item in enumerate(items_to_print):
                if progress.wasCanceled():
                    break

                progress.setValue(i)
                progress.setLabelText(f"Обработка изображения {i + 1} из {total}")

                image_path = item.text()
                new_image = add_padding_to_aspect_ratio(image_path, aspect_ratio=aspect_ratio)
                self.print_images_ratio(new_image)

            progress.setValue(total)

        except Exception as ex:
            logger.error(f"Ошибка: {ex}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось обработать изображение: {str(ex)}")

    def print_by_size(self):
        """Печать с учетом конкретных размеров"""
        if not self.images_list.selectedItems():
            QMessageBox.warning(self, "Ошибка", "Не выбрано изображение для печати!")
            return

        width = self.size_width.value()
        height = self.size_height.value()
        try:
            items_to_print = self.images_list.selectedItems()
            for item in items_to_print:
                image_path = item.text()
                new_image = add_padding_to_aspect_ratio(image_path, output_size=(int(width), int(height)))
                self.print_images_ratio(new_image)
        except Exception as ex:
            logger.error(ex)

    def print_images_ratio(self, image):
        """Печать обработанного изображения с учетом соотношения сторон"""
        try:
            if self.printer_combo.count() == 0:
                QMessageBox.warning(self, "Ошибка", "Не выбран принтер!")
                return

            printer_info = self.printer_combo.currentData()
            if not printer_info:
                QMessageBox.warning(self, "Ошибка", "Не удалось получить информацию о принтере!")
                return

            printer = QPrinter(printer_info)
            printer.setFullPage(True)
            copies = self.copies_spin.value()
            printer.setCopyCount(copies)

            # Установка размера бумаги на основе обработанного изображения
            if hasattr(image, 'size'):
                width, height = image.size
                printer.setPaperSize(QSizeF(width / 300 * 25.4, height / 300 * 25.4), QPrinter.Millimeter)

            painter = QPainter()
            if not painter.begin(printer):
                QMessageBox.warning(self, "Ошибка", "Не удалось начать печать!")
                return

            try:
                # Конвертируем PIL Image в QImage если нужно
                if hasattr(image, 'mode'):  # Это PIL Image
                    if image.mode == 'RGB':
                        qimage = QImage(image.tobytes(), image.width, image.height,
                                        image.width * 3, QImage.Format_RGB888)
                    else:
                        image = image.convert('RGB')
                        qimage = QImage(image.tobytes(), image.width, image.height,
                                        image.width * 3, QImage.Format_RGB888)
                else:
                    qimage = image  # Уже QImage

                painter.drawImage(0, 0, qimage)
                painter.end()

                logger.info("Печать завершена успешно")
                QMessageBox.information(self, "Успех", "Печать завершена!")

            except Exception as e:
                painter.end()
                raise e

        except Exception as e:
            logger.error(f"Ошибка при печати: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при печати: {str(e)}")

    def print_images(self):
        if self.images_list.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет изображений для печати!")
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

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QShortcut

        # Ctrl+P - печать
        QShortcut(QKeySequence("Ctrl+P"), self, self.print_images)
        # Ctrl+A - добавить изображения
        QShortcut(QKeySequence("Ctrl+A"), self, self.add_images)
        # Delete - удалить выбранное
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_image)

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = PrintApp()
    window.show()
    sys.exit(app.exec_())