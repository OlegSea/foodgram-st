# Foodgram - «Продуктовый помощник»

**Автор:** Трифонов Алексей Юрьевич (Группа А-13-23) — [Telegram](https://t.me/olegsea)

## Описание проекта

Foodgram — веб-приложение для публикации рецептов, подписок на авторов и создания списков покупок. Пользователи могут делиться своими рецептами, добавлять понравившиеся в избранное и формировать список покупок для выбранных блюд.

## Технологический стек

### Backend
- **Python 3.11**
- **Django 5.2.8** — веб-фреймворк
- **Django REST Framework 3.16.1** — для создания API
- **Djoser 2.3.3** — аутентификация через токены
- **PostgreSQL** — основная база данных
- **Pillow 12.0.0** — работа с изображениями

### Frontend
- **React** — SPA-приложение
- **JavaScript/HTML/CSS**

### DevOps
- **Docker & Docker Compose** — контейнеризация
- **Nginx** — веб-сервер и прокси
- **GitHub Actions** — CI/CD

## Модели данных

### Основные модели
- **User** — пользователи (расширенная модель Django)
- **Recipe** — рецепты
- **Ingredient** — продукты
- **RecipeIngredient** — связь рецептов и продуктов с количеством
- **Favorite** — избранные рецепты пользователей
- **ShoppingCart** — список покупок пользователей
- **Subscription** — подписки пользователей

## Установка и запуск
Для запуска необходим Docker и Docker Compose. Рекомендую установить [just](https://github.com/casey/just).

Перед запуском не забудьте в папке infra создать `.env` файл (в `env.example` описаны необходимые пункты).

Приложение будет доступно по адресу: [http://localhost:3000](http://localhost:3000)

### Если установлен `just`:
```bash
git clone https://github.com/olegsea/foodgram-st

just build # собрать контейнеры из исходников
just run # использовать контейнеры с Docker Hub
just down # остановить контейнеры
just prune # почистить лишние volume
```

### Если нет:
```bash
git clone https://github.com/olegsea/foodgram-st

cd infra/

# собрать контейнеры из исходников
docker-compose -f docker-compose.local.yml up --build
# использовать контейнеры с Docker Hub
docker-compose up -d
```

## Локальная разработка

Для пользователей NixOS в папке `backend` есть flake.nix файл, благодаря которому можно запустить Dev Shell (`nix develop` в папке `backend`).

Для остальных рекомендую использовать [uv](https://docs.astral.sh/uv/).

```bash
cd backend/

# Создание виртуального окружения и установка зависимостей
uv sync

# Применение миграций
uv run python manage.py migrate

# Импорт продуктов из фикстуры
uv run python manage.py loaddata data/ingredients.json

# Импорт тестовых данных из фикстуры
uv run python manage.py loaddata data/test_data.json

# Создание суперпользователя
uv run python manage.py createsuperuser

# Запуск сервера разработки
uv run python manage.py runserver
```

## Доступы

После запуска доступны:

| Ресурс | URL |
|--------|-----|
| Приложение | [http://localhost:3000](http://localhost:3000) |
| API | [http://localhost:3000/api/](http://localhost:3000/api/) |
| Документация API | [http://localhost:3000/api/docs/](http://localhost:3000/api/docs/) |
| Админка | [http://localhost:3000/admin/](http://localhost:3000/admin/) |

При локальном запуске без Docker (только backend) используйте порт 8000.
