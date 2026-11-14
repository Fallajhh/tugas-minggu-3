from kivy.config import Config


Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', '0')

from kivy.core.window import Window


Window.clearcolor = (1, 1, 1, 1)


API_KEY_MAP = "d7aca19f-21d5-46ad-a797-10831ea5cd14"