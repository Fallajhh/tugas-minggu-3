from kivy.metrics import dp
from kivy.utils import platform

FALLBACK_TOP = dp(40)
FALLBACK_BOTTOM = 0
MAX_INSET = dp(120)


def _fallback():
    return FALLBACK_TOP, FALLBACK_BOTTOM


def _clamp(value):
    try:
        return int(max(0, min(float(value), MAX_INSET)))
    except (TypeError, ValueError):
        return 0


def _from_window_insets(activity, sdk_int):
    decor = activity.getWindow().getDecorView()
    insets = decor.getRootWindowInsets()

    if insets is None:
        return None

    if sdk_int >= 30:
        from jnius import autoclass

        Type = autoclass("android.view.WindowInsets$Type")
        bars = insets.getInsets(Type.systemBars() | Type.displayCutout())
        return bars.top, bars.bottom

    return insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetBottom()


def _from_resources(activity):
    res = activity.getResources()

    def dimen(name):
        rid = res.getIdentifier(name, "dimen", "android")
        return res.getDimensionPixelSize(rid) if rid > 0 else 0

    return dimen("status_bar_height"), dimen("navigation_bar_height")


def get_system_insets():
    if platform != "android":
        return _fallback()

    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        sdk_int = autoclass("android.os.Build$VERSION").SDK_INT

        result = None

        try:
            result = _from_window_insets(activity, sdk_int)
        except Exception as e:
            print("[insets] WindowInsets gagal:", e)

        if result is None:
            try:
                result = _from_resources(activity)
            except Exception as e:
                print("[insets] resource gagal:", e)

        if result is None:
            return _fallback()

        return _clamp(result[0]), _clamp(result[1])

    except Exception as e:
        print("[insets] gagal:", e)
        return _fallback()