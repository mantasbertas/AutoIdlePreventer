from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QSystemTrayIcon, QCheckBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal, QObject
import pyautogui
import random
import sys
import keyboard
import time
from pynput import mouse

class MouseMonitor(QObject):
    mouse_moved = pyqtSignal()
    mouse_idle = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.last_position = None
        self.mouse_idle_time = 10  # in seconds
        self.check_idle_timer = QTimer()
        self.check_idle_timer.timeout.connect(self.check_if_mouse_is_idle)
        self.check_idle_timer.start(1000)  # check every second

    def start(self):
        with mouse.Listener(on_move=self.on_move) as self.listener:
            self.listener.join()

    def on_move(self, x, y):
        self.last_position = (x, y)
        self.mouse_moved.emit()

    def check_if_mouse_is_idle(self):
        if self.last_position == pyautogui.position():
            self.mouse_idle_time -= 1
            if self.mouse_idle_time <= 0:
                self.mouse_idle.emit()
                self.mouse_idle_time = 10  # reset the timer
        else:
            self.last_position = pyautogui.position()
            self.mouse_idle_time = 10  # reset the timer

class Worker(QThread):
    def __init__(self, speed, interval, alt_tab_enabled):
        super().__init__()
        self.speed = speed
        self.interval = interval
        self.alt_tab_enabled = alt_tab_enabled
        self.is_running = True

    def run(self):
        # Define the coordinates of the center of the restricted region
        center_x = pyautogui.size()[0] // 2
        center_y = pyautogui.size()[1] // 2

        # Define the size of the restricted region
        region_size = 200

        # Calculate the boundaries of the restricted region
        left = center_x - region_size // 2
        top = center_y - region_size // 2
        right = center_x + region_size // 2
        bottom = center_y + region_size // 2
        move_counter = 0

        while self.is_running:
            # Calculate a random position within the restricted region
            new_x = random.randint(left, right)
            new_y = random.randint(top, bottom)

            # Move cursor to new position
            pyautogui.moveTo(new_x, new_y, duration=self.speed)

            # Alt tab if 10th move
            move_counter += 1
            if self.alt_tab_enabled and move_counter >= 10:
                keyboard.press_and_release('alt+tab')
                move_counter = 0

            # Generate a random interval based on the selected option
            if self.interval == "Short":
                interval = random.uniform(0.5, 1)
            elif self.interval == "Medium":
                interval = random.uniform(1, 2)
            elif self.interval == "Long":
                interval = random.uniform(2, 3)

            # Pause before next move
            time.sleep(interval)

    def stop(self):
        self.is_running = False

class MyApp(QWidget):
    request_stop = pyqtSignal()
    request_start = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.initUI()
        self.worker = None
        self.start_time = None
        self.request_stop.connect(self.stop_moving)

        self.mouse_monitor = MouseMonitor()
        self.mouse_monitor.mouse_moved.connect(self.stop_moving)
        self.mouse_monitor.mouse_idle.connect(self.start_moving)

        self.mouse_monitor_thread = QThread()
        self.mouse_monitor.moveToThread(self.mouse_monitor_thread)
        self.mouse_monitor_thread.started.connect(self.mouse_monitor.start)
        self.mouse_monitor_thread.start()

    def initUI(self):
        self.setWindowTitle("Porco Rosso")
        self.setWindowIcon(QIcon("porco.ico"))

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("porco.ico"))

        self.layout = QVBoxLayout()

        self.label_speed = QLabel("Select Movement Speed:")
        self.layout.addWidget(self.label_speed)

        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.25", "0.5", "1"])
        self.layout.addWidget(self.combo_speed)

        self.label_interval = QLabel("Select Movement Interval:")
        self.layout.addWidget(self.label_interval)

        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["Short", "Medium", "Long"])
        self.layout.addWidget(self.combo_interval)

        self.checkbox_alt_tab = QCheckBox("Enable Alt-Tab")
        self.layout.addWidget(self.checkbox_alt_tab)

        self.button_start = QPushButton("Start Moving")
        self.button_start.clicked.connect(self.start_moving)
        self.layout.addWidget(self.button_start)

        self.button_stop = QPushButton("Stop Moving")
        self.button_stop.clicked.connect(self.stop_moving)
        self.layout.addWidget(self.button_stop)

        self.label_timer = QLabel("Total Time Running: 00:00:00")
        self.layout.addWidget(self.label_timer)

        self.setLayout(self.layout)

    def start_moving(self):
        if self.worker and self.worker.isRunning():
            return

        speed = float(self.combo_speed.currentText())
        interval = self.combo_interval.currentText()
        alt_tab_enabled = self.checkbox_alt_tab.isChecked()

        self.worker = Worker(speed, interval, alt_tab_enabled)
        self.worker.start()

        self.start_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)  # Update every second

    def stop_moving(self):
        if self.worker is not None:
            self.worker.stop()
            self.timer.stop()
            self.label_timer.setText("Total Time Running: 00:00:00")

    def update_timer(self):
        elapsed_time = int(time.time() - self.start_time)
        self.label_timer.setText(f"Total Time Running: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")

def handle_q_key(e):
    window.request_stop.emit()

if __name__ == "__main__":
    keyboard.on_press_key('q', handle_q_key)

    app = QApplication(sys.argv)
    window = MyApp()
    window.setWindowFlags(Qt.WindowStaysOnTopHint)
    window.show()

    sys.exit(app.exec_())
