import json
import os

from content.util.paths import Paths

class Profiles:
    FILE = "profiles.json"

    DEFAULT = {
        "nama": "",
        "tanggal_lahir": "",   # contoh: "14/11/2000"
        "berat_badan": 0,      # kg
        "tinggi_badan": 0,     # cm
    }

    @classmethod
    def Exists(cls):
        return os.path.exists(Paths.database(cls.FILE))

    @classmethod
    def _write(cls, data):
        path = Paths.database(cls.FILE)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    @classmethod
    def CreateData(cls, nama="", tanggal_lahir="", berat_badan=0, tinggi_badan=0):
        if cls.Exists():
            data = Paths.read_json(cls.FILE)
            if data:
                return data

        data = {
            "nama": nama,
            "tanggal_lahir": tanggal_lahir,
            "berat_badan": berat_badan,
            "tinggi_badan": tinggi_badan,
        }
        cls._write(data)
        return data

    @classmethod
    def Read(cls):
        data = Paths.read_json(cls.FILE)
        return {**cls.DEFAULT, **data}

    @classmethod
    def Update(cls, **perubahan):
        data = cls.Read()

        for kunci, nilai in perubahan.items():
            if kunci in cls.DEFAULT:
                data[kunci] = nilai

        cls._write(data)
        return data