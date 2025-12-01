from PyQt5.QtGui import QFont


def apply_styles(app):
    """Применяет стили ко всему приложению"""

    # Основной стиль для приложения
    style = """
    /* Стиль для всех кнопок */
    /* Фон главного окна */
    QMainWindow {
        background: QLinearGradient( x1: 0, y1: 0,
                             x2: 1, y2: 0, 
                            stop: 0 #FFD700,
                            stop: 1 #006400 );
    }
    
    QPushButton {
        background-color: rgba(74, 144, 226, 0.8);  /* Полупрозрачный синий */
        border: 2px solid #4a90e2;
        border-radius: 15px;  /* Закругление углов */
        padding: 12px 20px;  /* Увеличиваем отступы для большего размера */
        color: white;
        font-weight: bold;
        font-size: 16px;
        min-height: 20px;  /* Минимальная высота для больших кнопок */
        max-height: 30px;
    }

    /* Скрыть разделитель сплиттера(разделителя колонок) */
    QSplitter::handle {
        background: transparent;
        width: 0px;
        height: 0px;
        border: none;
    }
    
    QSplitter::handle:hover {
        background: transparent;
    }

    QPushButton:hover {
        background-color: rgba(58, 119, 195, 0.9);  /* Темнее при наведении */
        border: 2px solid #3a77c3;
    }

    QPushButton:pressed {
        background-color: rgba(45, 95, 160, 0.95);  /* Еще темнее при нажатии */
        border: 2px solid #2d5fa0;
    }

    QPushButton:disabled {
        background-color: rgba(180, 180, 180, 0.6);  /* Серый для неактивных */
        border: 2px solid #b4b4b4;
        color: #808080;
    }

    /* Специальные стили для кнопки печати */
    QPushButton#printButton {
        background-color: #3CB371;  /* Зеленый для печати */
        border: 2px solid #2ecc71;
    }

    QPushButton#printButton:hover {
        background-color: rgba(39, 174, 96, 0.9);
        border: 2px solid #27ae60;
    }

    /* Стиль для радиокнопок шаблонов */
    QRadioButton {
        padding: 8px;
        font-size: 14px;
        spacing: 5px;
    }

    QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 2px solid #4a90e2;
    }

    QRadioButton::indicator:checked {
        background-color: #4a90e2;
    }

    /* Стиль для групповых рамок */
    QGroupBox {
        font-weight: bold;
        border: 2px solid #cccccc;
        border-radius: 8px;
        margin-top: 1ex;
        padding-top: 10px;
        background-color: rgba(255, 255, 255, 0.9);
    }

    QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;  /* Центрируем заголовок */
    left: 10px;
    padding: 0 15px 0 5px;
    background-color: rgba(255, 255, 255, 0.9);  /* Фон заголовка */
    border-radius: 4px;  /* Закругление углов */
    }

    /* Стиль для выпадающих списков */
    QComboBox {
        border: 2px solid #cccccc;
        border-radius: 8px;
        padding: 8px;
        background-color: white;
        min-height: 30px;
    }

    QComboBox:editable {
        background: white;
    }

    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 1px;
        border-left-color: #cccccc;
        border-left-style: solid;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }

    /* Стиль для списка изображений */
    QListWidget {
        border: 2px solid #cccccc;
        border-radius: 8px;
        background-color: white;
        alternate-background-color: #f8f8f8;
    }

    QListWidget::item {
        padding: 5px;
        border-bottom: 1px solid #eeeeee;
    }

    QListWidget::item:selected {
        background-color: #4a90e2;
        color: white;
        border-radius: 4px;
    }

    /* Стиль для спинбоксов */
    QSpinBox, QDoubleSpinBox {
        border: 2px solid #cccccc;
        border-radius: 8px;
        padding: 5px;
        background-color: white;
        min-height: 25px;
    }

    /* Стиль для области прокрутки шаблонов */
    QScrollArea {
        border: 1px solid #cccccc;
        border-radius: 8px;
        background-color: rgba(248, 248, 248, 0.9);
    }

    /* Стиль для превью изображения */
    QLabel#previewLabel {
        background-color: #f8f8f8;
        border: 2px solid #cccccc;
        border-radius: 8px;
    }
    """

    app.setStyleSheet(style)

    # Устанавливаем шрифт для всего приложения
    font = QFont("Segoe UI", 13)
    app.setFont(font)


def setup_button_styles(window):
    """Настраивает дополнительные стили для конкретных кнопок"""

    # Присваиваем объектные имена для точечного стилирования
    window.print_selected_btn.setObjectName("printButton")
    # window.print_aspect_btn.setObjectName("printButton")
    # window.print_size_btn.setObjectName("printButton")

    # Увеличиваем размеры конкретных кнопок
    # for btn in [window.print_selected_btn, window.print_aspect_btn, window.print_size_btn]:
    #     btn.setMinimumHeight(40)
    #     btn.setMinimumWidth(100)

    # Настраиваем стиль для кнопок добавления/удаления изображений
    for btn in [window.add_images_btn, window.remove_image_btn]:
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 152, 219, 0.8);
                border: 2px solid #3498db;
                border-radius: 12px;
                padding: 10px 15px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(41, 128, 185, 0.9);
                border: 2px solid #2980b9;
            }
        """)
        btn.setMinimumHeight(45)
