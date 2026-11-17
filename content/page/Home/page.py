from datetime import datetime

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.modalview import ModalView

from kivymd.uix.screen import MDScreen

from content.util.paths import Paths
from content.service.profile_manager import Profiles


class ModalCreateProfile(ModalView):

    auto_dismiss = False

    def save(self):
        nama = self.ids.nama.text.strip()
        tanggal = self.ids.tanggal.text.strip()
        berat = self.ids.berat.text.strip()
        tinggi = self.ids.tinggi.text.strip()

        nama_ok = bool(nama)

        try:
            datetime.strptime(tanggal, "%d/%m/%Y")
            tanggal_ok = True
        except (ValueError, TypeError):
            tanggal_ok = False

        try:
            berat_value = float(berat)
            berat_ok = berat_value > 0
        except (ValueError, TypeError):
            berat_value = 0
            berat_ok = False

        try:
            tinggi_value = float(tinggi)
            tinggi_ok = tinggi_value > 0
        except (ValueError, TypeError):
            tinggi_value = 0
            tinggi_ok = False

        self.ids.nama.error = not nama_ok
        self.ids.tanggal.error = not tanggal_ok
        self.ids.berat.error = not berat_ok
        self.ids.tinggi.error = not tinggi_ok

        if not all((nama_ok, tanggal_ok, berat_ok, tinggi_ok)):
            return

        try:
            Profiles.CreateData(
                nama,
                tanggal,
                berat_value,
                tinggi_value
            )
        except Exception as e:
            print(f"[ERROR] Gagal menyimpan profil: {e}")
            return

        self.dismiss()
        


class Home(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_modal = None
        self.profile_event = None

    def on_enter(self, *args):

        if Profiles.Exists():
            return

        if self.profile_modal and self.profile_modal.parent:
            return

        if self.profile_event:
            self.profile_event.cancel()

        self.profile_event = Clock.schedule_once(
            self.show_profile_modal,
            0.2
        )

    def show_profile_modal(self, dt):

        self.profile_event = None

        if Profiles.Exists():
            return

        if self.profile_modal and self.profile_modal.parent:
            return

        self.profile_modal = ModalCreateProfile()
        self.profile_modal.open()


Builder.load_file(
    Paths.file("page", "Home", "page.kv")
)