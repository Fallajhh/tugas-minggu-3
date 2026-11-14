import os


class Paths:
    BASE_DIR = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    CONTENT_DIR = os.path.join(BASE_DIR, "content")
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")

    @classmethod
    def asset(cls, *parts):
        path = os.path.join(cls.ASSETS_DIR, *parts)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Asset tidak ditemukan: {path}")
        return path


    @classmethod
    def file(cls, *parts):
        path = os.path.join(cls.CONTENT_DIR, *parts)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File tidak ditemukan: {path}")
        return path