from PIL import Image
import os


def parse_aspect_ratio(ratio_str):
    """Парсит строку соотношения сторон (например, '16:9')"""
    try:
        width_ratio, height_ratio = map(float, ratio_str.split(':'))
        return width_ratio / height_ratio
    except (ValueError, AttributeError):
        raise ValueError(f"Неверный формат соотношения сторон: {ratio_str}. Используйте формат 'ширина:высота'")


def add_padding_to_aspect_ratio(image_path, aspect_ratio=None, output_size=None, output_path=None):
    """
    Добавляет белые поля к изображению для достижения нужного соотношения сторон или размеров

    Изображение масштабируется так, чтобы полностью влезать в целевые размеры без обрезки
    """

    if aspect_ratio is None and output_size is None:
        raise ValueError("Должен быть указан либо aspect_ratio, либо output_size")

    if aspect_ratio is not None and output_size is not None:
        raise ValueError("Укажите только один параметр: aspect_ratio ИЛИ output_size")

    # Открываем изображение
    with Image.open(image_path) as img:
        original_img = img.convert('RGB')  # Конвертируем в RGB для гарантии

        # Получаем текущие размеры
        original_width, original_height = original_img.size
        original_ratio = original_width / original_height

        # Определяем целевые размеры
        if output_size is not None:
            # Парсим размеры, если передана строка
            if isinstance(output_size, str):
                try:
                    target_width, target_height = map(int, output_size.split('x'))
                except (ValueError, AttributeError):
                    raise ValueError(f"Неверный формат размеров: {output_size}. Используйте формат 'ширинаxвысота'")
            else:
                target_width, target_height = output_size

            target_ratio = target_width / target_height

            # Масштабируем изображение так, чтобы оно полностью влезало в целевые размеры
            # Используем минимальный масштаб, чтобы обе стороны были меньше или равны целевым
            scale_width = target_width / original_width
            scale_height = target_height / original_height
            scale = min(scale_width, scale_height)

            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            original_img = original_img.resize((new_width, new_height), Image.LANCZOS)
            original_width, original_height = new_width, new_height
            print(f"Изображение масштабировано до: {original_width}x{original_height}")

            new_width, new_height = target_width, target_height

        else:
            # Используем соотношение сторон
            if isinstance(aspect_ratio, str):
                target_ratio = parse_aspect_ratio(aspect_ratio)
            else:
                target_ratio = aspect_ratio

            # Если текущее соотношение уже соответствует целевому
            if abs(original_ratio - target_ratio) < 0.01:
                print("Изображение уже имеет нужное соотношение сторон")
                if output_path:
                    original_img.save(output_path)
                return original_img

            # Определяем новые размеры на основе соотношения сторон
            # Без масштабирования - только добавляем белые поля
            if original_ratio > target_ratio:
                # Ширина слишком большая - добавляем поля сверху и снизу
                new_width = original_width
                new_height = int(original_width / target_ratio)
            else:
                # Высота слишком большая - добавляем поля слева и справа
                new_height = original_height
                new_width = int(original_height * target_ratio)

        # Вычисляем отступы для центрирования
        padding_left = (new_width - original_width) // 2
        padding_right = new_width - original_width - padding_left
        padding_top = (new_height - original_height) // 2
        padding_bottom = new_height - original_height - padding_top

        # Проверяем, что отступы не отрицательные (изображение не выходит за границы)
        if padding_left < 0 or padding_top < 0:
            # Если изображение больше целевых размеров, масштабируем его еще раз
            scale = min(new_width / original_width, new_height / original_height)
            original_width = int(original_width * scale)
            original_height = int(original_height * scale)
            original_img = original_img.resize((original_width, original_height), Image.LANCZOS)

            # Пересчитываем отступы
            padding_left = (new_width - original_width) // 2
            padding_right = new_width - original_width - padding_left
            padding_top = (new_height - original_height) // 2
            padding_bottom = new_height - original_height - padding_top

            print(f"Дополнительное масштабирование до: {original_width}x{original_height}")

        # Создаем новое изображение с белым фоном
        new_img = Image.new('RGB', (new_width, new_height), (255, 255, 255))

        # Вставляем оригинальное изображение в центр
        new_img.paste(original_img, (padding_left, padding_top))

        # Сохраняем результат
        if output_path is None:
            name, ext = os.path.splitext(image_path)
            suffix = "_padded" if aspect_ratio else "_resized"
            output_path = f"{name}{suffix}{ext}"

        new_img.save(output_path)
        print(f"Изображение сохранено как: {output_path}")
        print(f"Исходные размеры: {img.size[0]}x{img.size[1]}")
        print(f"Масштабированные размеры: {original_width}x{original_height}")
        print(f"Финальные размеры: {new_width}x{new_height}")
        print(
            f"Добавлено полей: слева {padding_left}, справа {padding_right}, сверху {padding_top}, снизу {padding_bottom}")

        return new_img


if __name__ == "__main__":
    image_path = "..\хрупкое.jpg"

    # Вариант 1: по соотношению сторон
    try:
        add_padding_to_aspect_ratio(image_path, aspect_ratio="16:9", output_path="хрупкое_16x9.jpg")
    except Exception as e:
        print(f"Ошибка: {e}")

    # Вариант 2: по конкретным размерам (изображение будет масштабировано чтобы влезть)
    try:
        add_padding_to_aspect_ratio(image_path, output_size="800x600", output_path="хрупкое_800x600.jpg")
    except Exception as e:
        print(f"Ошибка: {e}")

    # Вариант 3: по большим размерам (изображение увеличится до максимально возможного)
    try:
        add_padding_to_aspect_ratio(image_path, output_size="3000x2000", output_path="хрупкое_3000x2000.jpg")
    except Exception as e:
        print(f"Ошибка: {e}")