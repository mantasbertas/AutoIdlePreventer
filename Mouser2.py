from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox, QSystemTrayIcon, QCheckBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal, QObject
import pyautogui
import random
import sys
import keyboard as kb
import time
from pynput import mouse, keyboard
from pynput.keyboard import Listener as KeyboardListener


from pynput import keyboard

from pynput import keyboard

class MouseMonitor(QObject):
    activity_detected = pyqtSignal()
    activity_idle = pyqtSignal()

    def __init__(self, get_idle_interval_func):
        super().__init__()
        self.get_idle_interval = get_idle_interval_func
        self.last_position = None
        self.last_key_pressed = None
        self.activity_idle_time = self.get_idle_interval()
        self.check_idle_timer = QTimer()
        self.check_idle_timer.timeout.connect(self.check_if_activity_is_idle)
        self.check_idle_timer.start(1000)  # check every second

        # Start mouse listener
        self.mouse_listener = mouse.Listener(on_move=self.on_move)
        self.mouse_listener.start()

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

    def on_move(self, x, y):
        self.last_position = (x, y)
        self.activity_detected.emit()

    def on_key_press(self, key):
        self.last_key_pressed = key
        self.activity_detected.emit()

    def check_if_activity_is_idle(self):
        # Check if either mouse or keyboard activity detected
        if self.last_position == pyautogui.position() and self.last_key_pressed is None:
            self.activity_idle_time -= 1
            if self.activity_idle_time <= 0:
                self.activity_idle.emit()
                self.activity_idle_time = self.get_idle_interval()
        else:
            self.last_position = pyautogui.position()
            self.last_key_pressed = None
            self.activity_idle_time = self.get_idle_interval()



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

        self.mouse_monitor = MouseMonitor(self.get_idle_interval)
        self.mouse_monitor.activity_detected.connect(self.stop_moving)
        self.mouse_monitor.activity_idle.connect(self.start_moving)

        self.mouse_monitor_thread = QThread()
        self.mouse_monitor.moveToThread(self.mouse_monitor_thread)
        # self.mouse_monitor_thread.started.connect(self.mouse_monitor.start)
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

        self.label_idle_interval = QLabel("Select Idle Interval:")
        self.layout.addWidget(self.label_idle_interval)

        self.combo_idle_interval = QComboBox()
        self.combo_idle_interval.addItems(["10", "30", "300"])
        self.layout.addWidget(self.combo_idle_interval)

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

        self.setFixedWidth(200)

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

    def get_idle_interval(self):
        return int(self.combo_idle_interval.currentText())

    def update_timer(self):
        elapsed_time = int(time.time() - self.start_time)
        self.label_timer.setText(f"Total Time Running: {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")

def handle_q_key(e):
    window.request_stop.emit()

if __name__ == "__main__":
    kb.on_press_key('q', handle_q_key)

    app = QApplication(sys.argv)
    window = MyApp()
    window.setWindowFlags(Qt.WindowStaysOnTopHint)
    window.show()

    sys.exit(app.exec_())
