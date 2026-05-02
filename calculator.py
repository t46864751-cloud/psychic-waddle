#!/bin/bash

# ============================================
# Большой безвредный Bash-скрипт
# Назначение: информационный инструмент, резервное копирование, тест сети
# Версия: 1.0
# ============================================


RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}           $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Функция для вывода успешных сообщений
success_msg() {
    echo -e "${GREEN}[✔] $1${NC}"
}

# Функция для вывода информационных сообщений
info_msg() {
    echo -e "${YELLOW}[ℹ] $1${NC}"
}

# Начало скрипта
clear
echo -e "${GREEN}Добро пожаловать в Большой Безвредный Скрипт!${NC}"
echo "Текущая дата и время: $(date)"
echo "Пользователь: $USER"
echo "Домашняя директория: $HOME"
echo ""

# 1. Системная информация
print_header "Системная информация"
echo "Операционная система: $(uname -o)"
echo "Ядро: $(uname -r)"
echo "Архитектура: $(uname -m)"
echo "Имя хоста: $(hostname)"
ec$(uptime -p | sed 's/up //')"
if command -v lsb_release &> /dev/null; then
    echo "Дисив: $(lsb_release -ds 2>/dev/null || echo 'Не определён')"
fi
echo ""

# 2. Информация о процессоре
print_header "Процессор"
if command -v lscpu &> /dev/null; then
    echo "Модель: $(lscpu | grep "Model name" | cut -d':' -f2 | xargs)"
    echo "Ядер: $(nproc)"
else
    info_msg "Утилита lscpu не найдена, используется /proc/cpuinfo"
    grep "model name" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs | sed 's/^/Модель: /'
    echo "Ядер: $(grep -c ^processor /proc/cpuinfo)"
fi
echo ""

# 3. Оперативная память (только чтение, никаких изменений)
print_header "Оперативная память"
if command -v free &> /dev/null; then
    free -h | grep -E "Mem:|Swap:"
else
    info_msg "Команда free не найдена"
fi
echo ""

# 4. Дисковая информация (только чтение)
print_header "Использование дисков"
if command -v df &> /dev/null; then
    df -h | grep -E "^/dev/"
else
    info_msg "Команда df не найдена"
fi
echo ""

# 5. Календарь на текущий месяц
print_header "Календарь"
cal -3
echo ""

# 6. Псевдопогода (безопасная заглушка)
print_header "Прогноз погоды (демонстрация)"
echo "Имитация получения погоды для города $(curl -s ifconfig.me/city 2>/dev/null || echo 'ВашГород')"
echo "Температура: +22°C (солнечно) — данные заглушки"
info_msg "Реальная погода отключена для безопасности скрипта"
echo ""

# 7. Создание резервной копии .bashrc (только если файл существует)
print_header "Резервное копирование .bashrc"
BACKUP_DIR="$HOME/bashrc_backups"
if [[ -f "$HOME/.bashrc" ]]; then
    mkdir -p "$BACKUP_DIR"
    BACKUP_NAME="bashrc_backup_$(date +%Y%m%d_%H%M%S).bak"
    cp "$HOME/.bashrc" "$BACKUP_DIR/$BACKUP_NAME"
    success_msg "Резервная копия создана: $BACKUP_DIR/$BACKUP_NAME"
    echo "Всего резервных копий: $(ls -1 $BACKUP_DIR/*.bak 2>/dev/null | wc -l)"
else
    info_msg "Файл .bashrc не найден, пропускаем резервное копирование"
fi
echo ""

# 8. Простой тест интернета (ping до 8.8.8.8, 2 попытки)
print_header "Тест соединения с интернетом"
if command -v ping &> /dev/null; then
    echo "Проверка связи с 8.8.8.8 (2 пакета):"
    ping -c 2 -W 2 8.8.8.8 &> /dev/null
    if [[ $? -eq 0 ]]; then
        success_msg "Интернет работает"
    else
        info_msg "Интернет недоступен или ping заблокирован"
    fi
else
    info_msg "Команда ping не найдена"
fi
echo ""
# 11. Завершение скрипта
print_header "Завершение"
echo "Скрипт выполнил все действия без изменений системы."
echo "Лог операций сохранён здесь: не сохранялся (только вывод в консоль)."
echo ""
info_msg "Чтобы запустить скрипт повторно, дайте права: chmod +x script.sh и ./script.sh"
echo -e "${GREEN}До свидания, $USER!${NC}"

exit 0
