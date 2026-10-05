# =============================================================================
# greenboard — ВИЗУАЛЬНЫЙ МОКАП (пустышка) дашборда управления видеокартой.
# Никакой реальной логики — только вёрстка и фейковые данные,
# чтобы оценить, как будет выглядеть будущее приложение.
# =============================================================================

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget,
    QMainWindow, QProgressBar, QPushButton, QSlider, QStackedWidget,
    QVBoxLayout, QWidget,
)

GREEN = "#76B900"
DARK = "#0a0a0c"

QSS = f"""
* {{
    font-family: 'Inter','Roboto','Cantarell','Ubuntu','DejaVu Sans','Noto Sans',sans-serif;
    color: #d1d1d1;
    outline: none;
}}
QMainWindow, QWidget#rootWidget {{ background-color: {DARK}; }}
QWidget#sidebarWidget {{ background-color: #101013; border-right: 1px solid #1a1a1e; }}
QWidget#headerBar {{ background-color: #101013; border-bottom: 1px solid #1a1a1e; }}
QLabel#brandLabel {{ color: {GREEN}; font-size: 20px; font-weight: bold; }}
QLabel#subtitleLabel {{ color: #9e9e9e; font-size: 13px; }}
QListWidget#sidebarList {{ background: transparent; border: none; }}
QListWidget#sidebarList::item {{
    color: #9e9e9e; height: 40px; padding-left: 12px; border-radius: 6px;
    margin: 2px 8px; font-size: 14px;
}}
QListWidget#sidebarList::item:hover {{ color: #d1d1d1; background: #1a1a1e; }}
QListWidget#sidebarList::item:selected {{
    color: #ffffff; background-color: rgba(118,185,0,0.22);
    border-left: 3px solid {GREEN}; font-weight: bold;
}}
QWidget#card {{ background-color: #141417; border: 1px solid #26262b; border-radius: 10px; }}
QLabel#cardTitle {{ color: {GREEN}; font-weight: bold; font-size: 14px; }}
QLabel#valueLabel {{ color: #ffffff; font-weight: bold; }}
QLabel#hintLabel {{ color: #9e9e9e; font-size: 12px; }}
QLabel#statusLabel {{ font-size: 20px; font-weight: bold; }}
QPushButton {{
    background-color: #1a1a1e; color: #d1d1d1; border: 1px solid #33333a;
    border-radius: 8px; padding: 8px 16px; min-height: 32px; font-weight: bold;
}}
QPushButton:hover {{ border-color: {GREEN}; background-color: #222226; }}
QPushButton:disabled {{ color: #616161; border-color: #26262b; background: #101013; }}
QPushButton[primary="true"] {{ background-color: rgba(118,185,0,0.18); border-color: {GREEN}; color: {GREEN}; }}
QPushButton[primary="true"]:hover {{ background-color: rgba(118,185,0,0.28); }}
QComboBox {{
    background: #0a0a0c; border: 1px solid #26262b; border-radius: 8px;
    padding: 6px 10px; min-height: 30px;
}}
QProgressBar {{
    border: 1px solid #26262b; border-radius: 6px; background: #0a0a0c; text-align: center;
    color: #d1d1d1; height: 18px;
}}
QProgressBar::chunk {{ background-color: {GREEN}; border-radius: 5px; }}
QSlider::groove:horizontal {{ height: 6px; background: #26262b; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {GREEN}; width: 16px; margin: -5px 0; border-radius: 8px; }}
"""


def card():
    c = QFrame()
    c.setObjectName("card")
    lay = QVBoxLayout(c)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    return c, lay


def title(text):
    l = QLabel(text)
    l.setObjectName("cardTitle")
    return l


def row(lay, left, right):
    r = QWidget()
    h = QHBoxLayout(r)
    h.setContentsMargins(0, 0, 0, 0)
    ll = QLabel(left)
    ll.setStyleSheet("color:#9e9e9e;")
    h.addWidget(ll)
    h.addStretch()
    if isinstance(right, str):
        rv = QLabel(right)
        rv.setObjectName("valueLabel")
        h.addWidget(rv)
    else:
        h.addWidget(right)
    lay.addWidget(r)
    return r


def hint(lay, text):
    h = QLabel(text)
    h.setObjectName("hintLabel")
    h.setWordWrap(True)
    lay.addWidget(h)


# ------------------- страницы -------------------

def page_driver():
    c, lay = card()
    lay.addWidget(title("Драйвер NVIDIA"))

    lay.addWidget(QLabel("GeForce GTX 1050 Ti"))
    row(lay, "Установленный драйвер", "nvidia-dkms 570.86.16")
    row(lay, "Доступно в репозитории", "570.86.16 (актуально)")
    row(lay, "Ядро", "linux 7.1.3-arch1-2")

    lay.addWidget(title("Сборка под ядра (DKMS)"))
    row(lay, "linux", "✓ собран")
    row(lay, "linux-lts", "✓ собран")
    row(lay, "linux-headers", "установлены")
    row(lay, "linux-lts-headers", "установлены")

    btn_row = QWidget()
    h = QHBoxLayout(btn_row)
    h.setContentsMargins(0, 0, 0, 0)
    b1 = QPushButton("Проверить обновления")
    b2 = QPushButton("Обновить драйвер")
    b2.setProperty("primary", True)
    h.addWidget(b1)
    h.addWidget(b2)
    h.addStretch()
    lay.addWidget(btn_row)
    hint(lay, "Обновление выполняется через pacman (одна транзакция), после — пересборка initramfs и перезагрузка.")
    lay.addStretch()
    return c


def page_monitor():
    c, lay = card()
    lay.addWidget(title("Мониторинг"))
    row(lay, "Температура", "54 °C")
    bar = QProgressBar(); bar.setValue(54); bar.setFormat("54 °C"); lay.addWidget(bar)
    row(lay, "Частота GPU", "1500 МГц")
    row(lay, "Частота памяти", "3504 МГц")
    row(lay, "Потребление", "60 / 75 Вт")
    bar2 = QProgressBar(); bar2.setValue(80); bar2.setFormat("60 Вт"); lay.addWidget(bar2)
    row(lay, "Вентиляторы", "38 % (только чтение)")
    row(lay, "Загрузка GPU", "42 %")
    lay.addStretch()
    return c


def page_power():
    c, lay = card()
    lay.addWidget(title("Мощность и вентиляторы"))
    row(lay, "Лимит мощности", "75 Вт")
    s = QSlider(Qt.Horizontal)
    s.setRange(50, 100)
    s.setValue(75)
    lay.addWidget(s)
    hint(lay, "Лимит мощности работает и на Wayland, и на Xorg (нужны права root).")
    lay.addWidget(title("Разгон и кривая вентиляторов"))
    hint(lay, "⚠ Только Xorg: fan-контроль и офсеты частот через nvidia-settings (нужен coolbits). На Wayland эта часть недоступна.")
    b = QPushButton("Настроить кривую вентиляторов (Xorg)")
    b.setEnabled(False)
    lay.addWidget(b)
    lay.addStretch()
    return c


def page_profiles():
    c, lay = card()
    lay.addWidget(title("Профили"))
    for name, desc in [
        ("Тихий", "лимит 65 Вт, вентиляторы — тихая кривая"),
        ("Игры", "лимит 75 Вт, макс. частота"),
        ("Макс. производительность", "лимит 75 Вт, офсет +150 МГц"),
    ]:
        r = QWidget()
        h = QHBoxLayout(r)
        h.setContentsMargins(0, 0, 0, 0)
        txt = QLabel(f"{name}\n<span style='color:#9e9e9e;font-size:12px;'>{desc}</span>")
        h.addWidget(txt, 1)
        b = QPushButton("Применить")
        b.setProperty("primary", True)
        h.addWidget(b)
        lay.addWidget(r)
    hint(lay, "Свой «профиль» = набор сохранённых настроек, применяется при запуске (не драйверный профиль).")
    lay.addStretch()
    return c


def page_record():
    c, lay = card()
    lay.addWidget(title("Запись и оверлей"))
    row(lay, "Оверлей (fps/темп)", QPushButton("Выкл"))
    row(lay, "Запись (NVENC)", QPushButton("Настроить"))
    row(lay, "Повтор (replay buffer)", QPushButton("Выкл"))
    hint(lay, "На Wayland захват идёт через PipeWire/dma-buf + NVENC (ffmpeg/OBS).")
    lay.addStretch()
    return c


PAGES = [
    ("📦 Драйвер", page_driver),
    ("📊 Мониторинг", page_monitor),
    ("⚡ Мощность/Разгон", page_power),
    ("🎮 Профили", page_profiles),
    ("🎥 Запись", page_record),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GreenBoard — GPU dashboard (mock)")
        self.resize(920, 600)
        self._build()

    def _build(self):
        root = QWidget()
        root.setObjectName("rootWidget")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())
        self._content_widget = self._content()
        body = QWidget()
        h = QHBoxLayout(body)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(self._sidebar())
        h.addWidget(self._content_widget, 1)
        outer.addWidget(body, 1)

    def _header(self):
        hb = QWidget()
        hb.setObjectName("headerBar")
        h = QHBoxLayout(hb)
        h.setContentsMargins(18, 10, 18, 10)
        b = QLabel("GreenBoard")
        b.setObjectName("brandLabel")
        s = QLabel("пульт управления видеокартой — визуальный мокап")
        s.setObjectName("subtitleLabel")
        h.addWidget(b)
        h.addSpacing(8)
        h.addWidget(s)
        h.addStretch()
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{GREEN}; font-size:16px;")
        h.addWidget(dot)
        return hb

    def _sidebar(self):
        side = QWidget()
        side.setObjectName("sidebarWidget")
        side.setFixedWidth(190)
        v = QVBoxLayout(side)
        v.setContentsMargins(8, 12, 8, 12)
        self.nav = QListWidget()
        self.nav.setObjectName("sidebarList")
        for name, _ in PAGES:
            self.nav.addItem(name)
        v.addWidget(self.nav, 1)
        foot = QLabel("greenboard · mock · без логики")
        foot.setStyleSheet("color:#616161;font-size:12px;")
        foot.setAlignment(Qt.AlignCenter)
        v.addWidget(foot)
        self.nav.currentRowChanged.connect(self._change)
        self.nav.setCurrentRow(0)
        return side

    def _content(self):
        self.stack = QStackedWidget()
        for _, fn in PAGES:
            self.stack.addWidget(fn())
        return self.stack

    def _change(self, row):
        self.stack.setCurrentIndex(row)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
