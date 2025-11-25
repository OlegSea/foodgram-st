#!/usr/bin/env bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo -e "${BLUE}"
echo "=========================================="
echo "    Создание админа"
echo "=========================================="
echo -e "${NC}"

if [ ! -f "docker-compose.yml" ]; then
    print_error "Файл docker-compose.yml не найден!"
    print_error "Пожалуйста, запустите скрипт из папки infra"
    exit 1
fi

check_containers() {
    print_message "Проверяем статус контейнеров..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен или недоступен!"
        exit 1
    fi

    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose не найден!"
        exit 1
    fi

    print_message "Используем команду: $COMPOSE_CMD"
}

start_containers() {
    print_message "Запускаем контейнеры..."

    $COMPOSE_CMD up -d

    if [ $? -ne 0 ]; then
        print_error "Не удалось запустить контейнеры!"
        exit 1
    fi

    print_success "Контейнеры запущены!"
    print_message "Ожидаем 30 секунд для полной загрузки..."
    sleep 30
}

create_admin() {
    print_message "Создаем администратора..."

    DEFAULT_EMAIL="admin@foodgram.ru"
    DEFAULT_USERNAME="admin"
    DEFAULT_PASSWORD="admin123"
    DEFAULT_FIRST_NAME="Admin"
    DEFAULT_LAST_NAME="User"

    echo
    print_message "Хотите использовать параметры по умолчанию?"
    echo "Email: $DEFAULT_EMAIL"
    echo "Username: $DEFAULT_USERNAME"
    echo "Password: $DEFAULT_PASSWORD"
    echo "Имя: $DEFAULT_FIRST_NAME"
    echo "Фамилия: $DEFAULT_LAST_NAME"
    echo

    read -p "Использовать параметры по умолчанию? (y/n, по умолчанию: y): " USE_DEFAULTS
    USE_DEFAULTS=${USE_DEFAULTS:-y}

    if [[ "$USE_DEFAULTS" =~ ^[Yy]$ ]]; then
        ADMIN_EMAIL=$DEFAULT_EMAIL
        ADMIN_USERNAME=$DEFAULT_USERNAME
        ADMIN_PASSWORD=$DEFAULT_PASSWORD
        ADMIN_FIRST_NAME=$DEFAULT_FIRST_NAME
        ADMIN_LAST_NAME=$DEFAULT_LAST_NAME
    else
        read -p "Email администратора: " ADMIN_EMAIL
        ADMIN_EMAIL=${ADMIN_EMAIL:-$DEFAULT_EMAIL}

        read -p "Username администратора: " ADMIN_USERNAME
        ADMIN_USERNAME=${ADMIN_USERNAME:-$DEFAULT_USERNAME}

        read -p "Имя администратора: " ADMIN_FIRST_NAME
        ADMIN_FIRST_NAME=${ADMIN_FIRST_NAME:-$DEFAULT_FIRST_NAME}

        read -p "Фамилия администратора: " ADMIN_LAST_NAME
        ADMIN_LAST_NAME=${ADMIN_LAST_NAME:-$DEFAULT_LAST_NAME}

        read -s -p "Пароль администратора: " ADMIN_PASSWORD
        ADMIN_PASSWORD=${ADMIN_PASSWORD:-$DEFAULT_PASSWORD}
        echo
    fi

    PYTHON_SCRIPT="
from users.models import User
from django.contrib.auth import get_user_model
import sys

User = get_user_model()

email = '$ADMIN_EMAIL'
username = '$ADMIN_USERNAME'
first_name = '$ADMIN_FIRST_NAME'
last_name = '$ADMIN_LAST_NAME'
password = '$ADMIN_PASSWORD'

try:
    if User.objects.filter(email=email).exists():
        print(f'Пользователь с email {email} уже существует. Обновляем данные...')
        admin_user = User.objects.get(email=email)
        admin_user.set_password(password)
        admin_user.username = username
        admin_user.first_name = first_name
        admin_user.last_name = last_name
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print('Администратор успешно обновлен!')
    else:
        if User.objects.filter(username=username).exists():
            print(f'Пользователь с username {username} уже существует. Обновляем данные...')
            admin_user = User.objects.get(username=username)
            admin_user.email = email
            admin_user.set_password(password)
            admin_user.first_name = first_name
            admin_user.last_name = last_name
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            print('Администратор успешно обновлен!')
        else:
            print('Создаем нового администратора...')
            admin_user = User.objects.create_superuser(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            print('Администратор успешно создан!')

    print(f'Email: {admin_user.email}')
    print(f'Username: {admin_user.username}')
    print(f'Имя: {admin_user.first_name}')
    print(f'Фамилия: {admin_user.last_name}')
    print('Статус: Суперпользователь')

except Exception as e:
    print(f'Ошибка при создании администратора: {e}')
    sys.exit(1)
"

    print_message "Выполняем создание/обновление администратора..."

    $COMPOSE_CMD exec backend python manage.py shell -c "$PYTHON_SCRIPT"

    if [ $? -eq 0 ]; then
        print_success "Администратор успешно создан/обновлен!"
        echo
        print_success "Данные для входа в админ-панель:"
        echo -e "${GREEN}Email:${NC} $ADMIN_EMAIL"
        echo -e "${GREEN}Username:${NC} $ADMIN_USERNAME"
        echo -e "${GREEN}Пароль:${NC} $ADMIN_PASSWORD"
        echo
        print_success "Админ-панель доступна по адресу: http://localhost:3000/admin/"
        echo -e "${YELLOW}Рекомендуется сменить пароль после первого входа!${NC}"
    else
        print_error "Не удалось создать администратора!"
        exit 1
    fi
}

main() {
    check_containers
    start_containers
    create_admin

    echo
    print_success "Скрипт завершен успешно!"
    print_message "Вы можете войти в админ-панель по адресу: http://localhost:3000/admin/"
}

main
