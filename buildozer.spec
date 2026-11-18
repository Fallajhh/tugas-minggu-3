[app]
title = JAGJAG
package.name = jagjag
package.domain = org.isekairid

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,otf,ttf
source.exclude_dirs = .venv,.git,.github,bin,.buildozer,__pycache__,tests

version = 0.1

requirements = python3,kivy==2.3.0,kivymd==2.0.0,materialyoucolor,materialshapes,asynckivy,asyncgui,exceptiongroup,pillow,kivy-garden.mapview,requests,plyer,pyjnius,android,com.android.alarm.permission.SET_ALARM

# foreground + sticky: service dihidupkan ulang OS kalau di-kill
services = tracker:content/service/tracker.py:foreground:sticky:foregroundServiceType=location

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon/icon.png
presplash.filename = %(source.dir)s/assets/img/presplash.jpg
android.presplash_color = #FFFFFF

# Python 3.11 (rilis terbaru p4a memakai 3.14 yang belum didukung Kivy 2.3.0)
p4a.branch = v2024.01.21

android.gradle_dependencies = com.google.android.gms:play-services-location:21.3.0
android.enable_androidx = True

android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,FOREGROUND_SERVICE,FOREGROUND_SERVICE_LOCATION,POST_NOTIFICATIONS,WAKE_LOCK

android.manifest.launch_mode = singleTask
android.allow_backup = False

[buildozer]
log_level = 2
warn_on_root = 0