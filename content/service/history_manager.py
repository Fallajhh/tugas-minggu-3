import time

from content.util.math_location import path_length
from content.util.paths import Paths

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


class HistoryManager:
    MAX_ITEMS = 100 

    @staticmethod
    def load():
        data = Paths.read_json(Paths.HISTORY)
        return data if isinstance(data, list) else []

    @staticmethod
    def add(started_at, ended_at, paused_s, segments):
        clean = []
        for seg in segments:
            pts = [[round(lat, 6), round(lon, 6)] for lat, lon in seg]
            if pts:
                clean.append(pts)

        total_points = sum(len(seg) for seg in clean)
        if total_points < 2:
            return None

        distance = path_length(clean)

        start = clean[0][0]
        end = clean[-1][-1]

        lt = time.localtime(started_at)
        day = DAYS[lt.tm_wday]
        date_text = f"{lt.tm_mday} {MONTHS[lt.tm_mon - 1]} {lt.tm_year}"

        elapsed = max(0, int(ended_at - started_at))
        active = max(0, int(elapsed - paused_s))

        entry = {
            "id": int(started_at),
            "name": f"Rute {day}, {date_text}",
            "day": day,
            "date": time.strftime("%Y-%m-%d", lt),
            "start_time": time.strftime("%H:%M:%S", lt),
            "end_time": time.strftime("%H:%M:%S", time.localtime(ended_at)),
            "started_at": started_at,
            "ended_at": ended_at,
            "elapsed_s": elapsed,
            "duration_s": active,
            "distance_m": round(distance, 1),
            "start": {"lat": start[0], "lon": start[1]},
            "destination": {"lat": end[0], "lon": end[1]},
            "segments": clean,
        }

        history = HistoryManager.load()
        history.insert(0, entry)
        Paths.write_json(history[:HistoryManager.MAX_ITEMS], Paths.HISTORY)
        return entry

    @staticmethod
    def delete(entry_id):
        history = [h for h in HistoryManager.load() if h.get("id") != entry_id]
        Paths.write_json(history, Paths.HISTORY)