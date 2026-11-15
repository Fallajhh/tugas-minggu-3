[app]
title = JAGJAG
package.name = jagjag
package.domain = org.isekairid

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,otf,ttf
source.exclude_dirs = .venv,.git,.github,bin,.buildozer,__pycache__

version = 0.1

requirements = python3,kivy==2.3.0,kivymd==2.0.0,materialyoucolor,materialshapes,asynckivy,asyncgui,exceptiongroup,pillow,kivy-garden.mapview,requests,plyer,pyjnius,android
services = tracker:content/service/tracker.py:foreground:sticky


orientation = portrait
fullscreen = 0

# Ikon aplikasi dan layar pembuka
icon.filename = %(source.dir)s/assets/icon/icon.png
presplash.filename = %(source.dir)s/assets/img/presplash.jpg
android.presplash_color = #FFFFFF

# Kunci python-for-android ke rilis lama (Python 3.11).
# Rilis terbaru memakai Python 3.14 yang belum didukung Kivy 2.3.0.
p4a.branch = v2024.01.21

android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET,ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, FOREGROUND_SERVICE, FOREGROUND_SERVICE_LOCATION, POST_NOTIFICATIONS, WAKE_LOCK

[buildozer]
log_level = 2
warn_on_root = 0