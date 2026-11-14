from kivy.lang import Builder
from kivy.properties import StringProperty,ColorProperty
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem,MDNavigationItemIcon

from content.util.paths import Paths

class NavBarItem(MDNavigationItem):
    icon = StringProperty()
    text = StringProperty()
    color_active = ColorProperty("#1E88E5") 
    color_inactive = ColorProperty("#1a1a1a")



class NavBar(MDNavigationBar):
    pass


Builder.load_file(Paths.file("_components", "Navbar.kv"))