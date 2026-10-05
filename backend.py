#!/usr/bin/env python3
"""Бэкенд GreenBoard: чтение реальных данных GPU через nvidia-smi (без внешних библиотек)."""

import subprocess


def _safe_float(s):
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "[N/A]", "N/A", "[Not Supported]", "-", "[Unknown]"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def query_gpu():
    """Основная метрика GPU или None, если nvidia-smi недоступен."""
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,"
        "memory.used,memory.total,power.draw,power.limit,clocks.gr,clocks.mem,"
        "fan.speed,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=5, errors="replace").stdout.strip()
    except Exception:
        return None
    if not out:
        return None
    parts = [p.strip() for p in out.split(",")]
    if len(parts) < 12:
        return None
    return {
        "name": parts[0],
        "temp": _safe_float(parts[1]),
        "gpu_util": _safe_float(parts[2]),
        "mem_util": _safe_float(parts[3]),
        "mem_used": _safe_float(parts[4]),
        "mem_total": _safe_float(parts[5]),
        "power": _safe_float(parts[6]),
        "power_limit": _safe_float(parts[7]),
        "clock": _safe_float(parts[8]),
        "mem_clock": _safe_float(parts[9]),
        "fan": _safe_float(parts[10]),
        "driver": parts[11],
    }


def query_processes():
    """Процессы, использующие GPU. Список (pid, имя, память МБ)."""
    cmd = [
        "nvidia-smi",
        "--query-compute-apps=pid,process_name,used_memory",
        "--format=csv,noheader,nounits",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=5, errors="replace").stdout.strip()
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def query_dkms():
    """Строки 'dkms status' (для вкладки драйвера)."""
    try:
        out = subprocess.run(["dkms", "status"], capture_output=True, text=True,
                             timeout=5, errors="replace").stdout.strip()
    except Exception:
        return None
    return out


def kernel():
    try:
        return subprocess.run(["uname", "-r"], capture_output=True, text=True,
                              timeout=5).stdout.strip()
    except Exception:
        return "?"
