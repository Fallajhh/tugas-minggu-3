import os
import sys
import time
from datetime import datetime

# pastikan root project ada di sys.path (service jalan di proses terpisah)
ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from content.util.paths import Paths  # noqa: E402


# --- simpan satu titik ------------------------------------------------------
def save_point(lat, lon, accuracy=None):
    now = datetime.now()
    day = now.strftime("%d/%m/%Y")
    point = {
        "time": now.strftime("%H:%M:%S"),
        "lat": lat,
        "lon": lon,
        "accuracy": accuracy,
    }

    # log lengkap
    data = Paths.read_json(Paths.LOG)
    data.setdefault(day, []).append(point)
    Paths.write_json(data, Paths.LOG)

    # titik terakhir untuk UI
    Paths.write_json({**point, "ts": time.time()}, Paths.LAST)

    print(f"[tracker] {day} {point['time']} -> {lat}, {lon}")


# --- Android: LocationManager langsung (lebih andal di service daripada plyer)
def run_android():
    from jnius import autoclass, PythonJavaClass, java_method

    PythonService = autoclass("org.kivy.android.PythonService")
    Context = autoclass("android.content.Context")
    PowerManager = autoclass("android.os.PowerManager")
    Looper = autoclass("android.os.Looper")
    LocationManager = autoclass("android.location.LocationManager")

    service = PythonService.mService

    pm = service.getSystemService(Context.POWER_SERVICE)
    wake = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "jagjag:tracker")
    wake.acquire()
    print("[tracker] wakelock aktif")

    class Listener(PythonJavaClass):
        __javainterfaces__ = ["android/location/LocationListener"]
        __javacontext__ = "app"

        @java_method("(Landroid/location/Location;)V")
        def onLocationChanged(self, loc):
            try:
                save_point(loc.getLatitude(), loc.getLongitude(), loc.getAccuracy())
            except Exception as e:
                print("[tracker] gagal simpan:", e)

        @java_method("(Ljava/lang/String;)V")
        def onProviderEnabled(self, provider):
            pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderDisabled(self, provider):
            pass

        @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
        def onStatusChanged(self, provider, status, extras):
            pass

    listener = Listener()
    lm = service.getSystemService(Context.LOCATION_SERVICE)

    try:
        Looper.prepare()
        looper = Looper.myLooper()

        started = False
        for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
            try:
                lm.requestLocationUpdates(provider, 2000, 0.0, listener, looper)
                print(f"[tracker] listen provider: {provider}")
                started = True
            except Exception as e:  # SecurityException kalau izin belum ada
                print(f"[tracker] provider {provider} gagal: {e}")

        if not started:
            print("[tracker] tidak ada provider aktif. Cek izin lokasi!")
            return

        print("[tracker] GPS dimulai")
        Looper.loop()  # blok di sini, callback datang lewat looper
    finally:
        try:
            lm.removeUpdates(listener)
        except Exception:
            pass
        if wake.isHeld():
            wake.release()


# --- Desktop: titik palsu supaya UI bisa dites ------------------------------
def run_desktop():
    print("[tracker] bukan Android, simpan titik tes")
    save_point(-6.9175, 107.6191, 5.0)


if __name__ == "__main__":
    try:
        import jnius
    except ImportError:
        run_desktop()
    else:
        run_android()