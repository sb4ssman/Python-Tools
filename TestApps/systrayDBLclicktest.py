# testscript2  


""" @JulienFr
JulienFr commented on Jan 12 • 
You do not need to add this double-click behavior in pystray.
You can overwrite pystray._win32.Icon. _on_notify callback with any behavior in an pystray._win32.Icon subclass.
This does a new Icon backend that you instantiate only on e.g. win32 platform.

...
if lparam == win32.WM_LBUTTONDBLCLK:
    # your custom behavior from e.g. tkinter
@daveblackuk
daveblackuk commented on Feb 4
Julien,

useful, can you please provide a full code example.

Thanks

@JulienFr
JulienFr commented on Feb 4
Win32PystrayIcon is used in case of win32 sys platform.
It triggers the on_double_click callback defined in the global Icon instance, when the left double-click is detected from win32 on notify event. """

from PIL import Image
import threading, io, base64, sys
from pystray import Icon, Menu, MenuItem

APP_ICON2 = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlz\nAAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKfSURB\nVDiNZdNfaNVlHAbwz/n9zu/M6Vz7o41yzplg4BCFolbZWi2FiBIMvQq9qJAuCokugqCWFAgJxSgS\n+kN5Uxb9uVJyVgc0wgg65UpczLl2HHPacM7z23bmOaeLnU6bvlcP7/s8z/d5X94n4Ya1dz3Fp9GF\n1vLmORzDB3T3zWcn/oc9VYy/hd3tssEWAxrErgmNqpHW6he3FnAAL9Cdn2fQU8X4keXiB/f7Vrus\nvFBOSiwSi8wI9Wv0pvuMq/4ej9CdD+cM7n5nmXj7576wsTaW7HpIPEtuqiBXCORErkoJlHT420nN\nq6cl60kfSZTvnPnYN8H9hjR8ckDdzh3Ge08I6m7y444XXTw3VkmSkzItaZ9NBYINIQ+83C7b/pyT\n8ktqBW1trmROyzy7V76YkGxeIZs5WxHHIqGiCYuCC5bMJPHwFgPyQqWWVv2v9ohFZmvrrdy51eFt\nLy0Qz+HF1rvgd02bA7Q0mhKLXDo9VCHd/voembcPuThyuSKeSVXLlc+TirAqQOmaxHUTIi3bugxn\nzspJKdXVe+y9PfZPfqnj+a1zCQVQSmJ4VM26+eJYZOzUgMe/3mes/7zGtSt99cqnzvx23rK1K8Qi\n0VyC4SR6f7B63T2GK+JY5ND217Q8usn4pdip42dM5BOeeONJhw/+pEZev0Y4GtKZHbF090ajQaBU\nMbiSDwz+MWJ48B+ThVAssripwWQ+ITk0qNeaAp4JSY/RefOvbrmrw5BJVTe8x3+4r2/MnctnfTTS\nZEbyXboPln9i57Ep0b0/a75tg1GBksuqF4iXmtFs0ocjTSYs+g67SBfKBukCnZ9NiepPWHXHVVVB\nvWlVCiJFoZK/NDpqTWFusl3XlWlBndsoPoXN5TonMFiu8/t0/zmf/S9tcxBW9J/R4gAAAABJRU5E\nrkJggg==\n'


class Win32PystrayIcon(Icon):
	WM_LBUTTONDBLCLK = 0x0203

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if 'on_double_click' in kwargs:
			self.on_double_click = kwargs['on_double_click']

	def _on_notify(self, wparam, lparam):
		super()._on_notify(wparam, lparam)
		if lparam == self.WM_LBUTTONDBLCLK:
			self.on_double_click(self, None)


if sys.platform == 'win32':
	Icon = Win32PystrayIcon


def create_image():
	buffer = io.BytesIO(base64.b64decode(APP_ICON2))
	img = Image.open(buffer)
	return img


def quit(icon, item):
	icon.stop()


def show():
	print('show main window')


def create_icon():
	# i can use one click using default=True, but no option for double-click
	menu = Menu(
		MenuItem("Start / Show", show, default=True), MenuItem(
			"Minimize to Systray",
			lambda: None
		), MenuItem("Close to Systray", lambda: None), MenuItem("Quit", quit)
	)
	icon = Icon(
		'test', create_image(), menu=menu,
		**{
			'on_double_click': lambda icon, _: print('double-clicked!')
		} if sys.platform == "win32" else {}
	)
	return icon


def foo():
	print('start icon')
	icon = create_icon()
	icon.run()


threading.Thread(target=foo).start()