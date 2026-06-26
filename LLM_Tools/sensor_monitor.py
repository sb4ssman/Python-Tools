"""
LLM_Tools live sensor monitor.

What it does
  Reads live temperatures, fan speeds, GPU load, GPU memory, GPU power, and CPU
  package power when a supported sensor source is available. It does not talk
  to drivers directly; instead it consumes existing monitor integrations and
  command-line tools, then merges the readings into one small schema.

Source priority
  1. HWiNFO64 shared memory on Windows
  2. MSI Afterburner shared memory on Windows
  3. LibreHardwareMonitor WMI on Windows
  4. OpenHardwareMonitor WMI on Windows
  5. nvidia-smi on any platform where it is installed
  6. Windows WMI thermal-zone fallback

Cross-platform expectations
  The best sensor coverage is currently Windows-first because the richest
  sources are Windows monitor tools. Linux/macOS can still report NVIDIA GPU
  metrics through nvidia-smi when available. Missing tools are tolerated; the
  script returns an empty "none" snapshot instead of failing loudly.

Usage
  python LLM_Tools/sensor_monitor.py
  python LLM_Tools/sensor_monitor.py --sources
  python LLM_Tools/sensor_monitor.py --mode llm
  python LLM_Tools/sensor_monitor.py --stream
  python LLM_Tools/sensor_monitor.py --stream --out sensors.jsonl
  python LLM_Tools/sensor_monitor.py --interval 5

Import API
  from sensor_monitor import SensorMonitor
  mon = SensorMonitor()
  data = mon.read()
  mon.stream(interval=3)
"""

import argparse
import ctypes
import json
import mmap
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Shared-memory structure definitions (Windows)
# ---------------------------------------------------------------------------

class _HWiNFO_HEADER(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("signature",              ctypes.c_uint32),   # 'HWiS'
        ("version",                ctypes.c_uint32),
        ("revision",               ctypes.c_uint32),
        ("poll_time",              ctypes.c_int32),
        ("offset_sensors",         ctypes.c_uint32),
        ("size_sensor_element",    ctypes.c_uint32),
        ("num_sensors",            ctypes.c_uint32),
        ("offset_readings",        ctypes.c_uint32),
        ("size_reading_element",   ctypes.c_uint32),
        ("num_readings",           ctypes.c_uint32),
    ]

class _HWiNFO_SENSOR(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("sensor_id",              ctypes.c_uint32),
        ("sensor_instance",        ctypes.c_uint32),
        ("name_orig",              ctypes.c_char * 128),
        ("name_user",              ctypes.c_char * 128),
    ]

_HWINFO_READING_TYPE = {0: "None", 1: "Temp", 2: "Volt", 3: "Fan",
                         4: "Current", 5: "Power", 6: "Clock",
                         7: "Usage", 8: "Other"}

class _HWiNFO_READING(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("reading_type",           ctypes.c_uint32),
        ("reading_id",             ctypes.c_uint32),
        ("sensor_index",           ctypes.c_uint32),
        ("reading_id2",            ctypes.c_uint32),
        ("label_orig",             ctypes.c_char * 128),
        ("label_user",             ctypes.c_char * 128),
        ("unit",                   ctypes.c_char * 16),
        ("value",                  ctypes.c_double),
        ("value_min",              ctypes.c_double),
        ("value_max",              ctypes.c_double),
        ("value_avg",              ctypes.c_double),
    ]

_MAHM_MAX_PATH = 260

class _MAHM_HEADER(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("signature",              ctypes.c_uint32),   # 'MAHM'
        ("version",                ctypes.c_uint32),
        ("header_size",            ctypes.c_uint32),
        ("num_entries",            ctypes.c_uint32),
        ("entry_size",             ctypes.c_uint32),
        ("poll_time",              ctypes.c_int32),
    ]

class _MAHM_ENTRY(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("src_name",               ctypes.c_char * _MAHM_MAX_PATH),
        ("src_units",              ctypes.c_char * _MAHM_MAX_PATH),
        ("loc_src_name",           ctypes.c_char * _MAHM_MAX_PATH),
        ("loc_src_units",          ctypes.c_char * _MAHM_MAX_PATH),
        ("fmt",                    ctypes.c_char * _MAHM_MAX_PATH),
        ("data",                   ctypes.c_float),
        ("min_limit",              ctypes.c_float),
        ("max_limit",              ctypes.c_float),
        ("flags",                  ctypes.c_uint32),
        ("gpu_index",              ctypes.c_uint32),
        ("src_id",                 ctypes.c_uint32),
    ]


# ---------------------------------------------------------------------------
# Sensor reading result schema
# ---------------------------------------------------------------------------
# read() returns a dict matching this shape (all keys present, may be empty):
# {
#   "timestamp":  "2026-06-08T10:49:00",
#   "source":     "HWiNFO64",          # which source(s) contributed
#   "fans":       [{"name": str, "rpm": float}, ...],
#   "temps":      [{"name": str, "celsius": float}, ...],
#   "gpu":        [{"name": str, "util_pct": float, "mem_used_mb": float,
#                   "mem_total_mb": float, "temp_c": float, "power_w": float,
#                   "fan_pct": float}, ...],
#   "cpu_power_w": float | None,
# }


def _empty_result(source: str = "none") -> Dict:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "fans": [],
        "temps": [],
        "gpu": [],
        "cpu_power_w": None,
    }


# ---------------------------------------------------------------------------
# Individual source readers
# ---------------------------------------------------------------------------

class _SourceBase:
    name = "base"

    def is_available(self) -> bool:
        return False

    def read(self) -> Optional[Dict]:
        return None


class _HWiNFOSource(_SourceBase):
    name = "HWiNFO64"
    _SM_NAME = "Global\\HWiNFO_SENS_SM2"
    _MAP_SIZE = 4 * 1024 * 1024  # generous upper bound; unmapped pages cost nothing

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        try:
            m = mmap.mmap(-1, self._MAP_SIZE, tagname=self._SM_NAME,
                          access=mmap.ACCESS_READ)
            sig = m.read(4)
            m.close()
            return sig == b"HWiS"
        except Exception:
            return False

    def read(self) -> Optional[Dict]:
        if platform.system() != "Windows":
            return None
        try:
            m = mmap.mmap(-1, self._MAP_SIZE, tagname=self._SM_NAME,
                          access=mmap.ACCESS_READ)
        except Exception:
            return None

        try:
            hdr = _HWiNFO_HEADER.from_buffer_copy(m.read(ctypes.sizeof(_HWiNFO_HEADER)))
            if hdr.signature != 0x53695748:  # 'HWiS' little-endian
                return None

            # Read sensor name table
            m.seek(hdr.offset_sensors)
            sensors = []
            for _ in range(hdr.num_sensors):
                raw = m.read(hdr.size_sensor_element)
                s = _HWiNFO_SENSOR.from_buffer_copy(raw[:ctypes.sizeof(_HWiNFO_SENSOR)])
                sensors.append(s.name_user.decode("utf-8", errors="replace").strip()
                                or s.name_orig.decode("utf-8", errors="replace").strip())

            # Read readings
            m.seek(hdr.offset_readings)
            result = _empty_result(self.name)
            for _ in range(hdr.num_readings):
                raw = m.read(hdr.size_reading_element)
                r = _HWiNFO_READING.from_buffer_copy(raw[:ctypes.sizeof(_HWiNFO_READING)])
                label = (r.label_user.decode("utf-8", errors="replace").strip()
                         or r.label_orig.decode("utf-8", errors="replace").strip())
                sensor_name = sensors[r.sensor_index] if r.sensor_index < len(sensors) else ""
                full_name = f"{sensor_name} / {label}" if sensor_name else label
                rtype = r.reading_type

                if rtype == 3:  # Fan
                    result["fans"].append({"name": full_name, "rpm": round(r.value, 1)})
                elif rtype == 1:  # Temp
                    result["temps"].append({"name": full_name, "celsius": round(r.value, 1)})
                elif rtype == 5:  # Power
                    llow = label.lower()
                    if "cpu" in llow and "package" in llow:
                        result["cpu_power_w"] = round(r.value, 2)

            return result
        except Exception:
            return None
        finally:
            m.close()


class _AfterburnerSource(_SourceBase):
    name = "MSI Afterburner"
    _SM_NAME = "Global\\MAHMSharedMemory"
    _MAP_SIZE = 4 * 1024 * 1024

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        try:
            m = mmap.mmap(-1, self._MAP_SIZE, tagname=self._SM_NAME,
                          access=mmap.ACCESS_READ)
            sig = m.read(4)
            m.close()
            return sig == b"MAHM"
        except Exception:
            return False

    def read(self) -> Optional[Dict]:
        if platform.system() != "Windows":
            return None
        try:
            m = mmap.mmap(-1, self._MAP_SIZE, tagname=self._SM_NAME,
                          access=mmap.ACCESS_READ)
        except Exception:
            return None

        try:
            hdr = _MAHM_HEADER.from_buffer_copy(m.read(ctypes.sizeof(_MAHM_HEADER)))
            if hdr.signature != 0x4D48414D:  # 'MAHM'
                return None

            result = _empty_result(self.name)
            gpu_map: Dict[int, Dict] = {}

            m.seek(hdr.header_size)
            for _ in range(hdr.num_entries):
                raw = m.read(hdr.entry_size)
                entry = _MAHM_ENTRY.from_buffer_copy(raw[:ctypes.sizeof(_MAHM_ENTRY)])
                name = entry.src_name.decode("utf-8", errors="replace").strip()
                val = entry.data
                idx = entry.gpu_index
                nlow = name.lower()

                if idx not in gpu_map:
                    gpu_map[idx] = {"name": f"GPU{idx}", "util_pct": None,
                                    "mem_used_mb": None, "mem_total_mb": None,
                                    "temp_c": None, "power_w": None, "fan_pct": None}

                if "gpu temperature" in nlow or (idx != 0xFFFFFFFF and "temperature" in nlow):
                    gpu_map[idx]["temp_c"] = round(val, 1)
                elif "gpu usage" in nlow or "gpu1 usage" in nlow:
                    gpu_map[idx]["util_pct"] = round(val, 1)
                elif "memory usage" in nlow:
                    gpu_map[idx]["mem_used_mb"] = round(val, 1)
                elif "fan speed" in nlow and idx != 0xFFFFFFFF:
                    gpu_map[idx]["fan_pct"] = round(val, 1)
                elif "power" in nlow and idx != 0xFFFFFFFF:
                    gpu_map[idx]["power_w"] = round(val, 2)
                elif "fan speed" in nlow:
                    result["fans"].append({"name": name, "rpm": round(val, 1)})
                elif "temperature" in nlow:
                    result["temps"].append({"name": name, "celsius": round(val, 1)})
                elif "cpu power" in nlow:
                    result["cpu_power_w"] = round(val, 2)

            result["gpu"] = [g for g in gpu_map.values()
                              if g["gpu_index"] != 0xFFFFFFFF
                              ] if False else list(gpu_map.values())
            # Clean out the placeholder index=0xFFFFFFFF (system-level entries)
            result["gpu"] = [g for k, g in gpu_map.items() if k != 0xFFFFFFFF]
            return result
        except Exception:
            return None
        finally:
            m.close()


class _LibreHWMonSource(_SourceBase):
    name = "LibreHardwareMonitor"
    _NAMESPACE = "root\\LibreHardwareMonitor"

    def _wmi_query(self, query: str) -> Optional[str]:
        cmd = ["powershell", "-NoProfile", "-Command",
               f"Get-WmiObject -Namespace '{self._NAMESPACE}' -Query \"{query}\" | "
               "Select-Object Name,SensorType,Value | ConvertTo-Json"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=10)
            if r.returncode == 0 and r.stdout:
                return r.stdout.decode("utf-8", errors="replace")
        except Exception:
            pass
        return None

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        raw = self._wmi_query("SELECT * FROM Sensor WHERE SensorType='Fan'")
        return raw is not None and len(raw.strip()) > 5

    def read(self) -> Optional[Dict]:
        raw = self._wmi_query("SELECT * FROM Sensor")
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, list):
            data = [data]

        result = _empty_result(self.name)
        for entry in data:
            name = entry.get("Name", "")
            stype = (entry.get("SensorType") or "").lower()
            val = entry.get("Value")
            if val is None:
                continue
            if stype == "fan":
                result["fans"].append({"name": name, "rpm": round(float(val), 1)})
            elif stype == "temperature":
                result["temps"].append({"name": name, "celsius": round(float(val), 1)})
            elif stype == "power" and "cpu" in name.lower():
                result["cpu_power_w"] = round(float(val), 2)
        return result


class _OpenHWMonSource(_LibreHWMonSource):
    name = "OpenHardwareMonitor"
    _NAMESPACE = "root\\OpenHardwareMonitor"


class _NvidiaSmiSource(_SourceBase):
    name = "nvidia-smi"

    def is_available(self) -> bool:
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=name",
                                 "--format=csv,noheader"],
                                capture_output=True, timeout=8)
            return r.returncode == 0 and bool(r.stdout.strip())
        except Exception:
            return False

    def read(self) -> Optional[Dict]:
        fields = ("index,name,temperature.gpu,utilization.gpu,"
                  "memory.used,memory.total,power.draw,fan.speed")
        try:
            r = subprocess.run(
                ["nvidia-smi", f"--query-gpu={fields}",
                 "--format=csv,noheader,nounits"],
                capture_output=True, timeout=10,
            )
        except Exception:
            return None
        if r.returncode != 0 or not r.stdout:
            return None

        result = _empty_result(self.name)
        for line in r.stdout.decode("utf-8", errors="replace").strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 8:
                continue
            def _f(x):
                try:
                    return float(x)
                except (ValueError, TypeError):
                    return None
            gpu = {
                "name":         parts[1],
                "temp_c":       _f(parts[2]),
                "util_pct":     _f(parts[3]),
                "mem_used_mb":  _f(parts[4]),
                "mem_total_mb": _f(parts[5]),
                "power_w":      _f(parts[6]),
                "fan_pct":      _f(parts[7]),
            }
            result["gpu"].append(gpu)
        return result


class _WmiFallbackSource(_SourceBase):
    """Last-resort: MSAcpi thermal zones + basic WMI counters (Windows only)."""
    name = "WMI"

    def _ps(self, cmd: str) -> Any:
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True, timeout=15,
            )
            if r.returncode == 0 and r.stdout:
                return json.loads(r.stdout.decode("utf-8", errors="replace"))
        except Exception:
            pass
        return None

    def is_available(self) -> bool:
        return platform.system() == "Windows"

    def read(self) -> Optional[Dict]:
        result = _empty_result(self.name)
        raw = self._ps(
            "Get-WmiObject -Namespace root\\WMI -Class MSAcpi_ThermalZoneTemperature "
            "| Select-Object InstanceName,CurrentTemperature | ConvertTo-Json"
        )
        if raw:
            if not isinstance(raw, list):
                raw = [raw]
            for entry in raw:
                temp_k10 = entry.get("CurrentTemperature")
                if temp_k10:
                    celsius = round((float(temp_k10) / 10.0) - 273.15, 1)
                    name = entry.get("InstanceName", "ThermalZone")
                    result["temps"].append({"name": name, "celsius": celsius})
        return result


# ---------------------------------------------------------------------------
# Main monitor class
# ---------------------------------------------------------------------------

# Priority order — first available source is primary; others can fill gaps
_SOURCE_PRIORITY = [
    _HWiNFOSource,
    _AfterburnerSource,
    _LibreHWMonSource,
    _OpenHWMonSource,
    _NvidiaSmiSource,
    _WmiFallbackSource,
]


class SensorMonitor:
    """
    Hardware-agnostic sensor monitor.

    Probes available data sources in priority order and reads whichever
    is present. Multiple sources are merged: e.g. Afterburner for GPU,
    nvidia-smi fills gaps if Afterburner misses something.
    """

    def __init__(self):
        self._sources: List[_SourceBase] = []
        self._probed = False

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_sources(self) -> List[str]:
        """Probe all sources and return names of available ones."""
        self._sources = []
        for cls in _SOURCE_PRIORITY:
            src = cls()
            if src.is_available():
                self._sources.append(src)
        self._probed = True
        return [s.name for s in self._sources]

    def read(self) -> Dict:
        """Return a single sensor snapshot merged from all available sources."""
        if not self._probed:
            self.detect_sources()

        merged = _empty_result("none")
        sources_used = []

        for src in self._sources:
            data = src.read()
            if not data:
                continue
            sources_used.append(src.name)

            # Fans: take all (deduplicate by name)
            existing_fan_names = {f["name"] for f in merged["fans"]}
            for f in data.get("fans", []):
                if f["name"] not in existing_fan_names:
                    merged["fans"].append(f)
                    existing_fan_names.add(f["name"])

            # Temps: take all (deduplicate by name)
            existing_temp_names = {t["name"] for t in merged["temps"]}
            for t in data.get("temps", []):
                if t["name"] not in existing_temp_names:
                    merged["temps"].append(t)
                    existing_temp_names.add(t["name"])

            # GPU: merge by name; first source with a given GPU name wins per-field
            for gpu_entry in data.get("gpu", []):
                existing = next((g for g in merged["gpu"]
                                  if g["name"] == gpu_entry["name"]), None)
                if existing is None:
                    merged["gpu"].append(dict(gpu_entry))
                else:
                    # Fill None fields from later sources
                    for k, v in gpu_entry.items():
                        if existing.get(k) is None and v is not None:
                            existing[k] = v

            # CPU power: first non-None wins
            if merged["cpu_power_w"] is None and data.get("cpu_power_w") is not None:
                merged["cpu_power_w"] = data["cpu_power_w"]

        merged["source"] = ", ".join(sources_used) if sources_used else "none"
        merged["timestamp"] = datetime.now().isoformat(timespec="seconds")
        return merged

    def stream(self, interval: float = 3.0, output_path: Optional[Path] = None,
               formatter: str = "standard"):
        """
        Poll sensors continuously. Writes each snapshot to stdout and
        optionally to output_path (one JSON object per line for easy parsing).

        Press Ctrl+C to stop.
        """
        if not self._probed:
            available = self.detect_sources()
            print(f"[sensor_monitor] Sources: {', '.join(available) or 'none'}", flush=True)

        f = open(output_path, "a", encoding="utf-8") if output_path else None
        try:
            while True:
                data = self.read()
                line = json.dumps(data)
                if f:
                    f.write(line + "\n")
                    f.flush()
                if formatter == "standard":
                    print(self.format(data, "standard"), flush=True)
                else:
                    print(line, flush=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[sensor_monitor] Stopped.", flush=True)
        finally:
            if f:
                f.close()

    def format(self, data: Dict, mode: str = "standard") -> str:
        if mode == "llm":
            return json.dumps(self._fmt_llm(data))
        if mode == "jsonl":
            return json.dumps(data)
        return self._fmt_standard(data)

    # ── Formatters ────────────────────────────────────────────────────────────

    def _fmt_standard(self, data: Dict) -> str:
        W = 62
        sep = "─" * W
        ts = data.get("timestamp", "")
        src = data.get("source", "?")
        lines = [sep, f"  Sensor Snapshot — {ts}  [{src}]", sep]

        fans = data.get("fans", [])
        if fans:
            lines.append("  FANS")
            for f in sorted(fans, key=lambda x: x["name"]):
                rpm = f.get("rpm")
                lines.append(f"    {f['name']:<40} {rpm:>6.0f} RPM" if rpm is not None
                              else f"    {f['name']}")

        temps = data.get("temps", [])
        if temps:
            lines.append("  TEMPS")
            for t in sorted(temps, key=lambda x: -x.get("celsius", 0)):
                c = t.get("celsius")
                lines.append(f"    {t['name']:<40} {c:>5.1f} °C" if c is not None
                              else f"    {t['name']}")

        gpus = data.get("gpu", [])
        if gpus:
            lines.append("  GPU")
            for g in gpus:
                name = g.get("name", "GPU")
                parts = []
                if g.get("temp_c") is not None:
                    parts.append(f"{g['temp_c']:.0f}°C")
                if g.get("util_pct") is not None:
                    parts.append(f"{g['util_pct']:.0f}% util")
                if g.get("mem_used_mb") is not None and g.get("mem_total_mb") is not None:
                    parts.append(f"{g['mem_used_mb']:.0f}/{g['mem_total_mb']:.0f} MB")
                if g.get("power_w") is not None:
                    parts.append(f"{g['power_w']:.1f}W")
                if g.get("fan_pct") is not None:
                    parts.append(f"fan {g['fan_pct']:.0f}%")
                lines.append(f"    {name:<36} {' | '.join(parts)}")

        cpu_pw = data.get("cpu_power_w")
        if cpu_pw is not None:
            lines.append(f"  CPU Power  {cpu_pw:.1f} W")

        lines.append(sep)
        return "\n".join(lines)

    def _fmt_llm(self, data: Dict) -> Dict:
        """Compact form for LLM consumption."""
        out: Dict[str, Any] = {
            "ts": data.get("timestamp"),
            "src": data.get("source"),
        }
        fans = data.get("fans", [])
        if fans:
            out["fans"] = {f["name"]: f.get("rpm") for f in fans}
        temps = data.get("temps", [])
        if temps:
            out["temps"] = {t["name"]: t.get("celsius") for t in temps}
        gpus = data.get("gpu", [])
        if gpus:
            out["gpu"] = gpus
        if data.get("cpu_power_w") is not None:
            out["cpu_w"] = data["cpu_power_w"]
        return out


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    parser = argparse.ArgumentParser(description="Hardware sensor monitor")
    parser.add_argument("--mode", choices=["standard", "llm", "jsonl"],
                        default="standard",
                        help="standard: human-readable | llm: compact JSON | jsonl: raw JSON")
    parser.add_argument("--stream", action="store_true",
                        help="Stream continuously (Ctrl+C to stop)")
    parser.add_argument("--interval", type=float, default=3.0,
                        help="Poll interval in seconds for --stream (default: 3)")
    parser.add_argument("--out", type=str, default=None,
                        help="Output file for --stream (jsonl, appended)")
    parser.add_argument("--sources", action="store_true",
                        help="List available data sources and exit")
    args = parser.parse_args()

    mon = SensorMonitor()

    if args.sources:
        available = mon.detect_sources()
        print("Available sources:")
        for name in available:
            print(f"  ✓ {name}")
        if not available:
            print("  (none detected)")
        sys.exit(0)

    if args.stream:
        out_path = Path(args.out) if args.out else None
        mon.stream(interval=args.interval, output_path=out_path,
                   formatter=args.mode)
    else:
        data = mon.read()
        print(mon.format(data, args.mode))
