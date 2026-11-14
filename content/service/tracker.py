import json
import os
import threading
from datetime import datetime

# --- Bagian 1: cegah CPU tidur (tetap sama) -------------------------------
wake = None
try:
    from jnius import autoclass

    PythonService = autoclass("org.kivy.android.PythonService")
    Context = autoclass("android.content.Context")
    PowerManager = autoclass("android.os.PowerManager")

    service = PythonService.mService
    pm = service.getSystemService(Context.POWER_SERVICE)
    wake = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "jagjag:tracker")
    wake.acquire()
    print("[tracker] wakelock aktif")
except ImportError:
    print("[tracker] bukan Android, wakelock dilewati")


# --- Bagian 2: lokasi file log --------------------------------------------
BASE_DIR = os.environ.get("ANDROID_PRIVATE", ".")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_FILE = os.path.join(DATA_DIR, "log.json")
os.makedirs(DATA_DIR, exist_ok=True)


# --- Bagian 3: fungsi utama, simpan satu titik ----------------------------
def save_point(lat, lon, accuracy=None):
    now = datetime.now()
    day = now.strftime("%d/%m/%Y")          # contoh: 14/11/2026
    point = {
        "time": now.strftime("%H:%M:%S"),
        "lat": lat,
        "lon": lon,
        "accuracy": accuracy,
    }

    # baca log lama (kalau ada)
    try:
        with open(LOG_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    # tambahkan titik ke daftar hari ini
    data.setdefault(day, []).append(point)

    # tulis ke file sementara dulu, lalu ganti file asli
    # supaya UI tidak pernah membaca file yang setengah tertulis
    tmp = LOG_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, LOG_FILE)

    print(f"[tracker] {day} {point['time']} -> {lat}, {lon}")


# --- Bagian 4: dipanggil GPS tiap ada titik baru --------------------------
def on_location(**kwargs):
    save_point(kwargs.get("lat"), kwargs.get("lon"), kwargs.get("accuracy"))


# --- Bagian 5: jalankan GPS ------------------------------------------------
try:
    from plyer import gps

    gps.configure(on_location=on_location)
    gps.start(minTime=1000, minDistance=0)
    print("[tracker] GPS dimulai")
    threading.Event().wait()                # tahan service tetap hidup
except (ImportError, NotImplementedError):
    # Di Windows tidak ada GPS, jadi simpan satu titik palsu untuk tes
    print("[tracker] GPS tidak tersedia, simpan titik tes")
    save_point(-6.9175, 107.6191, 5.0)
finally:
    if wake is not None and wake.isHeld():
        wake.release()