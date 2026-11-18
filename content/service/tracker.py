import json
import math
import os
import sys
import threading
import time

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from content.util.math_location import distance_m, is_valid_coord
from content.util.paths import Paths

LIVE_FILE = Paths.TRACK

MAX_ACCURACY = 25.0
MAX_AGE = 10.0
MIN_MOVE = 5.0 
PAUSE_MOVE = 6.0
MAX_SPEED = 15.0
PROCESS_NOISE = 3.0
GAP_BREAK = 15.0
WATCHDOG_STALE = 20.0
PAUSE_AFTER = 8.0

GPS_INTERVAL_MS = 1500
USE_WAKELOCK = False


class Pipeline:

    def __init__(self):
        self.lat = None
        self.lon = None
        self.var = -1.0
        self.t = 0.0
        self.saved = None
        self.rejects = 0
        self.sid = 0
        self.last_fix = time.time()
        self.paused = False
        self.last_move = 0.0
        self.move_ref = None
        self.live_path = Paths.database(LIVE_FILE)

    def feed(self, lat, lon, acc, t):
        if not is_valid_coord(lat, lon):
            return

        if not acc or acc <= 0:
            acc = 10.0

        if time.time() - t > MAX_AGE:
            return

        if acc > MAX_ACCURACY:
            return

        if self.var < 0:
            self._new_segment(lat, lon, acc, t)
            return

        dt = max(0.0, t - self.t)

        if dt > GAP_BREAK:
            self._new_segment(lat, lon, acc, t)
            return

        d_raw = distance_m(self.lat, self.lon, lat, lon)
        if d_raw / max(dt, 1.0) > MAX_SPEED:
            self.rejects += 1
            if self.rejects < 3:
                return
            self._new_segment(lat, lon, acc, t)
            return
        self.rejects = 0

        self.var += dt * PROCESS_NOISE ** 2
        k = self.var / (self.var + acc * acc)
        self.lat += k * (lat - self.lat)
        self.lon += k * (lon - self.lon)
        self.var = (1 - k) * self.var
        self.t = t

        self._update_pause(acc, t)

        if self.saved is not None:
            d = distance_m(self.saved[0], self.saved[1], self.lat, self.lon)
            if d < max(MIN_MOVE, acc * 0.5):
                return

        self._save(self.lat, self.lon, acc, t)

    def _update_pause(self, acc, t):
        d = distance_m(self.move_ref[0], self.move_ref[1], self.lat, self.lon)
        if d >= max(PAUSE_MOVE, acc * 0.5):
            self.move_ref = (self.lat, self.lon)
            self.last_move = t
            if self.paused:
                self.paused = False
                self._append({"ev": "resume", "ts": t})
        elif not self.paused and t - self.last_move >= PAUSE_AFTER:
            self.paused = True
            self._append({"ev": "pause", "ts": self.last_move})

    def _new_segment(self, lat, lon, acc, t):
        self.lat, self.lon, self.var, self.t = lat, lon, acc * acc, t
        self.rejects = 0
        self.move_ref = (lat, lon)
        self.last_move = t
        if self.paused:
            self.paused = False
            self._append({"ev": "resume", "ts": t})
        self.sid = int(t)
        self._save(lat, lon, acc, t)

    def _append(self, data):
        line = json.dumps(data) + "\n"
        with open(self.live_path, "ab") as f:
            f.write(line.encode("utf-8"))

    def _save(self, lat, lon, acc, t):
        self.saved = (lat, lon)
        self._append(
            {
                "lat": round(lat, 7),
                "lon": round(lon, 7),
                "acc": acc,
                "ts": t,
                "seg": self.sid,
            }
        )


def run_android():
    from jnius import autoclass, PythonJavaClass, java_method

    PythonService = autoclass("org.kivy.android.PythonService")
    Context = autoclass("android.content.Context")
    PowerManager = autoclass("android.os.PowerManager")
    Looper = autoclass("android.os.Looper")
    LocationManager = autoclass("android.location.LocationManager")

    service = PythonService.mService

    wake = None
    if USE_WAKELOCK:
        pm = service.getSystemService(Context.POWER_SERVICE)
        wake = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "jagjag:tracker")
        wake.acquire()


    pipe = Pipeline()
    stop = threading.Event()
    need_restart = threading.Event()

    class Listener(PythonJavaClass):
        __javainterfaces__ = ["android/location/LocationListener"]
        __javacontext__ = "app"

        @java_method("(Landroid/location/Location;)V")
        def onLocationChanged(self, loc):
            try:
                pipe.last_fix = time.time()
                acc = loc.getAccuracy() if loc.hasAccuracy() else None
                pipe.feed(
                    loc.getLatitude(),
                    loc.getLongitude(),
                    acc,
                    loc.getTime() / 1000.0,
                )
            except Exception as e:
                print("[tracker] gagal proses:", e)

        @java_method("(Ljava/lang/String;)V")
        def onProviderEnabled(self, provider):
            print("[tracker] provider hidup lagi:", provider)
            need_restart.set()

        @java_method("(Ljava/lang/String;)V")
        def onProviderDisabled(self, provider):
            print("[tracker] provider mati:", provider)

        @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
        def onStatusChanged(self, provider, status, extras):
            pass

    listener = Listener()
    lm = service.getSystemService(Context.LOCATION_SERVICE)

    def make_fused():
        try:
            Availability = autoclass("com.google.android.gms.common.GoogleApiAvailability")
            if Availability.getInstance().isGooglePlayServicesAvailable(service) != 0:
                print("[tracker] Google Play Services tidak tersedia")
                return None
            LocationServices = autoclass("com.google.android.gms.location.LocationServices")
            Builder = autoclass("com.google.android.gms.location.LocationRequest$Builder")
            request = (
                Builder(100, GPS_INTERVAL_MS)
                .setMinUpdateIntervalMillis(GPS_INTERVAL_MS // 2)
                .build()
            )
            client = LocationServices.getFusedLocationProviderClient(service)
            return client, request
        except Exception as e:
            print("[tracker] fused tidak bisa dipakai:", e)
            return None

    fused = make_fused()

    def register(looper):
        if fused:
            try:
                fused[0].requestLocationUpdates(fused[1], listener, looper)
                print("[tracker] listen: Fused Location")
                return True
            except Exception as e:
                print("[tracker] fused gagal, pakai LocationManager:", e)
        try:
            lm.requestLocationUpdates(
                LocationManager.GPS_PROVIDER, GPS_INTERVAL_MS, 0.0, listener, looper
            )
            print("[tracker] listen provider: gps")
            return True
        except Exception as e:
            print(f"[tracker] provider gps gagal: {e}")
            return False

    def unregister():
        if fused:
            try:
                fused[0].removeLocationUpdates(listener)
            except Exception:
                pass
        try:
            lm.removeUpdates(listener)
        except Exception:
            pass

    try:
        Looper.prepare()
        looper = Looper.myLooper()

        if not register(looper):
            print("[tracker] tidak ada provider aktif. Cek izin lokasi!")
            return

        def watchdog():
            while not stop.is_set():
                need_restart.wait(10)
                if stop.is_set():
                    break
                stale = time.time() - pipe.last_fix > WATCHDOG_STALE
                if need_restart.is_set() or stale:
                    need_restart.clear()
                    print("[tracker] watchdog: daftar ulang listener GPS")
                    unregister()
                    register(looper)
                    pipe.last_fix = time.time()

        threading.Thread(target=watchdog, daemon=True).start()

        print("[tracker] GPS dimulai")
        Looper.loop()
    finally:
        stop.set()
        need_restart.set()
        unregister()
        if wake is not None and wake.isHeld():
            wake.release()


def watch_parent():
    try:
        sys.stdin.buffer.read()
    except Exception:
        pass
    os._exit(0)


def run_desktop():
    import random

    if "--watch-parent" in sys.argv:
        threading.Thread(target=watch_parent, daemon=True).start()

    print("[tracker] bukan Android, simulasi jalan kaki")
    pipe = Pipeline()
    lat, lon = -6.9175, 107.6191
    step = 0
    while True:
        step += 1
        lat += 0.000012
        lon += 0.000015 * math.sin(step / 8.0)

        if step % 60 == 30:
            print("[tracker] simulasi: berdiri diam 15 dtk")
            for _ in range(15):
                pipe.feed(
                    lat + random.gauss(0, 0.000008),
                    lon + random.gauss(0, 0.000008),
                    8.0,
                    time.time(),
                )
                time.sleep(1)

        if step % 60 == 0:
            print("[tracker] simulasi: sinyal hilang 20 dtk + pindah jauh")
            time.sleep(20)
            lat += 0.05

        pipe.feed(
            lat + random.gauss(0, 0.000008),
            lon + random.gauss(0, 0.000008),
            8.0,
            time.time(),
        )
        time.sleep(1)


if __name__ == "__main__":
    try:
        import jnius
    except ImportError:
        run_desktop()
    else:
        run_android()