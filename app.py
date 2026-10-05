#!/usr/bin/env python3
# =============================================================================
# GreenBoard — панель управления видеокартой (Linux).
# Реальный мониторинг через nvidia-smi; остальные вкладки пока мокап.
# =============================================================================

import sys

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QMainWindow, QProgressBar, QPushButton, QSlider, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

import backend

GREEN = "#76B900"
GREEN_DIM = "rgba(118,185,0,0.22)"
WARN = "#f5a623"
DARK = "#0b0d0a"
PANEL = "#12150f"
PANEL2 = "#171b12"
BORDER = "#2a2f24"

QSS = f"""
* {{ font-family:'Inter','Roboto','Cantarell','Ubuntu','DejaVu Sans','Noto Sans',sans-serif; color:#d7dcd3; outline:none; }}
QMainWindow, QWidget#root {{ background-color:{DARK}; }}
QWidget#header {{ background-color:#0f120c; border-bottom:1px solid {BORDER}; }}
QLabel#brand {{ color:{GREEN}; font-size:20px; font-weight:bold; }}
QLabel#tagline {{ color:#8a9186; font-size:13px; }}
QLabel#madeby {{ color:#5f665c; font-size:11px; }}
QTabWidget#tabs::pane {{ border:none; }}
QTabBar::tab {{ background:transparent; color:#8a9186; padding:10px 18px; margin:4px 4px; border-radius:8px; font-weight:bold; font-size:13px; }}
QTabBar::tab:hover {{ color:#d7dcd3; background:#1a1f16; }}
QTabBar::tab:selected {{ color:{GREEN}; background:{GREEN_DIM}; }}
QWidget#card {{ background-color:{PANEL}; border:1px solid {BORDER}; border-radius:12px; }}
QLabel#cardTitle {{ color:{GREEN}; font-weight:bold; font-size:14px; }}
QLabel#hint {{ color:#8a9186; font-size:12px; }}
QLabel#metricValue {{ font-size:24px; font-weight:bold; color:#ffffff; }}
QLabel#metricLabel {{ font-size:12px; color:#8a9186; }}
QFrame#metric {{ background-color:{PANEL2}; border:1px solid {BORDER}; border-radius:12px; }}
QPushButton {{ background-color:#1a1f16; color:#d7dcd3; border:1px solid {BORDER}; border-radius:8px; padding:8px 16px; min-height:32px; font-weight:bold; }}
QPushButton:hover {{ border-color:{GREEN}; background-color:#22291b; }}
QPushButton:disabled {{ color:#5f665c; border-color:#23281d; background:#12150f; }}
QPushButton[primary="true"] {{ background-color:{GREEN_DIM}; border-color:{GREEN}; color:{GREEN}; }}
QPushButton[primary="true"]:hover {{ background-color:rgba(118,185,0,0.32); }}
QProgressBar {{ border:1px solid {BORDER}; border-radius:6px; background:#0b0d0a; height:18px; text-align:center; color:#d7dcd3; }}
QProgressBar::chunk {{ background-color:{GREEN}; border-radius:5px; }}
QSlider::groove:horizontal {{ height:6px; background:#2a2f24; border-radius:3px; }}
QSlider::handle:horizontal {{ background:{GREEN}; width:18px; margin:-6px 0; border-radius:9px; }}
QTableWidget {{ background:#0b0d0a; border:1px solid {BORDER}; border-radius:8px; gridline-color:#1f2419; }}
QHeaderView::section {{ background:#12150f; color:#8a9186; border:none; padding:6px; font-weight:bold; }}
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


def hint(lay, text):
    h = QLabel(text)
    h.setObjectName("hint")
    h.setWordWrap(True)
    lay.addWidget(h)


def _fmt(v, suffix="", nd=0):
    return "—" if v is None else f"{v:.{nd}f}{suffix}"


def metric_tile():
    t = QFrame()
    t.setObjectName("metric")
    v = QVBoxLayout(t)
    v.setContentsMargins(14, 12, 14, 12)
    v.setSpacing(2)
    val = QLabel("—")
    val.setObjectName("metricValue")
    lab = QLabel("")
    lab.setObjectName("metricLabel")
    v.addWidget(val)
    v.addWidget(lab)
    t.value = val
    t.label = lab
    return t


class LiveGraph(QWidget):
    """Real-time сглаженный график одного показателя. На конце линии — текущее значение."""

    RIGHT_PAD = 54

    def __init__(self, maxv=100.0, unit=" %", parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.maxv = maxv
        self.unit = unit
        self.series = []

    def add(self, v):
        if v is None:
            return
        self.series.append(min(float(v), self.maxv))
        if len(self.series) > 240:
            self.series.pop(0)
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor("#0b0d0a"))

        # сетка
        p.setPen(QPen(QColor("#1f2419"), 1))
        for i in range(1, 4):
            y = int(h * i / 4)
            p.drawLine(0, y, w, y)

        if len(self.series) < 2:
            p.end()
            return

        w_plot = w - self.RIGHT_PAD
        n = len(self.series)
        pts = [QPointF(i / (n - 1) * w_plot,
                       h - (v / self.maxv) * (h - 22) - 8)
               for i, v in enumerate(self.series)]

        # сглаженный путь (квадратичные кривые через середины отрезков)
        path = QPainterPath()
        path.moveTo(pts[0])
        for i in range(1, n):
            p0, p1 = pts[i - 1], pts[i]
            mid = QPointF((p0.x() + p1.x()) / 2, (p0.y() + p1.y()) / 2)
            path.quadTo(p0, mid)
        path.lineTo(pts[-1])

        # заливка под линией
        area = QPainterPath(path)
        area.lineTo(pts[-1].x(), h)
        area.lineTo(pts[0].x(), h)
        area.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(118, 185, 0, 90))
        grad.setColorAt(1, QColor(118, 185, 0, 0))
        p.fillPath(area, grad)

        # линия
        p.setPen(QPen(QColor(GREEN), 2))
        p.drawPath(path)

        # процент на конце линии
        last = pts[-1]
        p.setPen(QPen(QColor(GREEN)))
        f = p.font()
        f.setBold(True)
        f.setPixelSize(13)
        p.setFont(f)
        p.drawText(QPointF(last.x() + 8, last.y() + 5),
                   f"{self.series[-1]:.0f}{self.unit}")
        p.end()


class OverviewPage(QWidget):
    def __init__(self):
        super().__init__()
        o = QVBoxLayout(self)
        o.setContentsMargins(20, 18, 20, 18)
        o.setSpacing(14)

        c, lay = card()
        top = QHBoxLayout()
        left = QVBoxLayout()
        self.name = QLabel("—")
        self.name.setStyleSheet("font-size:20px;font-weight:bold;color:#ffffff;")
        left.addWidget(self.name)
        self.driver = QLabel("")
        self.driver.setObjectName("hint")
        left.addWidget(self.driver)
        top.addLayout(left, 1)
        self.temp = QLabel("—")
        self.temp.setStyleSheet(f"font-size:40px;font-weight:bold;color:{GREEN};")
        top.addWidget(self.temp, 0, Qt.AlignVCenter)
        lay.addLayout(top)
        o.addWidget(c)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.tiles = {}
        tile_defs = [
            ("clock", "Частота GPU"), ("mem_clock", "Частота памяти"),
            ("power", "Потребление"), ("fan", "Вентиляторы"),
            ("util", "Загрузка GPU"), ("vram", "Видеопамять"),
        ]
        for i, (key, lab) in enumerate(tile_defs):
            t = metric_tile()
            t.label.setText(lab)
            self.tiles[key] = t
            grid.addWidget(t, i // 3, i % 3)
        o.addLayout(grid)

        c2, lay2 = card()
        lay2.addWidget(title("Процессы, использующие GPU"))
        self.proc = QTableWidget(0, 3)
        self.proc.setHorizontalHeaderLabels(["PID", "Процесс", "Видеопамять"])
        self.proc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc.verticalHeader().setVisible(False)
        self.proc.setEditTriggers(QTableWidget.NoEditTriggers)
        lay2.addWidget(self.proc)
        o.addWidget(c2)
        o.addStretch()

    def update_data(self, d, procs):
        if d is None:
            self.name.setText("nvidia-smi недоступен")
            self.driver.setText("")
            self.temp.setText("—")
            return
        self.name.setText(d["name"])
        self.driver.setText(f"Драйвер {d['driver']} · ядро {backend.kernel()}")
        self.temp.setText(_fmt(d["temp"], "°"))
        self.tiles["clock"].value.setText(_fmt(d["clock"], " МГц"))
        self.tiles["mem_clock"].value.setText(_fmt(d["mem_clock"], " МГц"))
        power = _fmt(d["power"], " Вт")
        plimit = _fmt(d["power_limit"], " Вт")
        self.tiles["power"].value.setText(f"{power} / {plimit}")
        self.tiles["fan"].value.setText(
            "0 % (0-dB)" if d["fan"] == 0 else _fmt(d["fan"], " %")
        )
        self.tiles["util"].value.setText(_fmt(d["gpu_util"], " %"))
        if d["mem_used"] is not None and d["mem_total"] is not None:
            self.tiles["vram"].value.setText(f"{d['mem_used'] / 1024:.1f} / {d['mem_total'] / 1024:.1f} ГБ")
        else:
            self.tiles["vram"].value.setText("—")
        self.proc.setRowCount(len(procs))
        for r, (pid, name, mem) in enumerate(procs):
            for col, val in enumerate((pid, name, mem)):
                self.proc.setItem(r, col, QTableWidgetItem(val))


class MonitorPage(QWidget):
    def __init__(self):
        super().__init__()
        o = QVBoxLayout(self)
        o.setContentsMargins(20, 18, 20, 18)
        o.setSpacing(14)

        self.graphs = {}
        self.labels = {}
        self.meta = {}
        grid = QGridLayout()
        grid.setSpacing(12)
        metrics = [
            ("gpu_util", "Загрузка GPU", 100.0, " %"),
            ("temp", "Температура", 100.0, " °C"),
            ("power", "Питание", 300.0, " Вт"),
            ("mem_used", "Видеопамять", 4096.0, " МБ"),
            ("clock", "Частота GPU", 2000.0, " МГц"),
            ("fan", "Вентиляторы", 100.0, " %"),
        ]
        for i, (key, name, maxv, unit) in enumerate(metrics):
            c, lay = card()
            lbl = QLabel(name)
            lbl.setObjectName("cardTitle")
            lay.addWidget(lbl)
            g = LiveGraph(maxv, unit)
            lay.addWidget(g)
            grid.addWidget(c, i // 2, i % 2)
            self.graphs[key] = g
            self.labels[key] = lbl
            self.meta[key] = (name, unit)
        o.addLayout(grid)
        o.addStretch()

    def update_data(self, d):
        if d is None:
            return
        # динамические шкалы
        if d.get("power_limit"):
            self.graphs["power"].maxv = d["power_limit"]
        if d.get("mem_total"):
            self.graphs["mem_used"].maxv = d["mem_total"]
        for key in self.graphs:
            v = d.get(key)
            if v is None:
                continue
            self.graphs[key].add(v)
            name, unit = self.meta[key]
            if key == "mem_used":
                self.labels[key].setText(f"{name} · {v / 1024:.1f} ГБ")
            elif key == "fan" and v == 0:
                self.labels[key].setText(f"{name} · 0 % (стоп, 0-dB)")
            else:
                self.labels[key].setText(f"{name} · {v:.0f}{unit}")


def page_driver():
    outer = QWidget()
    o = QVBoxLayout(outer)
    o.setContentsMargins(20, 18, 20, 18)
    o.setSpacing(14)
    d = backend.query_gpu()
    c, lay = card()
    lay.addWidget(title("Драйвер"))
    lay.addWidget(QLabel(f"Установлен: {d['driver'] if d else '—'}"))
    lay.addWidget(QLabel(f"Ядро: {backend.kernel()}"))
    o.addWidget(c)

    c2, lay2 = card()
    lay2.addWidget(title("DKMS (сборка под ядра)"))
    dkms = backend.query_dkms()
    if dkms:
        for line in dkms.splitlines():
            ok = "installed" in line
            lay2.addWidget(QLabel(("✓ " if ok else "✗ ") + line.strip()))
    else:
        lay2.addWidget(QLabel("dkms не найден или недоступен"))
    hint(lay2, "Обновление — через pacman одной транзакцией, после пересборка initramfs и перезагрузка.")
    o.addWidget(c2)

    row = QWidget()
    h = QHBoxLayout(row)
    h.setContentsMargins(0, 0, 0, 0)
    b1 = QPushButton("Проверить обновления")
    b2 = QPushButton("Обновить драйвер")
    b2.setProperty("primary", True)
    h.addWidget(b1)
    h.addWidget(b2)
    h.addStretch()
    o.addWidget(row)
    o.addStretch()
    return outer


def page_power():
    outer = QWidget()
    o = QVBoxLayout(outer)
    o.setContentsMargins(20, 18, 20, 18)
    o.setSpacing(14)
    c, lay = card()
    lay.addWidget(title("Лимит мощности"))
    val = QLabel("—")
    val.setObjectName("metricValue")
    lay.addWidget(val)
    s = QSlider(Qt.Horizontal)
    s.setRange(50, 100)
    s.setValue(75)
    lay.addWidget(s)
    hint(lay, "Работает и на Wayland, и на Xorg (требуются права root).")
    o.addWidget(c)
    c2, lay2 = card()
    lay2.addWidget(title("Разгон и вентиляторы"))
    hint(lay2, "⚠ Только Xorg: кривая вентиляторов и офсеты частот — через nvidia-settings (нужен coolbits).")
    h = QHBoxLayout()
    for t in ("Кривая вентиляторов", "Офсет частоты"):
        b = QPushButton(t)
        b.setEnabled(False)
        h.addWidget(b)
    h.addStretch()
    lay2.addLayout(h)
    o.addWidget(c2)
    o.addStretch()
    return outer


def page_profiles():
    outer = QWidget()
    o = QVBoxLayout(outer)
    o.setContentsMargins(20, 18, 20, 18)
    o.setSpacing(12)
    for name, desc, active in [
        ("Тихий", "лимит 65 Вт · тихая кривая вентиляторов", False),
        ("Игры", "лимит 75 Вт · максимальная частота", True),
        ("Макс. производительность", "лимит 75 Вт · офсет +150 МГц", False),
    ]:
        c, lay = card()
        h = QHBoxLayout()
        txt = QLabel(f"<b>{name}</b><br><span style='color:#8a9186;font-size:12px;'>{desc}</span>")
        h.addWidget(txt, 1)
        b = QPushButton("Активен" if active else "Применить")
        b.setProperty("primary", not active)
        if active:
            b.setEnabled(False)
        h.addWidget(b)
        lay.addLayout(h)
        o.addWidget(c)
    hint(o, "Профиль — набор сохранённых настроек, применяется при запуске (не драйверный профиль).")
    o.addStretch()
    return outer


def page_record():
    outer = QWidget()
    o = QVBoxLayout(outer)
    o.setContentsMargins(20, 18, 20, 18)
    o.setSpacing(12)
    for name, desc, on in [
        ("Оверлей", "fps / температура / загрузка поверх игры", True),
        ("Запись", "NVENC, 1080p60", False),
        ("Повтор (replay buffer)", "сохранить последние 30 секунд", False),
    ]:
        c, lay = card()
        h = QHBoxLayout()
        txt = QLabel(f"<b>{name}</b><br><span style='color:#8a9186;font-size:12px;'>{desc}</span>")
        h.addWidget(txt, 1)
        b = QPushButton("Выкл" if on else "Вкл")
        b.setProperty("primary", on)
        h.addWidget(b)
        lay.addLayout(h)
        o.addWidget(c)
    hint(o, "На Wayland захват — через PipeWire/dma-buf + NVENC (ffmpeg/OBS).")
    o.addStretch()
    return outer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GreenBoard — GPU dashboard")
        self.resize(980, 680)
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(500)
        self._refresh()

    def _build(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())

        self.overview = OverviewPage()
        self.monitor = MonitorPage()
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabs")
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.overview, "Обзор")
        self.tabs.addTab(page_driver(), "Драйвер")
        self.tabs.addTab(self.monitor, "Мониторинг")
        self.tabs.addTab(page_power(), "Питание")
        self.tabs.addTab(page_profiles(), "Профили")
        self.tabs.addTab(page_record(), "Запись")
        outer.addWidget(self.tabs, 1)

    def _header(self):
        hb = QWidget()
        hb.setObjectName("header")
        h = QHBoxLayout(hb)
        h.setContentsMargins(20, 12, 20, 12)
        b = QLabel("GreenBoard")
        b.setObjectName("brand")
        tag = QLabel("панель управления видеокартой")
        tag.setObjectName("tagline")
        made = QLabel("By InIProject — SkilinPur")
        made.setObjectName("madeby")
        h.addWidget(b)
        h.addSpacing(10)
        h.addWidget(tag)
        h.addStretch()
        h.addWidget(made)
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{GREEN};font-size:14px;")
        h.addSpacing(8)
        h.addWidget(dot)
        return hb

    def _refresh(self):
        d = backend.query_gpu()
        procs = backend.query_processes()
        self.overview.update_data(d, procs)
        self.monitor.update_data(d)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
