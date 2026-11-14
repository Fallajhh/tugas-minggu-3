[app]
title = JAGJAG
package.name = jagjag
package.domain = org.isekairid

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = .venv,.git,.github,bin,.buildozer,__pycache__

version = 0.1

requirements = python3,kivy==2.3.0,https://github.com/kivymd/KivyMD/archive/master.zip,materialyoucolor,materialshapes,asynckivy,asyncgui,exceptiongroup,pillow

orientation = portrait
fullscreen = 0

# Ikon aplikasi dan layar pembuka
icon.filename = %(source.dir)s/assets/icon/icon.png
presplash.filename = %(source.dir)s/assets/img/presplash.jpg
android.presplash_color = #FFFFFF

android.api = 34
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1