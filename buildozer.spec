[app]
title = Cyberclicker
package.name = cyberclicker
package.domain = org.iskander

# ЖЁСТКИЙ СБРОС КЭША СЕРВЕРА — СТАВИМ ВЕРСИЮ 0.3!
version = 0.7

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# СВЯЗКА ВЕКА: СТАБИЛЬНЫЙ ПИТОН 3.10 И КИВИ 2.3.0
requirements = python3,kivy
# Принудительно игнорируем сишные баги компиляции SSL и SQLite!
p4a.blacklist = sqlite3,openssl,ssl,_ssl,_sqlite3

orientation = portrait
fullscreen = 1

# НАСТРОЙКИ АНДРОИДА
android.api = 31
android.minapi = 21
android.ndk = 25b
android.private_storage = 1

# ЖЕСТКО ЗАКАЗЫВАЕМ ПРАВА НА ПАМЯТЬ У АНДРОИДА ДЛЯ РАБОТЫ СОХРАНЕНИЙ!
android.permissions = android.permission.WRITE_EXTERNAL_STORAGE, android.permission.READ_EXTERNAL_STORAGE

# ПРИНУДИТЕЛЬНО ТОЛЬКО СОВРЕМЕННЫЙ 64-БИТНЫЙ КОРПУС!
android.archs = arm64-v8a

# АВТО-ПРИНЯТИЕ ЛИЦЕНЗИЙ GOOGLE
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
icon.filename = icon.png

# ИКОНКА НАШЕГО ПАЦАНСКОГО КЛИКЕРА НА ЭКРАНЕ Т

