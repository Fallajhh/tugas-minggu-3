import content.config.config   # paling atas

from kivymd.app import MDApp

from content._components.Navbar import NavBar
from content.page.Home.page import Home
from content.page.Map.page import Map
from content.page.Record.page import Record
from content.page.Time.page import Time
from content.page.Profile.page import Profile
from content.page.Manager.page import Manager

class MainApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Light"
        return Manager()


MainApp().run()