from django.core.cache import cache
import hashlib
from time import time


def get_or_create_dynamic_id(user):
    # Пытаемся достать уже созданный код для этого юзера из кэша
    cache_key_user = f"user_code_id_{user.id}"
    existing_code = cache.get(cache_key_user)
    if existing_code:
        return existing_code
    # Если кода нет, генерируем новый
    attempts = 0
    while attempts < 5:
        current_minute = int(time() // 60)
        seed = f"{user.secret_key}-{current_minute}-{attempts}"
        new_code = f"TASK-{hashlib.sha256(seed.encode()).hexdigest()[:8].upper()}"

        # Проверяем, не занят ли этот код КЕМ-ТО ДРУГИМ
        # nx=True в Redis гарантирует, что запись создастся только если ключа нет
        is_unique = cache.add(f"dynamic_id_registry_{new_code}", user.id, timeout=60)

        if is_unique:
            # Сохраняем обратную связь, чтобы не генерить код заново при каждом обновлении страницы
            cache.set(cache_key_user, new_code, timeout=60)
            return new_code

        attempts += 1

    return "ERROR-RETRY"

def get_user_id_by_dynamic_code(code):
    return cache.get(f"dynamic_id_registry_{code}")