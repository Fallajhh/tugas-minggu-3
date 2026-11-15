import subprocess
import sys

from kivy.utils import platform

from content.util.paths import Paths


class TrackManager:
    _proc = None  # hanya dipakai di desktop (mode tes)

    @staticmethod
    def _service():
        from android import mActivity
        from jnius import autoclass

        name = mActivity.getPackageName() + ".ServiceTracker"
        return mActivity, autoclass(name)

    @staticmethod
    def start():
        if platform != "android":
            try:
                TrackManager._proc = subprocess.Popen(
                    [sys.executable, Paths.file("service", "tracker.py")]
                )
                print("[TrackManager] desktop: tracker tes dijalankan")
            except Exception as e:
                print("[TrackManager] gagal start tracker tes:", repr(e))
            return

        try:
            activity, service = TrackManager._service()
            service.start(activity, "")
            print("[TrackManager] service dinyalakan")
        except Exception as e:
            print("[TrackManager] gagal start:", repr(e))

    @staticmethod
    def stop():
        if platform != "android":
            proc = TrackManager._proc
            if proc and proc.poll() is None:
                proc.terminate()
            TrackManager._proc = None
            return

        try:
            activity, service = TrackManager._service()
            service.stop(activity)
            print("[TrackManager] service dihentikan")
        except Exception as e:
            print("[TrackManager] gagal stop:", repr(e))