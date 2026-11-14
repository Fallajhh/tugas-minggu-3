import content.config.config
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp

from content.page.Manager.page import Manager


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        return Manager()

    def on_start(self):
        Clock.schedule_once(lambda dt: Clock.schedule_once(lambda dt: Window.show(), 0), 0)


MainApp().run()