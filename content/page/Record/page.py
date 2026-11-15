import os
import time

from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivy_garden.mapview import MapLayer
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from content.util.paths import Paths
from content.service.track_manager import TrackManager


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
        self.points = []   # titik yang sudah selesai dilalui
        self.tail = None   # posisi marker sekarang (ujung garis)

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
    _timer = None       # timer stopwatch (1 detik)
    _poll = None        # timer baca file lokasi (0.5 detik)
    _anim = None        # timer gerak marker (tiap frame)

    started_at = 0
    last_ts = None      # waktu titik GPS terakhir yang sudah dibaca
    marker_pos = None   # posisi marker yang sedang tampil: (lat, lon)
    move = None         # gerakan berjalan: (dari, ke, waktu_mulai, durasi)

    def on_kv_post(self, base_widget):
        self.map_view = self.ids.map_view
        self.human_position = self.ids.human_position
        self.status = self.ids.status

        try:
            cache = os.path.join(MDApp.get_running_app().user_data_dir, "map_cache")
            os.makedirs(cache, exist_ok=True)
            self.map_view.map_source.cache_dir = cache
        except Exception as e:
            print("[record] cache_dir gagal diatur:", e)

        self.map_view.bind(zoom=self.update_marker_scale)
        self.update_marker_scale(self.map_view, self.map_view.zoom)

    def poll_location(self, dt):
        p = Paths.read_json(Paths.LAST)
        if not p:
            return

        ts = p.get("ts", 0)
        if ts < self.started_at or ts == self.last_ts:
            return

        try:
            lat = float(p["lat"])
            lon = float(p["lon"])
        except (KeyError, ValueError, TypeError):
            return
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return

        if (
            self.marker_pos is None
            or abs(lat - self.marker_pos[0]) + abs(lon - self.marker_pos[1]) > 0.005
        ):
            self.marker_pos = (lat, lon)
            self.move = None
            self.show(lat, lon)
            self.ids.track_line.add_point(lat, lon)
            self.map_view.center_on(lat, lon)
        else:
            lama = 2 if self.last_ts is None else ts - self.last_ts
            lama = max(0.5, min(3, lama))
            self.move = (self.marker_pos, (lat, lon), time.monotonic(), lama)

        self.last_ts = ts
        self.status.text = f"GPS Aktif\n{lat:.5f}, {lon:.5f}"

    def animate(self, dt):
        if not self.move:
            return

        dari, ke, mulai, lama = self.move
        k = min(1, (time.monotonic() - mulai) / lama)

        lat = dari[0] + (ke[0] - dari[0]) * k
        lon = dari[1] + (ke[1] - dari[1]) * k

        self.marker_pos = (lat, lon)
        self.show(lat, lon)
        self.map_view.center_on(lat, lon)

        if k >= 1:
            self.ids.track_line.add_point(*ke)
            self.move = None

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

        self.started_at = time.time()
        self.last_ts = None
        self.marker_pos = None
        self.move = None
        self.ids.track_line.clear()

        self._timer = Clock.schedule_interval(self.tick, 1)
        self._poll = Clock.schedule_interval(self.poll_location, 0.5)
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

        self.marker_pos = None
        self.move = None
        self.status.text = "Perekaman dihentikan"

        app = MDApp.get_running_app()
        app.root.ids.screen_manager.current = "Home"
        app.root.ids.navbar.select("Home")

    def on_leave(self):
        self.cancel_timers()


Builder.load_file(Paths.file("page", "Record", "page.kv"))