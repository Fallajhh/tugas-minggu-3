import json
import os
import time
from collections import deque

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivy.uix.modalview import ModalView
from kivy_garden.mapview import MapLayer
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from content.util.paths import Paths
from content.service.track_manager import TrackManager

LIVE_FILE = "track.jsonl"


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
        self.segments = [[]]
        self.tail = None

    def add_point(self, lat, lon):
        self.segments[-1].append((lat, lon))

    def break_line(self):
        if self.segments[-1]:
            self.segments.append([])
        self.tail = None

    def clear(self):
        self.segments = [[]]
        self.tail = None
        self.canvas.clear()

    def reposition(self):
        mapview = self.parent
        if mapview is None:
            return

        self.canvas.clear()
        with self.canvas:
            Color(1, 0.4, 0.13, 1)
            for i, seg in enumerate(self.segments):
                pts = list(seg)
                if i == len(self.segments) - 1 and self.tail:
                    pts.append(self.tail)
                if len(pts) < 2:
                    continue
                koordinat = []
                for lat, lon in pts:
                    x, y = mapview.get_window_xy_from(lat, lon, mapview.zoom)
                    koordinat += [x, y]
                Line(points=koordinat, width=3, cap="round", joint="round")


class Record(MDScreen):
    _timer = None
    _poll = None
    _anim = None

    recording = BooleanProperty(False)
    started_at = 0
    marker_pos = None
    seg = None
    last_play_ts = None
    _offset = 0
    queue = None
    cur_sid = None
    centered = False
    paused = BooleanProperty(False)
    pause_start = 0
    paused_total = 0

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
            except ValueError:
                continue
            if "ev" in p:
                self.handle_event(p)
                continue
            try:
                lat = float(p["lat"])
                lon = float(p["lon"])
                ts = float(p.get("ts", 0))
                sid = p.get("seg", 0)
            except (ValueError, KeyError, TypeError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue
            if ts < self.started_at - 1:
                continue
            hasil.append((lat, lon, ts, sid))
        return hasil

    def handle_event(self, p):
        try:
            ts = float(p.get("ts", time.time()))
        except (ValueError, TypeError):
            return
        ev = p.get("ev")
        if ev == "pause" and not self.paused:
            self.paused = True
            self.pause_start = ts
        elif ev == "resume" and self.paused:
            self.paused_total += max(0, ts - self.pause_start)
            self.paused = False

    def poll_location(self, dt):
        for titik in self.read_new_points():
            self.queue.append(titik)

    def animate(self, dt):
        now = time.monotonic()

        if self.seg is None:
            if not self.queue:
                return

            lat, lon, ts, sid = self.queue.popleft()
            if sid != self.cur_sid or self.marker_pos is None:
                self.cur_sid = sid
                self.ids.track_line.break_line()
                self.marker_pos = (lat, lon)
                self.last_play_ts = ts
                self.ids.track_line.add_point(lat, lon)
                self.show(lat, lon)
                if not self.centered:
                    self.centered = True
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
        self.cur_sid = None
        self.centered = False
        self.paused = False
        self.pause_start = 0
        self.paused_total = 0
        self.ids.track_line.clear()

        try:
            path = Paths.database(LIVE_FILE)
            open(path, "ab").close()
            self._offset = os.path.getsize(path)
        except OSError as e:
            print("[record] gagal siapkan file track:", e)
            self._offset = 0

        self._schedule()

    def resume_timers(self):
        pending = []
        if self.seg:
            pending.append((*self.seg[1], 0, self.cur_sid))
        pending += list(self.queue)
        pending += self.read_new_points()

        self.queue = deque()
        self.seg = None

        if pending:
            for lat, lon, _, sid in pending:
                if sid != self.cur_sid:
                    self.ids.track_line.break_line()
                    self.cur_sid = sid
                self.ids.track_line.add_point(lat, lon)
            lat, lon, ts, _ = pending[-1]
            self.marker_pos = (lat, lon)
            self.last_play_ts = ts
            self.show(lat, lon)

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
        now = time.time()
        diam = self.paused_total + (now - self.pause_start if self.paused else 0)
        detik = int(max(0, now - self.started_at - diam))
        jam, sisa = divmod(detik, 3600)
        menit, detik = divmod(sisa, 60)

        if self.marker_pos:
            posisi = f"{self.marker_pos[0]:.5f}, {self.marker_pos[1]:.5f}"
        else:
            posisi = "Menunggu GPS..."

        waktu = f"{jam:02d}:{menit:02d}:{detik:02d}"
        if self.paused:
            waktu += "  (jeda otomatis)"
        self.status.text = f"{waktu}\n{posisi}"

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