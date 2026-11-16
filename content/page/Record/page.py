import json
import os
import time
from collections import deque

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivy_garden.mapview import MapLayer
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from content.util.paths import Paths
from content.service.track_manager import TrackManager

# harus sama dengan tracker.py
LIVE_FILE = "track_live.jsonl"


class RecordModal(ModalView):
    started = False

    def on_start(self):
        self.started = True

        app = MDApp.get_running_app()
        record = app.root.ids.screen_manager.get_screen("Record")

        record.start_timer()
        TrackManager.start()

        self.dismiss()

    def on_dismiss(self):
        if not self.started:
            app = MDApp.get_running_app()
            app.root.ids.screen_manager.current = "Home"
            app.root.ids.navbar.select("Home")


class TrackLine(MapLayer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.points = [] 
        self.tail = None

    def add_point(self, lat, lon):
        self.points.append((lat, lon))

    def clear(self):
        self.points = []
        self.tail = None
        self.canvas.clear()

    def reposition(self):
        mapview = self.parent
        if mapview is None:
            return

        semua = list(self.points)
        if self.tail:
            semua.append(self.tail)

        koordinat = []
        for lat, lon in semua:
            x, y = mapview.get_window_xy_from(lat, lon, mapview.zoom)
            koordinat += [x, y]

        self.canvas.clear()
        if len(koordinat) >= 4:
            with self.canvas:
                Color(1, 0.4, 0.13, 1)
                Line(points=koordinat, width=3, cap="round", joint="round")


class Record(MDScreen):
    _timer = None        # timer stopwatch (1 detik)
    _poll = None         # timer baca file live (0.3 detik)
    _anim = None         # timer gerak marker (tiap frame)

    recording = False    # True selama sesi rekam berjalan
    started_at = 0
    marker_pos = None    # posisi marker yang sedang tampil: (lat, lon)
    seg = None           # segmen berjalan: (dari, ke, waktu_mulai, durasi)
    last_play_ts = None  # ts titik terakhir yang sudah diputar
    _offset = 0          # posisi byte terakhir yang sudah dibaca di file live
    queue = None         # antrian titik GPS yang belum diputar

    def on_kv_post(self, base_widget):
        self.map_view = self.ids.map_view
        self.human_position = self.ids.human_position
        self.status = self.ids.status
        self.queue = deque()

        try:
            cache = os.path.join(MDApp.get_running_app().user_data_dir, "map_cache")
            os.makedirs(cache, exist_ok=True)
            self.map_view.map_source.cache_dir = cache
        except Exception as e:
            print("[record] cache_dir gagal diatur:", e)

        self.map_view.bind(zoom=self.update_marker_scale)
        self.update_marker_scale(self.map_view, self.map_view.zoom)

    def on_enter(self):
        if self.recording:
            self.resume_timers()
        else:
            Factory.RecordModal().open()

    def read_new_points(self):
        path = Paths.database(LIVE_FILE)
        if not os.path.exists(path):
            return []

        try:
            with open(path, "rb") as f:
                f.seek(self._offset)
                chunk = f.read()
        except OSError:
            return []

        end = chunk.rfind(b"\n")
        if end < 0:
            return []
        self._offset += end + 1

        hasil = []
        for baris in chunk[:end].split(b"\n"):
            try:
                p = json.loads(baris)
                lat = float(p["lat"])
                lon = float(p["lon"])
                ts = float(p.get("ts", 0))
            except (ValueError, KeyError, TypeError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            if ts < self.started_at - 1:
                continue
            hasil.append((lat, lon, ts))
        return hasil

    def poll_location(self, dt):
        for titik in self.read_new_points():
            self.queue.append(titik)

    def animate(self, dt):
        now = time.monotonic()

        if self.seg is None:
            if not self.queue:
                return

            lat, lon, ts = self.queue.popleft()
            if (
                self.marker_pos is None
                or abs(lat - self.marker_pos[0]) + abs(lon - self.marker_pos[1]) > 0.005
            ):
                self.marker_pos = (lat, lon)
                self.last_play_ts = ts
                self.ids.track_line.add_point(lat, lon)
                self.show(lat, lon)
                self.map_view.center_on(lat, lon)
                return

            gap = 1.0 if self.last_play_ts is None else ts - self.last_play_ts
            gap = max(0.3, min(3.0, gap))
            gap /= 1 + len(self.queue)
            self.last_play_ts = ts
            self.seg = (self.marker_pos, (lat, lon), now, gap)

        dari, ke, mulai, lama = self.seg
        k = min(1.0, (now - mulai) / lama)

        lat = dari[0] + (ke[0] - dari[0]) * k
        lon = dari[1] + (ke[1] - dari[1]) * k

        self.marker_pos = (lat, lon)
        self.show(lat, lon)
        self.map_view.center_on(lat, lon)

        if k >= 1:
            self.ids.track_line.add_point(*ke)
            self.seg = None

    def show(self, lat, lon):
        self.human_position.lat = lat
        self.human_position.lon = lon

        layer = getattr(self.human_position, "_layer", None)
        if layer:
            layer.reposition()
            self.ids.track_line.tail = (lat, lon)
            self.ids.track_line.reposition()

    def update_marker_scale(self, map_view, zoom):
        size = max(8, min(48, 24 * (2 ** (zoom - 14))))
        self.human_position.size = (size, size)

    def start_timer(self):
        self.cancel_timers()

        self.recording = True
        self.started_at = time.time()
        self.queue = deque()
        self.marker_pos = None
        self.seg = None
        self.last_play_ts = None
        self._offset = 0
        self.ids.track_line.clear()

        try:
            open(Paths.database(LIVE_FILE), "wb").close()
        except OSError as e:
            print("[record] gagal reset file live:", e)

        self._schedule()

    def resume_timers(self):
        pending = []
        if self.seg:
            pending.append((*self.seg[1], 0))
        pending += list(self.queue)
        pending += self.read_new_points()

        self.queue = deque()
        self.seg = None

        if pending:
            for lat, lon, _ in pending:
                self.ids.track_line.add_point(lat, lon)
            lat, lon, ts = pending[-1]
            self.marker_pos = (lat, lon)
            self.last_play_ts = ts
            self.show(lat, lon)
            self.map_view.center_on(lat, lon)

        self.cancel_timers()
        self._schedule()

    def _schedule(self):
        self._timer = Clock.schedule_interval(self.tick, 1)
        self._poll = Clock.schedule_interval(self.poll_location, 0.3)
        self._anim = Clock.schedule_interval(self.animate, 0)

    def cancel_timers(self):
        for name in ("_timer", "_poll", "_anim"):
            ev = getattr(self, name)
            if ev:
                ev.cancel()
                setattr(self, name, None)

    def tick(self, dt):
        detik = int(time.time() - self.started_at)
        jam, sisa = divmod(detik, 3600)
        menit, detik = divmod(sisa, 60)

        if self.marker_pos:
            posisi = f"{self.marker_pos[0]:.5f}, {self.marker_pos[1]:.5f}"
        else:
            posisi = "Menunggu GPS..."

        self.status.text = f"{jam:02d}:{menit:02d}:{detik:02d}\n{posisi}"

    def stop_tracking(self):
        TrackManager.stop()
        self.cancel_timers()

        self.recording = False
        self.queue = deque()
        self.marker_pos = None
        self.seg = None
        self.status.text = "Perekaman dihentikan"

        app = MDApp.get_running_app()
        app.root.ids.screen_manager.current = "Home"
        app.root.ids.navbar.select("Home")

    def on_leave(self):
        self.cancel_timers()


Builder.load_file(Paths.file("page", "Record", "page.kv"))