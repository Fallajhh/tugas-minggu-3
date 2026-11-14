[app]
title = JAGJAG
package.name = jagjag
package.domain = org.isekairid

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,otf,ttf
source.exclude_dirs = .venv,.git,.github,bin,.buildozer,__pycache__

version = 0.1

requirements = python3,kivy==2.3.0,https://github.com/kivymd/KivyMD/archive/master.zip,materialyoucolor,materialshapes,asynckivy,asyncgui,exceptiongroup,pillow

orientation = portrait
fullscreen = 0

# Ikon aplikasi dan layar pembuka
icon.filename = %(source.dir)s/assets/icon/icon.png
presplash.filename = %(source.dir)s/assets/img/presplash.jpg
android.presplash_color = #FFFFFF

# Kunci python-for-android ke rilis lama (Python 3.11).
# Rilis terbaru memakai Python 3.14 yang belum didukung Kivy 2.3.0.
p4a.branch = v2024.01.21

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 0