from kivy.utils import platform

SERVICE = "org.jagjag.app.ServiceTracker"   # package.domain + package.name + Service + Tracker


class TrackManager:

    @staticmethod
    def start():
        if platform != "android":
            print("[TrackManager] bukan Android, service tidak dinyalakan")
            return
        from android import mActivity
        from jnius import autoclass
        autoclass(SERVICE).start(mActivity, "")

    @staticmethod
    def stop():
        if platform != "android":
            return
        from android import mActivity
        from jnius import autoclass
        autoclass(SERVICE).stop(mActivity)