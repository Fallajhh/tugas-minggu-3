import content.config.config
from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp

from content.page.Manager.page import Manager


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        return Manager()

    def on_start(self):
        if platform != "android":
            Clock.schedule_once(lambda dt: Clock.schedule_once(lambda dt: Window.show(), 0), 0)
        else:
            Clock.schedule_once(self.ask_permissions, 1)

    def ask_permissions(self, dt):
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
            Permission.POST_NOTIFICATIONS,
        ])


    def on_pause(self):
        return True


MainApp().run()