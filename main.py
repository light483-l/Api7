import sys
from PyQt6 import uic
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QApplication, QLabel, QMainWindow,
                             QPushButton, QHBoxLayout, QWidget,
                             QLineEdit, QVBoxLayout)
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


class SearchLineEdit(QLineEdit):
    enterPressed = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.enterPressed.emit()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    g_map: QLabel
    press_delta = 0.1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('main_window.ui', self)

        self.map_zoom = 5
        self.map_ll = [37.977751, 55.757718]
        self.map_l = 'map'
        self.map_key = '5edfcff0-94a7-4c66-bbc0-f743141f39c6'
        self.current_marker = None
        self.show_marker = False

        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("Введите адрес для поиска")
        self.search_btn = QPushButton("Искать")
        self.reset_btn = QPushButton("Сбросить")

        self.light_btn = QPushButton('Светлая тема')
        self.dark_btn = QPushButton('Тёмная тема')

        for btn in [self.search_btn, self.reset_btn, self.light_btn, self.dark_btn]:
            btn.setFixedSize(120, 30)

        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_edit)
        self.search_layout.addWidget(self.search_btn)
        self.search_layout.addWidget(self.reset_btn)

        self.theme_layout = QHBoxLayout()
        self.theme_layout.addWidget(self.light_btn)
        self.theme_layout.addWidget(self.dark_btn)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.search_layout)
        self.main_layout.addWidget(self.g_map)
        self.main_layout.addLayout(self.theme_layout)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        self.search_btn.clicked.connect(self.search_object)
        self.search_edit.enterPressed.connect(self.search_object)
        self.reset_btn.clicked.connect(self.reset_search)  # Обработчик сброса
        self.light_btn.clicked.connect(self.set_light_theme)
        self.dark_btn.clicked.connect(self.set_dark_theme)

        self.g_map.setFocus()
        self.refresh_map()

    def reset_search(self):
        self.current_marker = None
        self.show_marker = False
        self.search_edit.clear()
        self.refresh_map()
        self.g_map.setFocus()

    def set_light_theme(self):
        self.map_l = 'map'
        self.refresh_map()
        self.g_map.setFocus()

    def set_dark_theme(self):
        self.map_l = 'skl'
        self.refresh_map()
        self.g_map.setFocus()

    def search_object(self):
        search_text = self.search_edit.text().strip()
        if not search_text:
            return

        try:
            geocoder_params = {
                "apikey": self.map_key,
                "geocode": search_text,
                "format": "json"
            }

            response = requests.get(
                "https://geocode-maps.yandex.ru/1.x/",
                params=geocoder_params
            )
            response.raise_for_status()

            json_data = response.json()
            feature = json_data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            pos = feature["Point"]["pos"].split()
            self.map_ll = [float(pos[0]), float(pos[1])]
            self.current_marker = f"{self.map_ll[0]},{self.map_ll[1]}"
            self.show_marker = True

            self.refresh_map()
            self.g_map.setFocus()

        except Exception as e:
            print(f"Ошибка при поиске объекта: {e}")
            self.g_map.setFocus()

    def keyPressEvent(self, event):
        if self.g_map.hasFocus():
            key = event.key()
            if key == Qt.Key.Key_PageUp and self.map_zoom < 17:
                self.map_zoom += 1
            if key == Qt.Key.Key_PageDown and self.map_zoom > 0:
                self.map_zoom -= 1
            if key == Qt.Key.Key_Left:
                self.map_ll[0] -= self.press_delta
            if key == Qt.Key.Key_Right:
                self.map_ll[0] += self.press_delta
            if key == Qt.Key.Key_Up:
                self.map_ll[1] += self.press_delta
            if key == Qt.Key.Key_Down:
                self.map_ll[1] -= self.press_delta

            self.refresh_map()
        else:
            super().keyPressEvent(event)

    def refresh_map(self):
        try:
            map_params = {
                "ll": f"{self.map_ll[0]},{self.map_ll[1]}",
                "l": self.map_l,
                "z": self.map_zoom,
            }

            if self.show_marker and self.current_marker:
                map_params["pt"] = f"{self.current_marker},pm2dgl"

            session = requests.Session()
            retry = Retry(total=10, connect=5, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            response = session.get(
                "https://static-maps.yandex.ru/1.x/",
                params=map_params
            )
            response.raise_for_status()

            with open("tmp.png", mode="wb") as tmp:
                tmp.write(response.content)

            pixmap = QPixmap()
            pixmap.load("tmp.png")
            self.g_map.setPixmap(pixmap)

        except Exception as e:
            print(f"Ошибка при загрузке карты: {e}")


app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec())
