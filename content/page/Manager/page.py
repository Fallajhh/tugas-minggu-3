from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout




from content.util.paths import Paths


class Manager(MDBoxLayout):
    pass


Builder.load_file(Paths.file("page","Manager","page.kv"))