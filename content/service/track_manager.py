from kivy.utils import platform


class TrackManager:

    @staticmethod
    def _service():
        from android import mActivity
        from jnius import autoclass
        name = mActivity.getPackageName() + ".ServiceTracker"
        return mActivity, autoclass(name)

    @staticmethod
    def start():
        if platform != "android":
            print("[TrackManager] bukan Android, service tidak dinyalakan")
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
            return
        try:
            activity, service = TrackManager._service()
            service.stop(activity)
        except Exception as e:
            print("[TrackManager] gagal stop:", repr(e))