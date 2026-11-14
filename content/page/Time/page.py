from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from content.util.paths import Paths


class Time(MDScreen):
    pass


Builder.load_file(Paths.file("page", "Time", "page.kv"))
