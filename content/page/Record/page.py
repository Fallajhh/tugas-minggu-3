from datetime import datetime

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
        TrackManager.start()
        self.dismiss()

    def on_dismiss(self):
        if not self.started:
            app = MDApp.get_running_app()
            app.root.ids.screen_manager.current = "Home"
            app.root.ids.navbar.select("Home")
    
class Record(MDScreen):
    _timer = None

    def on_enter(self, *args):
        self.update_status()
        self._timer = Clock.schedule_interval(self.update_status, 1)

    def on_leave(self, *args):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def update_status(self, *args):
        data = Paths.read_json(Paths.LOG)
        points = data.get(datetime.now().strftime("%d/%m/%Y"), [])

        if not points:
            self.ids.status.text = "Menunggu GPS..."
            return

        last = points[-1]
        self.ids.status.text = (
            f"{last['time']}\n"
            f"{last['lat']:.5f}, {last['lon']:.5f}"
        )

    def stop_tracking(self):
        TrackManager.stop()
        self.ids.status.text = "Perekaman dihentikan"



Builder.load_file(Paths.file("page", "Record", "page.kv"))
