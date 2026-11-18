import content.config.config

from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty
from kivymd.app import MDApp

from content.page.Manager.page import Manager
from content.util.insets import get_system_insets


class MainApp(MDApp):

    inset_top = NumericProperty(0)
    inset_bottom = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.location_permission_granted = False
        self.fine_location_granted = False
        self.notification_permission_granted = False

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.update_insets()
        Window.bind(size=self.update_insets)
        return Manager()

    def update_insets(self, *args):
        self.inset_top, self.inset_bottom = get_system_insets()

    def on_start(self):
        Clock.schedule_once(self.update_insets, 0.5)

        if platform != "android":
            Clock.schedule_once(
                lambda dt: Clock.schedule_once(
                    lambda dt: Window.show(), 0
                ),
                0
            )
            return

        Clock.schedule_once(self.ask_permissions, 1)

    # --------------------------------------------------
    # Permissions
    # --------------------------------------------------
    def ask_permissions(self, dt=None):
        if platform != "android":
            return

        try:
            from android.permissions import request_permissions
            from jnius import autoclass

            BuildVersion = autoclass("android.os.Build$VERSION")
            sdk_version = BuildVersion.SDK_INT

            permissions = [
                "android.permission.ACCESS_FINE_LOCATION",
                "android.permission.ACCESS_COARSE_LOCATION",
            ]

            if sdk_version >= 33:
                permissions.append(
                    "android.permission.POST_NOTIFICATIONS"
                )

            request_permissions(
                permissions,
                self.on_permissions_result
            )

        except Exception as e:
            print(f"[PERMISSION ERROR] {e}")

    def on_permissions_result(self, permissions, grants):
        permission_results = dict(zip(permissions, grants))

        fine = permission_results.get(
            "android.permission.ACCESS_FINE_LOCATION",
            False
        )

        coarse = permission_results.get(
            "android.permission.ACCESS_COARSE_LOCATION",
            False
        )

        notification = permission_results.get(
            "android.permission.POST_NOTIFICATIONS",
            True
        )

        self.fine_location_granted = bool(fine)
        self.location_permission_granted = bool(fine or coarse)
        self.notification_permission_granted = bool(notification)

        print("[PERMISSION] Fine location:", self.fine_location_granted)
        print("[PERMISSION] Coarse location:", bool(coarse))
        print("[PERMISSION] Location granted:", self.location_permission_granted)
        print("[PERMISSION] Notification:", self.notification_permission_granted)

        if not self.location_permission_granted:
            print("[WARNING] Izin lokasi belum diberikan.")

        if not self.fine_location_granted:
            print("[WARNING] GPS presisi belum diberikan.")

    # --------------------------------------------------
    # App lifecycle
    # --------------------------------------------------
    def on_pause(self):
        return True

    def on_resume(self):
        Clock.schedule_once(self.update_insets, 0.2)

        if platform == "android":
            print("[APP] Application resumed.")

    def on_stop(self):
        print("[APP] Application stopped.")


MainApp().run()