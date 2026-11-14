import content.config.config 
from kivymd.app import MDApp

from content.page.Manager.page import Manager


class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        return Manager()


MainApp().run()