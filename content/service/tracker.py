import math
import os
import sys
import time
import json
from datetime import datetime

# pastikan root project ada di sys.path (service jalan di proses terpisah)
ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from content.util.paths import Paths  # noqa: E402

# file live: SATU BARIS JSON PER TITIK, hanya di-append (harus sama dengan page.py)
LIVE_FILE = "track_live.jsonl"

# --- parameter yang bisa kamu setel ----------------------------------------
MAX_ACCURACY = 25.0   # meter. titik dengan akurasi lebih jelek dibuang
MIN_MOVE = 3.0        # meter. gerak lebih kecil dari ini dianggap diam/jitter
MAX_SPEED = 15.0      # m/s. lompatan lebih cepat dari ini dianggap GPS ngawur
PROCESS_NOISE = 3.0   # m/s. makin besar = filter makin cepat ikut gerakan
LOG_FLUSH = 10        # detik. jeda tulis ke log.json (bukan tiap titik lagi)


def distance_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class Pipeline:
    """Filter titik GPS lalu simpan. Urutan: akurasi -> lompatan -> Kalman -> gerbang diam."""

    def __init__(self):
        self.lat = None
        self.lon = None
        self.var = -1.0      # varian posisi (m^2), -1 = belum ada data
        self.t = 0.0
        self.saved = None    # titik terakhir yang disimpan
        self.rejects = 0
        self.pending = []    # antrian untuk log.json
        self.last_flush = time.time()
        self.live_path = Paths.database(LIVE_FILE)

    def feed(self, lat, lon, acc, t):
        if not acc or acc <= 0:
            acc = 10.0

        # 1. buang titik jelek (biasanya provider NETWORK / GPS belum lock)
        if acc > MAX_ACCURACY:
            return

        # titik pertama: langsung terima
        if self.var < 0:
            self.lat, self.lon, self.var, self.t = lat, lon, acc * acc, t
            self._save(lat, lon, acc)
            return

        dt = max(0.0, t - self.t)

        # 2. buang lompatan mustahil (kalau 3x berturut-turut, anggap valid & reset)
        d_raw = distance_m(self.lat, self.lon, lat, lon)
        if d_raw / max(dt, 1.0) > MAX_SPEED:
            self.rejects += 1
            if self.rejects < 3:
                return
            self.lat, self.lon, self.var, self.t = lat, lon, acc * acc, t
            self.rejects = 0
            self._save(lat, lon, acc)
            return
        self.rejects = 0

        # 3. Kalman sederhana: titik akurat dipercaya lebih, titik goyang diredam
        self.var += dt * PROCESS_NOISE ** 2
        k = self.var / (self.var + acc * acc)
        self.lat += k * (lat - self.lat)
        self.lon += k * (lon - self.lon)
        self.var = (1 - k) * self.var
        self.t = t

        # 4. gerbang diam: kalau belum bergeser berarti, jangan simpan
        if self.saved is not None:
            d = distance_m(self.saved[0], self.saved[1], self.lat, self.lon)
            if d < max(MIN_MOVE, acc * 0.5):
                return

        self._save(self.lat, self.lon, acc)

    def _save(self, lat, lon, acc):
        now = datetime.now()
        day = now.strftime("%d/%m/%Y")
        point = {
            "time": now.strftime("%H:%M:%S"),
            "lat": round(lat, 7),
            "lon": round(lon, 7),
            "accuracy": acc,
        }
        self.saved = (lat, lon)

        # live: append satu baris (cepat, tidak baca ulang seluruh file)
        line = json.dumps({**point, "ts": time.time()}) + "\n"
        with open(self.live_path, "ab") as f:
            f.write(line.encode("utf-8"))
            f.flush()

        # titik terakhir (kompatibel dengan kode lain yang baca LAST)
        try:
            Paths.write_json({**point, "ts": time.time()}, Paths.LAST)
        except Exception as e:
            print("[tracker] gagal tulis last:", e)

        # log lengkap: ditulis berkala saja
        self.pending.append((day, point))
        if time.time() - self.last_flush >= LOG_FLUSH:
            self.flush()

        print(f"[tracker] {day} {point['time']} -> {lat:.6f}, {lon:.6f}")

    def flush(self):
        self.last_flush = time.time()
        if not self.pending:
            return
        try:
            data = Paths.read_json(Paths.LOG)
            for day, p in self.pending:
                data.setdefault(day, []).append(p)
            Paths.write_json(data, Paths.LOG)
            self.pending = []
        except Exception as e:
            print("[tracker] gagal flush log:", e)


# --- Android: LocationManager langsung --------------------------------------
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

    pipe = Pipeline()

    class Listener(PythonJavaClass):
        __javainterfaces__ = ["android/location/LocationListener"]
        __javacontext__ = "app"

        @java_method("(Landroid/location/Location;)V")
        def onLocationChanged(self, loc):
            try:
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
                lm.requestLocationUpdates(provider, 1000, 0.0, listener, looper)
                print(f"[tracker] listen provider: {provider}")
                started = True
            except Exception as e:  # SecurityException kalau izin belum ada
                print(f"[tracker] provider {provider} gagal: {e}")

        if not started:
            print("[tracker] tidak ada provider aktif. Cek izin lokasi!")
            return

        print("[tracker] GPS dimulai")
        Looper.loop()
    finally:
        try:
            lm.removeUpdates(listener)
        except Exception:
            pass
        pipe.flush()
        if wake.isHeld():
            wake.release()


# --- Desktop: jalan palsu (berkelok + noise) supaya UI bisa dites ------------
def run_desktop():
    import random

    print("[tracker] bukan Android, simulasi jalan kaki")
    pipe = Pipeline()
    lat, lon = -6.9175, 107.6191
    step = 0
    while True:
        step += 1
        lat += 0.000012
        lon += 0.000015 * math.sin(step / 8.0)
        pipe.feed(
            lat + random.gauss(0, 0.000008),
            lon + random.gauss(0, 0.000008),
            8.0,
            time.time(),
        )
        time.sleep(1)


if __name__ == "__main__":
    try:
        import jnius  # noqa: F401
    except ImportError:
        run_desktop()
    else:
        run_android()