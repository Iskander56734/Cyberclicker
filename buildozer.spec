[app]

# (string) Title of your application
title = CyberClicker

# (string) Package name
package.name = cyberclicker

# (string) Package domain (needed for android packaging)
package.domain = org.iskander

# (string) Source code where the main.py live
source.dir = .

# (list) Source files to include (letting Python and PNG images work)
source.include_exts = py,png,json,txt

# (list) Application requirements
# Включаем только самые важные и проверенные библиотеки
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,idna,charset-normalizer

# (string) Custom source folders for requirements (if any)
# source.include_patterns = assets/*,images/*.png

# (string) Application versioning
version = 1.0

# (list) Permissions
# === САМАЯ ГЛАВНАЯ СТРОКА: ОТКРЫВАЕМ ЖЕЛЕЗНЫЙ ДОСТУП В ИНТЕРНЕТ ===
android.permissions = INTERNET

android.accept_sdk_license = True

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use architectures
android.archs = arm64-v8a, armeabi-v7a

# (str) The Android card orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Icon and Presplash (Optional, defaults will be used if left blank)
# icon.filename = %(source.dir)s/icon.png

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
