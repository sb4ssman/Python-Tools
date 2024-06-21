# testscript1

#Made a function that Shows tkinter window when tray icon is double clicked.
# Might be helpful in implementing it into Pystray.

# You can call the function using Thread which will show and hide/destroy Tkinter main window when clicking menu buttons or double clicking the icon.

import tkinter
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon


def Tray_Icon():
    def close_tray_icon():
        root.deiconify()
        tray_icon.hide()
        app.exit()
        sys.exit()
    def onDoubleClick(reason):
        if reason == QSystemTrayIcon.DoubleClick:
            root.deiconify()
            tray_icon.hide()
            app.exit()
            sys.exit()

    root.withdraw()
    app = QApplication(sys.argv)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon('icon.png'))

    menu = QMenu()
    menu.addAction("Show").triggered.connect(lambda: close_tray_icon())
    menu.addAction("Exit").triggered.connect(lambda: root.destroy())
    tray_icon.activated.connect(onDoubleClick)

    tray_icon.setContextMenu(menu)
    tray_icon.show()
    sys.exit(app.exec_())


root = tkinter.Tk()
root.title("MyTKinterProgram")
root.geometry('720x940')
root.protocol('WM_DELETE_WINDOW', lambda: Thread(target=Tray_Icon,daemon=True).start())
root.mainloop()


