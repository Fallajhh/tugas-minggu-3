import os

from content.util.paths import Paths


class Profiles:
    FILE = Paths.PROFILE

    DEFAULT = {
        "nama": "",
        "tanggal_lahir": "",
        "berat_badan": 0,
        "tinggi_badan": 0,
    }

    _cache = None

    @classmethod
    def Exists(cls):
        return os.path.exists(Paths.database(cls.FILE))

    @classmethod
    def Read(cls):
        if cls._cache is None:
            data = Paths.read_json(cls.FILE)
            cls._cache = {**cls.DEFAULT, **(data if isinstance(data, dict) else {})}
        return dict(cls._cache)
    
    @classmethod
    def Update(cls, **perubahan):
        data = cls.Read()
        baru = {k: v for k, v in perubahan.items() if k in cls.DEFAULT}

        if all(data[k] == v for k, v in baru.items()):
            return data

        data.update(baru)
        Paths.write_json(data, cls.FILE)
        cls._cache = data
        return dict(data)

    @classmethod
    def CreateData(cls, nama="", tanggal_lahir="", berat_badan=0, tinggi_badan=0):
        if Paths.read_json(cls.FILE):
            return cls.Read()

        return cls.Update(
            nama=nama,
            tanggal_lahir=tanggal_lahir,
            berat_badan=berat_badan,
            tinggi_badan=tinggi_badan,
        )