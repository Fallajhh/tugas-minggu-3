from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from content.util.paths import Paths
from content.service.profile import Profiles
from content.util.math_body_health import BodyMath


class Profile(MDScreen):

    def on_enter(self, *args):
        self.load_profile()

    def load_profile(self):
        data = Profiles.Read()

        nama = data.get("nama", "")
        tanggal_lahir = data.get("tanggal_lahir", "")
        berat = data.get("berat_badan", 0)
        tinggi = data.get("tinggi_badan", 0)

        self.ids.nama.text = f"Nama: {nama or '-'}"
        self.ids.tanggal_lahir.text = f"Tanggal lahir: {tanggal_lahir or '-'}"

        self.ids.berat.text = f"BB: {berat} kg"
        self.ids.tinggi.text = f"TB: {tinggi} cm"
        health = BodyMath.GetBodyHealth(
            tanggal_lahir,
            berat,
            tinggi
        )

        umur = health["umur"]
        imt = health["imt"]

        self.ids.umur.text = (
            f"Umur: {umur} tahun"
            if umur is not None else "Umur: Tidak diketahui"
        )

        self.show_result(
            imt if imt is not None else "-",
            health["kategori"],
        )

    def show_result(self, imt, kategori):
        self.ids.imt.text = str(imt)
        self.ids.kategori.text = f"Status: {kategori}"


Builder.load_file(Paths.file("page", "Profile", "page.kv"))