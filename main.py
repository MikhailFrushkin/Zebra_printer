import ctypes
import os
import sys
import time

from PyQt5.QtCore import Qt, QSizeF, QRect
from PyQt5.QtGui import QPixmap, QImage, QPainter, QIcon, QMouseEvent, QFontMetrics, QFont
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QLabel, QComboBox, QDoubleSpinBox, QFileDialog,
                             QWidget, QMessageBox, QGroupBox, QSpinBox, QSplitter, QScrollArea, QGridLayout,
                             QRadioButton, QButtonGroup, QCheckBox, QTextEdit, QFontComboBox, QDialog)
from loguru import logger

from styles import apply_styles, setup_button_styles
from utils.utils import get_resource_path


class ClickableLabel(QLabel):
    """QLabel с поддержкой кликов"""

    def __init__(self, template_path=None, main_window=None, parent=None):
        super().__init__(parent)
        self.template_path = template_path
        self.main_window = main_window
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent):
        """Обработка клика мыши"""
        if event.button() == Qt.LeftButton and self.template_path and self.main_window:
            # Вызываем метод главного окна напрямую
            self.main_window.on_template_image_clicked(self.template_path)
        super().mousePressEvent(event)


class TextPrintDialog(QDialog):
    """Диалоговое окно для ввода и печати текста"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Печать текста")
        self.setModal(True)
        self.setFixedSize(500, 400)

        self.parent_window = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Ввод текста
        layout.addWidget(QLabel("Введите текст для печати:"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите текст здесь...")
        self.text_edit.setMaximumHeight(150)
        layout.addWidget(self.text_edit)

        # Настройки шрифта
        font_group = QGroupBox("Настройки шрифта")
        font_layout = QVBoxLayout()

        # Выбор шрифта
        font_select_layout = QHBoxLayout()
        font_select_layout.addWidget(QLabel("Шрифт:"))
        self.font_combo = QFontComboBox()
        font_select_layout.addWidget(self.font_combo)
        font_layout.addLayout(font_select_layout)

        # Размер шрифта
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Размер шрифта (пт):"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 100)
        self.font_size_spin.setValue(56)
        size_layout.addWidget(self.font_size_spin)
        font_layout.addLayout(size_layout)

        # Жирный текст
        self.bold_checkbox = QCheckBox("Жирный текст")
        font_layout.addWidget(self.bold_checkbox)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Кнопки
        button_layout = QHBoxLayout()
        self.print_btn = QPushButton("Печать")
        self.print_btn.clicked.connect(self.create_text_image)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

    def create_text_image(self):
        """Создание изображения с текстом"""
        text = self.text_edit.toPlainText().strip()
        logger.debug(text)
        if not text:
            QMessageBox.warning(self, "Ошибка", "Введите текст для печати!")
            return

        # Получаем параметры из родительского окна
        width_mm = self.parent_window.width_spin.value()
        height_mm = self.parent_window.height_spin.value()
        dpi = int(self.parent_window.dpi_spin.value())

        # Преобразуем мм в пиксели
        width_px = int(width_mm * dpi / 25.4)
        height_px = int(height_mm * dpi / 25.4)

        # Создаем изображение
        image = QImage(width_px, height_px, QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QPainter(image)

        # Настройки шрифта
        font = QFont(self.font_combo.currentFont())
        font.setPointSize(self.font_size_spin.value())
        font.setBold(self.bold_checkbox.isChecked())
        painter.setFont(font)

        # Параметры для расчета переноса строк
        margin = int(10 * dpi / 25.4)  # Отступ 10 мм
        text_rect = QRect(margin, margin,
                          width_px - 2 * margin,
                          height_px - 2 * margin)

        # Автоподбор размера шрифта
        self.adjust_font_size(painter, text, text_rect)

        # Рисуем текст с переносом по словам
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, text)
        painter.end()

        # Сохраняем временное изображение
        temp_dir = os.path.join(os.path.expanduser("~"), ".image_printer_temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, f"text_{str(time.time())}.png")

        if image.save(temp_file, "PNG"):
            # Добавляем в список изображений
            self.parent_window.images_list.addItem(temp_file)
            self.parent_window.images_list.setCurrentRow(self.parent_window.images_list.count() - 1)
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось создать изображение с текстом!")

    def adjust_font_size(self, painter, text, text_rect):
        """Автоподбор размера шрифта для вписывания текста в область"""
        font = painter.font()
        # Максимальная ширина строки
        max_width = text_rect.width()
        # Разбиваем текст на слова
        words = text.split()

        # Пытаемся найти оптимальный размер шрифта
        for size in range(font.pointSize(), 6, -1):
            font.setPointSize(size)
            painter.setFont(font)
            font_metrics = QFontMetrics(font)

            current_line = []
            lines = []
            # Пробуем разбить текст на строки
            for word in words:
                test_line = (current_line + [word]) if current_line else [word]
                test_text = ' '.join(test_line)

                if font_metrics.horizontalAdvance(test_text) <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(' '.join(current_line))

            # Проверяем, помещается ли текст по высоте
            total_height = len(lines) * font_metrics.lineSpacing()
            if total_height <= text_rect.height():
                break



class PrintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Printer")
        self.setGeometry(100, 100, 1800, 700)  # Увеличиваем ширину для новой панели
        self.setWindowOpacity(0.99)
        self.selected_template = None
        self.template_buttons_group = QButtonGroup(self)
        self.template_buttons_group.setExclusive(True)
        self.initUI()
        self.background_image = QPixmap(get_resource_path("фон.jpg"))
        self.update_printers_list()
        self.load_templates()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setup_shortcuts()

        main_layout = QHBoxLayout(central_widget)

        # Главный сплиттер с тремя панелями
        main_splitter = QSplitter(Qt.Horizontal)

        # Левая панель (настройки печати)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Группа выбора принтера
        printer_group = QGroupBox()
        printer_layout = QVBoxLayout()

        self.printer_combo = QComboBox()

        printer_layout.addWidget(self.printer_combo)
        printer_group.setLayout(printer_layout)
        left_layout.addWidget(printer_group)

        # Количество копий (вынесено отдельно вверх)
        copies_group = QGroupBox()
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
        self.width_spin.setValue(100)
        size_layout.addWidget(self.width_spin)

        size_layout.addWidget(QLabel("Высота (мм):"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 1000)
        self.height_spin.setValue(75)
        size_layout.addWidget(self.height_spin)
        params_layout.addLayout(size_layout)

        # Отступы (в мм)
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Отступ слева (мм):"))
        self.margin_left_spin = QDoubleSpinBox()
        self.margin_left_spin.setRange(0, 100)
        self.margin_left_spin.setValue(1)
        margin_layout.addWidget(self.margin_left_spin)

        margin_layout.addWidget(QLabel("Отступ сверху (мм):"))
        self.margin_top_spin = QDoubleSpinBox()
        self.margin_top_spin.setRange(0, 100)
        self.margin_top_spin.setValue(1)
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
        self.darkness_spin.setValue(30)
        self.darkness_layout.addWidget(self.darkness_spin)
        params_layout.addLayout(self.darkness_layout)

        # Чекбокс "Сохранить пропорции"
        self.aspect_ratio_checkbox = QCheckBox("Сохранить пропорции")
        self.aspect_ratio_checkbox.setChecked(False)
        params_layout.addWidget(self.aspect_ratio_checkbox)

        # Кнопка печати выбранного изображения
        self.print_selected_btn = QPushButton("Печать")
        self.print_selected_btn.clicked.connect(lambda: self.print_images())
        params_layout.addWidget(self.print_selected_btn)
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)

        # В левой панели после существующих кнопок добавляем:
        self.print_text_btn = QPushButton("Печать текста")
        self.print_text_btn.clicked.connect(self.open_text_print_dialog)
        left_layout.addWidget(self.print_text_btn)

        # Кнопки управления изображениями
        self.add_images_btn = QPushButton("Добавить изображения")
        self.add_images_btn.clicked.connect(self.add_images)
        left_layout.addWidget(self.add_images_btn)

        self.remove_image_btn = QPushButton("Удалить выбранное")
        self.remove_image_btn.clicked.connect(self.remove_selected_image)
        left_layout.addWidget(self.remove_image_btn)

        left_layout.addStretch()

        # Центральная панель (список изображений и превью)
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        # Список изображений
        self.images_list = QListWidget()
        self.images_list.setSelectionMode(QListWidget.SingleSelection)
        self.images_list.currentItemChanged.connect(self.show_preview)
        center_layout.addWidget(self.images_list)

        # Превью изображения
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(300, 300)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.setObjectName("previewLabel")

        center_layout.addWidget(self.preview_label)

        # Правая панель (шаблоны)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Область прокрутки для шаблонов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.templates_layout = QGridLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        right_layout.addWidget(scroll_area)

        # Добавляем все панели в главный сплиттер
        left_panel.setObjectName("leftPanel")
        center_panel.setObjectName("centerPanel")
        right_panel.setObjectName("rightPanel")

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(center_panel)
        main_splitter.addWidget(right_panel)

        # Устанавливаем пропорции
        main_splitter.setSizes([300, 400, 300])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setStretchFactor(2, 1)

        main_layout.addWidget(main_splitter)

        self.printer_combo.currentTextChanged.connect(self.update_zebra_settings_visibility)
        # Подключаем обработчик выбора шаблонов
        self.template_buttons_group.buttonClicked.connect(self.on_template_selected)

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
        # Ctrl+R - обновить шаблоны
        QShortcut(QKeySequence("Ctrl+R"), self, self.load_templates)

    def load_templates(self):
        """Загрузка шаблонов из папки templates"""
        # Очищаем предыдущие шаблоны
        for i in reversed(range(self.templates_layout.count())):
            widget = self.templates_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        templates_dir = get_resource_path("templates")
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            return

        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        templates = []

        for file in os.listdir(templates_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                templates.append(os.path.join(templates_dir, file))

        if not templates:
            no_templates_label = QLabel("Нет шаблонов в папке 'templates'")
            self.templates_layout.addWidget(no_templates_label, 0, 0)
            return

        row, col = 0, 0
        max_cols = 2
        for template_path in templates:
            # Создаем контейнер для шаблона
            template_widget = QWidget()
            template_widget.setObjectName("templateWidget")
            template_layout = QVBoxLayout(template_widget)
            template_layout.setSpacing(5)
            template_layout.setContentsMargins(5, 5, 5, 5)

            # Превью шаблона (кликабельное)
            pixmap = QPixmap(template_path)
            if not pixmap.isNull():
                # Масштабируем превью
                scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview_label = ClickableLabel(template_path, self, template_widget)
                preview_label.setPixmap(scaled_pixmap)
                preview_label.setAlignment(Qt.AlignCenter)
                preview_label.setObjectName("templatePreview")
                preview_label.template_path = template_path

                # Добавляем эффект при наведении
                preview_label.setStyleSheet("""
                    QLabel#templatePreview {
                        border: 2px solid transparent;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QLabel#templatePreview:hover {
                        border: 2px solid #0078d7;
                        background-color: #f0f8ff;
                    }
                """)

                template_layout.addWidget(preview_label)

            # Радиокнопка для выбора
            radio_btn = QRadioButton(os.path.basename(template_path))
            radio_btn.template_path = template_path
            radio_btn.setStyleSheet("""
                QRadioButton {
                    spacing: 5px;
                    padding: 2px;
                }
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            self.template_buttons_group.addButton(radio_btn)
            template_layout.addWidget(radio_btn)

            # Добавляем в сетку
            self.templates_layout.addWidget(template_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def paintEvent(self, event):
        painter = QPainter(self)
        # Растягиваем изображение на весь фон
        painter.drawPixmap(self.rect(), self.background_image)
        super().paintEvent(event)

    def on_template_image_clicked(self, template_path):
        """Обработка клика на изображение шаблона"""
        logger.info(f"Клик на шаблон: {template_path}")

        # Устанавливаем соответствующую радиокнопку
        for button in self.template_buttons_group.buttons():
            if hasattr(button, 'template_path') and button.template_path == template_path:
                button.setChecked(True)
                self.on_template_selected(button)
                break

    def on_template_selected(self, button):
        """Обработка выбора шаблона"""
        self.selected_template = button.template_path
        logger.info(f"Выбран шаблон: {self.selected_template}")

        # Добавляем выбранный шаблон в список изображений
        if self.selected_template:
            # Очищаем предыдущий выбор
            self.images_list.clear()
            self.images_list.addItem(self.selected_template)
            self.images_list.setCurrentRow(0)

            # Показываем превью
            self.show_preview(self.images_list.currentItem())

    def on_aspect_combo_changed(self, text):
        """Показывает/скрывает поля для пользовательского соотношения"""
        if text == "Указать":
            self.custom_aspect_frame.show()
        else:
            self.custom_aspect_frame.hide()

    def update_zebra_settings_visibility(self):
        """Показывает/скрывает настройки плотности для Zebra"""
        printer_name = self.printer_combo.currentText()
        is_zebra = "zebra" in printer_name.lower()
        # Получаем родительский layout и показываем/скрываем его
        if hasattr(self, 'darkness_layout'):
            for i in range(self.darkness_layout.count()):
                widget = self.darkness_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(is_zebra)

    def show_preview(self, current_item):
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
            self.show_preview(self.images_list.currentItem())

    def update_printers_list(self):
        """Обновление списка доступных принтеров"""
        try:
            self.printer_combo.clear()

            # Получаем список принтеров
            printers = QPrinterInfo.availablePrinters()
            logger.debug(f"Найдено принтеров: {len(printers)}")

            if not printers:
                QMessageBox.warning(self, "Ошибка", "Не найдено ни одного принтера!")
                # Добавляем заглушку
                self.printer_combo.addItem("Принтеры не найдены", "")
                return

            # Добавляем принтеры в комбобокс
            for printer in printers:
                printer_name = printer.printerName()
                logger.debug(f"Добавляем принтер: {printer_name}")

                # Просто добавляем имя принтера, без userData
                self.printer_combo.addItem(printer_name)

            # Устанавливаем принтер по умолчанию
            default_printer = QPrinterInfo.defaultPrinter()
            if default_printer and not default_printer.isNull():
                default_name = default_printer.printerName()
                index = self.printer_combo.findText(default_name)
                if index >= 0:
                    self.printer_combo.setCurrentIndex(index)
                    logger.debug(f"Установлен принтер по умолчанию: {default_name}")

            self.update_zebra_settings_visibility()

        except Exception as e:
            logger.error(f"Ошибка при обновлении списка принтеров: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список принтеров: {str(e)}")

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

    def print_images(self):
        if self.images_list.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет изображений для печати!")
            return

        if self.printer_combo.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Не выбран принтер!")
            return

        try:
            # Получаем имя выбранного принтера
            printer_name = self.printer_combo.currentText()
            logger.debug(f"Выбран принтер: {printer_name}")

            # Создаем QPrinterInfo по имени
            printer_info = QPrinterInfo.printerInfo(printer_name)
            if printer_info.isNull():
                QMessageBox.warning(self, "Ошибка", f"Принтер '{printer_name}' не найден!")
                return

            printer = QPrinter(printer_info)
            printer.setFullPage(True)

            width_mm = self.width_spin.value()
            height_mm = self.height_spin.value()
            margin_left_mm = self.margin_left_spin.value()
            margin_top_mm = self.margin_top_spin.value()
            dpi = int(self.dpi_spin.value())
            copies = self.copies_spin.value()
            keep_aspect_ratio = self.aspect_ratio_checkbox.isChecked()

            printer_name_lower = printer_name.lower()
            if "zebra" in printer_name_lower:
                darkness = self.darkness_spin.value()
                # Здесь можно добавить настройки для Zebra

            printer.setPaperSize(QSizeF(width_mm, height_mm), QPrinter.Millimeter)
            printer.setResolution(dpi)
            printer.setCopyCount(copies)

            painter = None
            try:
                items_to_print = self.images_list.selectedItems()
                if not items_to_print:
                    items_to_print = [self.images_list.item(i) for i in range(self.images_list.count())]

                for item in items_to_print:
                    image_path = item.text()
                    image = QImage(image_path)

                    if image.isNull():
                        QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить изображение: {image_path}")
                        continue

                    # РАСЧЕТ РАЗМЕРОВ В ПИКСЕЛЯХ
                    target_width_px = int(width_mm * dpi / 25.4)
                    target_height_px = int(height_mm * dpi / 25.4)
                    margin_left_px = int(margin_left_mm * dpi / 25.4)
                    margin_top_px = int(margin_top_mm * dpi / 25.4)

                    if keep_aspect_ratio:
                        # СОХРАНЕНИЕ ПРОПОРЦИЙ С ЦЕНТРИРОВАНИЕМ
                        # Вычисляем соотношение сторон исходного изображения
                        source_aspect = image.width() / image.height()
                        target_aspect = target_width_px / target_height_px

                        if source_aspect > target_aspect:
                            # Изображение шире, чем целевая область - ограничиваем по ширине
                            scaled_width = target_width_px
                            scaled_height = int(target_width_px / source_aspect)
                        else:
                            # Изображение выше, чем целевая область - ограничиваем по высоте
                            scaled_height = target_height_px
                            scaled_width = int(target_height_px * source_aspect)

                        # Масштабируем изображение с сохранением пропорций
                        scaled_image = image.scaled(
                            scaled_width,
                            scaled_height,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )

                        # Вычисляем координаты для центрирования
                        x_offset = margin_left_px + (target_width_px - scaled_width) // 2
                        y_offset = margin_top_px + (target_height_px - scaled_height) // 2

                        if not painter:
                            painter = QPainter()
                            if not painter.begin(printer):
                                QMessageBox.warning(self, "Ошибка", "Не удалось начать печать!")
                                return

                        # Рисуем белый фон
                        painter.fillRect(
                            margin_left_px,
                            margin_top_px,
                            target_width_px,
                            target_height_px,
                            Qt.white
                        )

                        # Рисуем изображение по центру
                        painter.drawImage(x_offset, y_offset, scaled_image)

                    else:
                        # РАСТЯГИВАЕМ ИЗОБРАЖЕНИЕ БЕЗ СОХРАНЕНИЯ ПРОПОРЦИЙ
                        scaled_image = image.scaled(
                            target_width_px,
                            target_height_px,
                            Qt.IgnoreAspectRatio,  # Игнорируем пропорции
                            Qt.SmoothTransformation
                        )

                        if not painter:
                            painter = QPainter()
                            if not painter.begin(printer):
                                QMessageBox.warning(self, "Ошибка", "Не удалось начать печать!")
                                return

                        x_offset = margin_left_px
                        y_offset = margin_top_px
                        painter.drawImage(x_offset, y_offset, scaled_image)

                    if item != items_to_print[-1]:
                        printer.newPage()

                if painter:
                    painter.end()

                QMessageBox.information(self, "Успех", "Печать завершена!")

            except Exception as e:
                if painter:
                    painter.end()
                logger.error(f"Ошибка при печати: {e}")
                QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при печати: {str(e)}")

        except Exception as e:
            logger.error(f"Ошибка при подготовке к печати: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при подготовке к печати: {str(e)}")

    def open_text_print_dialog(self):
        """Открытие диалога печати текста"""
        dialog = TextPrintDialog(self)
        dialog.exec_()


if __name__ == "__main__":
    if sys.platform == "win32":
        myappid = "ZebraLemana 2.0.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(get_resource_path("1.ico")))

    # Применяем стили

    window = PrintApp()
    window.show()

    # Настраиваем стили кнопок после создания окна
    setup_button_styles(window)
    apply_styles(app)

    sys.exit(app.exec_())