import os
import time

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.modalview import ModalView
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


class Record(MDScreen):
    _timer = None
    _poll = None
    started_at = 0
    last_position = None
    camera_initialized = False

    def on_kv_post(self, base_widget):
        self.map_view = self.ids.map_view
        self.human_position = self.ids.human_position
        self.status = self.ids.status
        
        try:
            cache = os.path.join(
                MDApp.get_running_app().user_data_dir, "map_cache"
            )
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
        if p.get("ts", 0) < self.started_at:
            return
        self.on_location(
            lat=p.get("lat"), lon=p.get("lon"), accuracy=p.get("accuracy")
        )

    def on_location(self, **kwargs):
        latitude = kwargs.get("lat")
        longitude = kwargs.get("lon")

        if latitude is None or longitude is None:
            return

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            return

        if not (-90 <= latitude <= 90):
            return
        if not (-180 <= longitude <= 180):
            return

        self.last_position = (latitude, longitude)

        self.human_position.lat = latitude
        self.human_position.lon = longitude

        if not self.camera_initialized:
            self.map_view.center_on(latitude, longitude)
            self.camera_initialized = True

    def update_marker_scale(self, map_view, zoom):
        size = max(8, min(48, 24 * (2 ** (zoom - 14))))
        self.human_position.size = (size, size)

    def _cancel_clocks(self):
        for name in ("_timer", "_poll"):
            ev = getattr(self, name)
            if ev:
                ev.cancel()
                setattr(self, name, None)

    def start_timer(self):
        self.started_at = time.time()
        self.last_position = None
        self.camera_initialized = False

        self._cancel_clocks()
        self._timer = Clock.schedule_interval(self.tick, 1)
        self._poll = Clock.schedule_interval(self.poll_location, 1)

    def tick(self, dt):
        elapsed = int(time.time() - self.started_at)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)

        if self.last_position is not None:
            lat, lon = self.last_position
            position = f"{lat:.5f}, {lon:.5f}"
        else:
            position = "Menunggu GPS..."

        self.status.text = (
            f"{hours:02d}:{minutes:02d}:{seconds:02d}\n{position}"
        )

    def stop_tracking(self):
        TrackManager.stop()
        self._cancel_clocks()

        self.last_position = None
        self.camera_initialized = False
        self.status.text = "Perekaman dihentikan"

        app = MDApp.get_running_app()
        app.root.ids.screen_manager.current = "Home"
        app.root.ids.navbar.select("Home")

    def on_leave(self):
        self._cancel_clocks()


Builder.load_file(Paths.file("page", "Record", "page.kv"))