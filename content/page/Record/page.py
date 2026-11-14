from kivy.lang import Builder
from kivy.uix.modalview import ModalView
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from content.util.paths import Paths



class RecordModal(ModalView):
    started = False

    def on_start(self):
        self.started = True
        print("start")
        self.dismiss()

    def on_dismiss(self):
        if not self.started:
            app = MDApp.get_running_app()
            app.root.ids.screen_manager.current = "Home"
            app.root.ids.navbar.select("Home")


class Record(MDScreen):
    pass


Builder.load_file(Paths.file("page", "Record", "page.kv"))
