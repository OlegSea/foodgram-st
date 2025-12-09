import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            try:
                format_part, imgstr = data.split(";base64,")
                ext = format_part.split("/")[-1]

                decoded_data = base64.b64decode(imgstr)

                file_name = f"{uuid.uuid4()}.{ext}"

                data = ContentFile(decoded_data, name=file_name)

            except (ValueError, TypeError) as e:
                raise serializers.ValidationError(
                    "Неверный формат base64 изображения. "
                    "Ожидается формат: data:image/<тип>;base64,<данные>"
                ) from e

        return super().to_internal_value(data)
