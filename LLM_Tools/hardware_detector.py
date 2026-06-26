"""
LLM_Tools hardware detector.

What it does
  Collects a point-in-time hardware inventory and formats it for three common
  audiences: a readable terminal report, compact JSON for LLM context, and full
  JSON for debugging or archival snapshots. It is useful when choosing local
  inference models, checking GPU/VRAM availability, or giving an agent enough
  machine context to make sane tool recommendations.

Platform support
  Windows   PowerShell/WMI, nvidia-smi, optional psutil
  macOS     sysctl, system_profiler, nvidia-smi, optional psutil
  Linux     /proc, /sys, nvidia-smi, lspci/lshw/lsusb, optional psutil

Dependencies
  No required third-party package. If psutil is installed, RAM detection is
  more reliable. Optional system tools enrich results when present; missing
  tools are tolerated and simply leave those fields empty.

Usage
  python LLM_Tools/hardware_detector.py
  python LLM_Tools/hardware_detector.py --mode llm
  python LLM_Tools/hardware_detector.py --mode verbose
  python LLM_Tools/hardware_detector.py --mode verbose --save

Import API
  from hardware_detector import HardwareDetector
  det = HardwareDetector()
  data = det.detect()
  print(det.format(data, "standard"))
  print(det.format(data, "llm"))

Persistence
  --save writes to LLM_Tools/Data/settings.json by default, independent of the
  current working directory. Pass HardwareDetector(settings_path=...) or
  detect_and_save_hardware(settings_path=...) to use another file.
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _default_settings_path() -> Path:
    return Path(__file__).resolve().parent / "Data" / "settings.json"


class HardwareDetector:

    def __init__(self, settings_path: Optional[Union[str, Path]] = None):
        self.settings_path = Path(settings_path) if settings_path is not None else _default_settings_path()
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._os = platform.system()

    # ── Public API ────────────────────────────────────────────────────────────

    def detect(self) -> Dict:
        """Collect all hardware info. Returns the complete verbose dict.

        Note: verbose mode runs Get-PnpDevice / lshw which can add 2-5 s.
        """
        return {
            "id": str(uuid.uuid4()),
            "detected_at": datetime.now().isoformat(),
            "platform": self._detect_platform(),
            "cpu": self._detect_cpu(),
            "gpu": self._detect_gpu(),
            "ram": self._detect_ram(),
            "storage": self._detect_storage(),
            "displays": self._detect_displays(),
            "motherboard": self._detect_motherboard(),
            "network": self._detect_network(),
            "audio": self._detect_audio(),
            "battery": self._detect_battery(),
            "all_devices": self._detect_all_devices(),
            "inference_runtimes": self._check_runtimes(),
        }

    def format(self, data: Dict, mode: str = "standard") -> Union[str, Dict]:
        """Format collected data for the given audience."""
        if mode == "llm":
            return self._fmt_llm(data)
        if mode == "standard":
            return self._fmt_standard(data)
        return data  # verbose: raw dict

    def output(self, mode: str = "standard") -> Union[str, Dict]:
        """Detect and format in one call."""
        return self.format(self.detect(), mode)

    # ── Platform ──────────────────────────────────────────────────────────────

    def _detect_platform(self) -> Dict:
        return {
            "os": self._os,
            "os_version": platform.version(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    # ── CPU ───────────────────────────────────────────────────────────────────

    def _detect_cpu(self) -> Dict:
        info = {"name": "Unknown", "cores": 0, "threads": 0,
                "arch": platform.machine(), "avx2": False, "avx512": False}
        try:
            if self._os == "Windows":
                self._cpu_windows(info)
            elif self._os == "Darwin":
                self._cpu_macos(info)
            else:
                self._cpu_linux(info)
        except Exception:
            pass
        if info["name"] == "Unknown":
            info["name"] = (
                os.environ.get("PROCESSOR_IDENTIFIER")
                or platform.processor()
                or platform.machine()
                or "Unknown"
            )
        if info["threads"] == 0:
            info["threads"] = os.cpu_count() or 0
        return info

    def _cpu_windows(self, info: Dict):
        result = self._ps(
            "Get-CimInstance Win32_Processor | "
            "Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json"
        )
        if result:
            data = result[0] if isinstance(result, list) else result
            info["name"] = data.get("Name", "Unknown").strip()
            info["cores"] = data.get("NumberOfCores", 0)
            info["threads"] = data.get("NumberOfLogicalProcessors", 0)
        # Batch avx2+avx512 into one process; System.Runtime.Intrinsics requires .NET 5+ (pwsh/PS7)
        for ps_exe in ["pwsh", "powershell"]:
            avx_raw = self._run(
                [ps_exe, "-NoProfile", "-Command",
                 "@{avx2=[System.Runtime.Intrinsics.X86.Avx2]::IsSupported;"
                 "avx512=[System.Runtime.Intrinsics.X86.Avx512F]::IsSupported} | ConvertTo-Json"],
                timeout=8,
            )
            if avx_raw is not None:
                try:
                    avx = json.loads(avx_raw)
                    info["avx2"] = bool(avx.get("avx2"))
                    info["avx512"] = bool(avx.get("avx512"))
                except json.JSONDecodeError:
                    pass
                break

    def _cpu_macos(self, info: Dict):
        info["name"] = self._sysctl("machdep.cpu.brand_string") or "Apple Silicon"
        cores = self._sysctl("hw.physicalcpu")
        if cores:
            info["cores"] = int(cores)
        threads = self._sysctl("hw.logicalcpu")
        if threads:
            info["threads"] = int(threads)
        if platform.machine() == "x86_64":
            info["avx2"] = self._sysctl("hw.optional.avx2_0") == "1"
            info["avx512"] = self._sysctl("hw.optional.avx512f") == "1"
        # Apple Silicon: no AVX; avx2/avx512 remain False

    def _cpu_linux(self, info: Dict):
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            for line in cpuinfo.splitlines():
                if "model name" in line and info["name"] == "Unknown":
                    info["name"] = line.split(":", 1)[1].strip()
                if "cpu cores" in line and info["cores"] == 0:
                    info["cores"] = int(line.split(":", 1)[1].strip())
                if "siblings" in line and info["threads"] == 0:
                    info["threads"] = int(line.split(":", 1)[1].strip())
            flags = re.search(r"^flags\s*:(.+)", cpuinfo, re.MULTILINE)
            if flags:
                flag_list = flags.group(1).split()
                info["avx2"] = "avx2" in flag_list
                info["avx512"] = "avx512f" in flag_list
        except Exception:
            pass
        if info["threads"] == 0:
            r = self._run(["nproc"])
            if r:
                info["threads"] = int(r.strip())
                if info["cores"] == 0:
                    info["cores"] = info["threads"]

    # ── GPU ───────────────────────────────────────────────────────────────────

    def _detect_gpu(self) -> Dict:
        gpus: List[Dict] = []
        try:
            if self._os == "Windows":
                gpus = self._gpu_windows()
            elif self._os == "Darwin":
                gpus = self._gpu_macos()
            else:
                gpus = self._gpu_linux()
        except Exception:
            pass

        primary = (
            next((g for g in gpus if g["vendor"] == "NVIDIA" and g["role"] == "discrete"), None)
            or next((g for g in gpus if g["vendor"] == "AMD" and g["role"] == "discrete"), None)
            or (gpus[0] if gpus else None)
        )
        return {"primary": primary, "all": gpus}

    def _make_gpu(self, name: str, vram_gb: Optional[float] = None, unified: bool = False) -> Dict[str, Any]:
        low = name.lower()
        if "nvidia" in low:
            vendor, cuda_capable, role = "NVIDIA", True, "discrete"
        elif "amd" in low or "radeon" in low or "ati" in low:
            vendor, cuda_capable = "AMD", False
            # Common iGPU naming: "Radeon(TM) 610M/780M/890M" without "RX"/"Pro"
            role = "integrated" if not any(x in low for x in ["rx ", "pro w", " pro ", "vega "]) else "discrete"
        elif "apple" in low:
            vendor, cuda_capable, role = "Apple", False, "unified"
        elif "intel" in low:
            vendor, cuda_capable, role = "Intel", False, "integrated"
        else:
            vendor, cuda_capable, role = "Unknown", False, "discrete"
        return {
            "name": name, "vendor": vendor, "role": role,
            "vram_gb": vram_gb, "cuda_capable": cuda_capable,
            "cuda_device_index": None, "unified_memory": unified,
        }

    def _gpu_windows(self) -> List[Dict[str, Any]]:
        gpus = []
        # Include resolution fields so we know which controller has a display attached
        result = self._ps(
            "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,"
            "CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate | ConvertTo-Json"
        )
        if result:
            if not isinstance(result, list):
                result = [result]
            for entry in result:
                name = entry.get("Name")
                if not name:
                    continue
                vram_bytes = entry.get("AdapterRAM")
                # AdapterRAM is a 32-bit WMI field — caps at ~4 GB; nvidia-smi corrects it below
                vram_gb = round(float(vram_bytes) / 1024**3, 2) if vram_bytes else None
                gpu = self._make_gpu(name, vram_gb)
                w = entry.get("CurrentHorizontalResolution")
                h = entry.get("CurrentVerticalResolution")
                hz = entry.get("CurrentRefreshRate")
                if w and h:
                    gpu["active_display"] = {"width": w, "height": h, "refresh_hz": hz}
                gpus.append(gpu)
        self._enrich_nvidia(gpus)
        return gpus

    def _gpu_macos(self) -> List[Dict[str, Any]]:
        gpus = []
        result = self._run(["system_profiler", "SPDisplaysDataType", "-json"])
        if result:
            try:
                data = json.loads(result)
                for entry in data.get("SPDisplaysDataType", []):
                    name = entry.get("sppci_model") or entry.get("_name", "Unknown GPU")
                    is_apple = "apple" in name.lower()
                    vram_gb = None
                    if not is_apple:
                        vram_str = entry.get("spdisplays_vram") or entry.get("spdisplays_vram_shared", "")
                        if vram_str:
                            parts = vram_str.split()
                            try:
                                val = float(parts[0])
                                unit = parts[1].upper() if len(parts) > 1 else "MB"
                                vram_gb = round(val / 1024, 2) if "MB" in unit else round(val, 2)
                            except (ValueError, IndexError):
                                pass
                    gpus.append(self._make_gpu(name, vram_gb, unified=is_apple))
            except (json.JSONDecodeError, KeyError):
                pass
        if not gpus:
            raw = self._run(["system_profiler", "SPDisplaysDataType"]) or ""
            if "Apple" in raw:
                gpus.append(self._make_gpu("Apple Silicon", unified=True))
        return gpus

    def _gpu_linux(self) -> List[Dict[str, Any]]:
        gpus = []
        self._enrich_nvidia(gpus)
        if not gpus:
            lspci = self._run(["lspci"])
            if lspci:
                for line in lspci.splitlines():
                    low = line.lower()
                    if "vga" in low or "display" in low or "3d controller" in low:
                        desc = line.split(":", 2)[-1].strip() if ":" in line else line
                        gpus.append(self._make_gpu(desc))
        return gpus

    def _enrich_nvidia(self, gpus: List[Dict[str, Any]]):
        """Overlay accurate VRAM, CUDA device index, compute capability, and driver via nvidia-smi."""
        smi = self._run([
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,compute_cap,driver_version",
            "--format=csv,noheader,nounits",
        ])
        if not smi:
            return
        cuda_version = self._nvidia_cuda_version()
        already_enriched: set[int] = set()
        for line in smi.strip().splitlines():
            parts = [p.strip() for p in line.split(", ")]
            if len(parts) < 3:
                continue
            try:
                cuda_idx = int(parts[0])
            except ValueError:
                cuda_idx = None
            smi_name = parts[1]
            vram_gb = None
            try:
                vram_gb = round(float(parts[2]) / 1024, 2)
            except ValueError:
                pass
            compute_cap = parts[3] if len(parts) > 3 else None
            driver_ver = parts[4] if len(parts) > 4 else None

            match_idx = next(
                (i for i, g in enumerate(gpus)
                 if i not in already_enriched and g["vendor"] == "NVIDIA" and smi_name in g["name"]),
                None,
            )
            if match_idx is not None:
                already_enriched.add(match_idx)
                gpus[match_idx].update({
                    "vram_gb": vram_gb, "cuda_device_index": cuda_idx,
                    "compute_capability": compute_cap, "cuda_version": cuda_version,
                    "driver_version": driver_ver,
                })
            else:
                gpu = self._make_gpu(smi_name, vram_gb)
                gpu.update({
                    "cuda_device_index": cuda_idx, "compute_capability": compute_cap,
                    "cuda_version": cuda_version, "driver_version": driver_ver,
                })
                gpus.append(gpu)

    def _nvidia_cuda_version(self) -> Optional[str]:
        raw = self._run(["nvidia-smi"])
        if raw:
            m = re.search(r"CUDA Version:\s*(\d+\.\d+)", raw)
            if m:
                return m.group(1)
        return None

    # ── RAM ───────────────────────────────────────────────────────────────────

    def _detect_ram(self) -> Dict:
        info = {"total_gb": 0, "available_gb": 0}
        try:
            try:
                import psutil
                mem = psutil.virtual_memory()
                info["total_gb"] = round(mem.total / 1024**3, 2)
                info["available_gb"] = round(mem.available / 1024**3, 2)
                return info
            except ImportError:
                pass

            if self._os == "Windows":
                result = self._ps(
                    "Get-CimInstance Win32_OperatingSystem | "
                    "Select-Object TotalVisibleMemorySize,FreePhysicalMemory | ConvertTo-Json"
                )
                if result:
                    data = result[0] if isinstance(result, list) else result
                    info["total_gb"] = round(data.get("TotalVisibleMemorySize", 0) / 1024**2, 2)
                    info["available_gb"] = round(data.get("FreePhysicalMemory", 0) / 1024**2, 2)
                if info["total_gb"] == 0:
                    self._ram_windows_ctypes(info)
            elif self._os == "Darwin":
                mem = self._sysctl("hw.memsize")
                if mem:
                    info["total_gb"] = round(int(mem) / 1024**3, 2)
            else:
                for line in Path("/proc/meminfo").read_text().splitlines():
                    if line.startswith("MemTotal:"):
                        info["total_gb"] = round(int(line.split()[1]) / 1024**2, 2)
                    elif line.startswith("MemAvailable:"):
                        info["available_gb"] = round(int(line.split()[1]) / 1024**2, 2)
        except Exception:
            pass
        return info

    def _ram_windows_ctypes(self, info: Dict):
        """Fallback when WMI/CIM is unavailable but Win32 APIs are accessible."""
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                info["total_gb"] = round(stat.ullTotalPhys / 1024**3, 2)
                info["available_gb"] = round(stat.ullAvailPhys / 1024**3, 2)
        except Exception:
            pass

    # ── Storage ───────────────────────────────────────────────────────────────

    def _detect_storage(self) -> Dict:
        volumes: List[Dict] = []
        physical_disks: List[Dict] = []
        try:
            if self._os == "Windows":
                vols = self._ps(
                    "Get-PSDrive -PSProvider FileSystem | Select-Object Root,"
                    "@{N='Free';E={$_.Free}},@{N='Used';E={$_.Used}} | ConvertTo-Json"
                )
                if vols:
                    if not isinstance(vols, list):
                        vols = [vols]
                    for v in vols:
                        if not isinstance(v, dict):
                            continue
                        free = v.get("Free") or 0
                        used = v.get("Used") or 0
                        total = free + used
                        if total > 0:
                            volumes.append({
                                "path": v.get("Root", ""),
                                "free_gb": round(free / 1024**3, 2),
                                "total_gb": round(total / 1024**3, 2),
                            })
                # Separate call — Get-PhysicalDisk can be slow on some systems
                pdisks = self._ps(
                    "Get-PhysicalDisk | "
                    "Select-Object FriendlyName,MediaType,BusType,Size | ConvertTo-Json",
                    timeout=20,
                )
                if pdisks:
                    if not isinstance(pdisks, list):
                        pdisks = [pdisks]
                    for d in pdisks:
                        if not isinstance(d, dict):
                            continue
                        size = d.get("Size") or 0
                        bus = d.get("BusType", "")
                        media = d.get("MediaType", "")
                        # BusType is more specific (NVMe, SATA, USB); MediaType = SSD/HDD/Unspecified
                        disk_type = bus if bus in ("NVMe", "USB", "RAID") else (media or "Unknown")
                        physical_disks.append({
                            "name": d.get("FriendlyName", "Unknown"),
                            "type": disk_type,
                            "size_gb": round(size / 1024**3, 2),
                        })

            elif self._os == "Darwin":
                raw = self._run(["system_profiler", "SPStorageDataType", "-json"])
                if raw:
                    for vol in json.loads(raw).get("SPStorageDataType", []):
                        free = vol.get("free_space_in_bytes") or 0
                        total = vol.get("size_in_bytes") or 0
                        medium = vol.get("physical_drive", {}).get("medium_type", "")
                        volumes.append({
                            "path": vol.get("mount_point", vol.get("_name", "")),
                            "free_gb": round(free / 1024**3, 2),
                            "total_gb": round(total / 1024**3, 2),
                            "type": medium,
                        })

            else:  # Linux
                lsblk = self._run(["lsblk", "-J", "-o", "NAME,SIZE,TYPE,ROTA"])
                if lsblk:
                    for dev in json.loads(lsblk).get("blockdevices", []):
                        if dev.get("type") == "disk":
                            physical_disks.append({
                                "name": dev.get("name", ""),
                                "type": "HDD" if str(dev.get("rota", "1")) == "1" else "SSD/NVMe",
                                "size_gb": 0,
                            })
                df = self._run(["df", "-BG", "--output=target,avail,size"])
                if df:
                    for line in df.splitlines()[1:]:
                        parts = line.split()
                        if len(parts) >= 3 and parts[0].startswith("/"):
                            try:
                                volumes.append({
                                    "path": parts[0],
                                    "free_gb": float(parts[1].rstrip("G")),
                                    "total_gb": float(parts[2].rstrip("G")),
                                })
                            except ValueError:
                                pass

        except Exception:
            pass

        # Stdlib fallback for home drive if nothing detected
        if not volumes:
            try:
                u = shutil.disk_usage(Path.home())
                volumes = [{"path": str(Path.home().anchor),
                            "free_gb": round(u.free / 1024**3, 2),
                            "total_gb": round(u.total / 1024**3, 2)}]
            except Exception:
                pass

        return {"volumes": volumes, "physical_disks": physical_disks}

    # ── Displays ─────────────────────────────────────────────────────────────

    def _detect_displays(self) -> List[Dict[str, Any]]:
        displays = []
        try:
            if self._os == "Windows":
                result = self._ps(
                    "Add-Type -AssemblyName System.Windows.Forms; "
                    "[System.Windows.Forms.Screen]::AllScreens | "
                    "Select-Object @{N='Width';E={$_.Bounds.Width}},"
                    "@{N='Height';E={$_.Bounds.Height}},Primary | ConvertTo-Json"
                )
                if result:
                    if not isinstance(result, list):
                        result = [result]
                    for d in result:
                        displays.append({
                            "width": d.get("Width"),
                            "height": d.get("Height"),
                            "primary": bool(d.get("Primary", False)),
                        })
            elif self._os == "Darwin":
                raw = self._run(["system_profiler", "SPDisplaysDataType", "-json"])
                if raw:
                    for entry in json.loads(raw).get("SPDisplaysDataType", []):
                        for d in entry.get("spdisplays_ndrvs", []):
                            res = d.get("_spdisplays_resolution", "")
                            m = re.search(r"(\d+)\s*x\s*(\d+)", res)
                            if m:
                                displays.append({
                                    "width": int(m.group(1)),
                                    "height": int(m.group(2)),
                                    "name": d.get("_name", ""),
                                })
            else:
                xrandr = self._run(["xrandr", "--query"])
                if xrandr:
                    for line in xrandr.splitlines():
                        m = re.search(r"(\d+)x(\d+)\+\d+\+\d+", line)
                        if m:
                            displays.append({"width": int(m.group(1)), "height": int(m.group(2))})
        except Exception:
            pass
        return displays

    # ── Motherboard ───────────────────────────────────────────────────────────

    def _detect_motherboard(self) -> Dict:
        info: Dict = {}
        try:
            if self._os == "Windows":
                # Single PS process for all three WMI classes
                result = self._ps(
                    "@{"
                    "CS=(Get-CimInstance Win32_ComputerSystem|Select-Object Manufacturer,Model);"
                    "BB=(Get-CimInstance Win32_BaseBoard|Select-Object Manufacturer,Product,Version);"
                    "BIOS=(Get-CimInstance Win32_BIOS|Select-Object SMBIOSBIOSVersion,Manufacturer)"
                    "} | ConvertTo-Json -Depth 3"
                )
                if result:
                    cs   = result.get("CS")   or {}
                    bb   = result.get("BB")   or {}
                    bios = result.get("BIOS") or {}
                    info["manufacturer"]    = cs.get("Manufacturer")
                    info["model"]           = cs.get("Model")
                    info["board_manufacturer"] = bb.get("Manufacturer")
                    info["board_model"]     = bb.get("Product")
                    info["board_version"]   = bb.get("Version")
                    info["bios_version"]    = bios.get("SMBIOSBIOSVersion")
                    info["bios_vendor"]     = bios.get("Manufacturer")
            elif self._os == "Darwin":
                raw = self._run(["system_profiler", "SPHardwareDataType", "-json"])
                if raw:
                    hw = json.loads(raw).get("SPHardwareDataType", [{}])[0]
                    info["manufacturer"] = "Apple"
                    info["model"] = hw.get("machine_model")
                    info["serial"] = hw.get("serial_number")
                    info["bios_version"] = hw.get("boot_rom_version")
            else:
                dmi = Path("/sys/class/dmi/id")
                if dmi.exists():
                    def _r(name):
                        try:
                            return (dmi / name).read_text().strip()
                        except Exception:
                            return None
                    info["manufacturer"] = _r("sys_vendor")
                    info["model"] = _r("product_name")
                    info["board_manufacturer"] = _r("board_vendor")
                    info["board_model"] = _r("board_name")
                    info["bios_version"] = _r("bios_version")
                    info["bios_vendor"] = _r("bios_vendor")
        except Exception:
            pass
        return info

    # ── Inference Runtimes ────────────────────────────────────────────────────

    def _check_runtimes(self) -> Dict:
        return {"ollama": self._check_ollama(), "lmstudio": self._check_lmstudio()}

    def _check_ollama(self) -> bool:
        try:
            return subprocess.run(["ollama", "list"], capture_output=True, timeout=10).returncode == 0
        except Exception:
            return False

    def _check_lmstudio(self) -> bool:
        home = Path.home()
        if self._os == "Windows":
            paths = [home / ".lmstudio",
                     home / "AppData" / "Local" / "LM Studio",
                     home / "AppData" / "Local" / "Programs" / "LM Studio"]
        elif self._os == "Darwin":
            paths = [Path("/Applications/LM Studio.app"),
                     home / "Applications" / "LM Studio.app",
                     home / ".lmstudio"]
        else:
            paths = [home / ".lmstudio", home / ".local" / "share" / "lmstudio"]
            if self._run(["which", "lms"]):
                return True
        return any(p.exists() for p in paths)

    # ── Network ───────────────────────────────────────────────────────────────

    def _detect_network(self) -> List[Dict[str, Any]]:
        adapters = []
        try:
            if self._os == "Windows":
                result = self._ps(
                    "Get-NetAdapter | Select-Object Name,InterfaceDescription,"
                    "MacAddress,LinkSpeed,MediaType,PhysicalMediaType,Status | ConvertTo-Json"
                )
                if result:
                    if not isinstance(result, list):
                        result = [result]
                    for a in result:
                        adapters.append({
                            "name": a.get("Name"),
                            "description": a.get("InterfaceDescription"),
                            "mac": a.get("MacAddress"),
                            "speed": a.get("LinkSpeed"),
                            "media_type": a.get("PhysicalMediaType"),
                            "status": a.get("Status"),
                        })
            elif self._os == "Darwin":
                raw = self._run(["system_profiler", "SPNetworkDataType", "-json"])
                if raw:
                    for iface in json.loads(raw).get("SPNetworkDataType", []):
                        adapters.append({
                            "name": iface.get("_name"),
                            "description": iface.get("type"),
                            "mac": iface.get("Ethernet", {}).get("MAC Address"),
                            "status": "active" if iface.get("IPv4") or iface.get("IPv6") else "inactive",
                        })
            else:
                net = Path("/sys/class/net")
                if net.exists():
                    for iface in net.iterdir():
                        try:
                            mac = (iface / "address").read_text().strip()
                            operstate = (iface / "operstate").read_text().strip()
                            speed_path = iface / "speed"
                            speed = None
                            if speed_path.exists():
                                try:
                                    speed = int(speed_path.read_text().strip())
                                except ValueError:
                                    pass
                            adapters.append({
                                "name": iface.name,
                                "mac": mac,
                                "status": operstate,
                                "speed_mbps": speed,
                            })
                        except Exception:
                            pass
        except Exception:
            pass
        return adapters

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _detect_audio(self) -> List[Dict[str, Any]]:
        devices = []
        try:
            if self._os == "Windows":
                result = self._ps(
                    "Get-CimInstance Win32_SoundDevice | "
                    "Select-Object Name,Manufacturer,Status | ConvertTo-Json"
                )
                if result:
                    if not isinstance(result, list):
                        result = [result]
                    for d in result:
                        devices.append({
                            "name": d.get("Name"),
                            "manufacturer": d.get("Manufacturer"),
                            "status": d.get("Status"),
                        })
            elif self._os == "Darwin":
                raw = self._run(["system_profiler", "SPAudioDataType", "-json"])
                if raw:
                    for entry in json.loads(raw).get("SPAudioDataType", []):
                        for item in entry.get("_items", []):
                            devices.append({"name": item.get("_name")})
            else:
                cards = self._run(["aplay", "-l"])
                if cards:
                    for line in cards.splitlines():
                        if line.startswith("card "):
                            devices.append({"name": line.strip()})
        except Exception:
            pass
        return devices

    # ── Battery ───────────────────────────────────────────────────────────────

    _BATTERY_STATUS = {
        1: "Discharging", 2: "AC (plugged in)", 3: "Fully charged",
        4: "Low", 5: "Critical", 6: "Charging", 7: "Charging (high)",
        8: "Charging (low)", 9: "Charging (critical)", 10: "Unknown",
        11: "Partially charged",
    }

    def _detect_battery(self) -> Optional[Dict]:
        try:
            if self._os == "Windows":
                result = self._ps(
                    "Get-CimInstance Win32_Battery | "
                    "Select-Object Name,EstimatedChargeRemaining,BatteryStatus,"
                    "DesignCapacity,FullChargeCapacity | ConvertTo-Json"
                )
                if result:
                    data = result[0] if isinstance(result, list) else result
                    status_code = data.get("BatteryStatus")
                    return {
                        "name": data.get("Name"),
                        "charge_pct": data.get("EstimatedChargeRemaining"),
                        "status": self._BATTERY_STATUS.get(status_code, "Unknown"),
                        "design_capacity_mwh": data.get("DesignCapacity"),
                        "full_capacity_mwh": data.get("FullChargeCapacity"),
                    }
            elif self._os == "Darwin":
                raw = self._run(["system_profiler", "SPPowerDataType", "-json"])
                if raw:
                    power = json.loads(raw).get("SPPowerDataType", [{}])[0]
                    batt = power.get("sppower_battery_model_info", {})
                    state = power.get("sppower_battery_charge_info", {})
                    if batt or state:
                        return {
                            "name": batt.get("sppower_battery_model_name"),
                            "charge_pct": state.get("sppower_battery_state_of_charge"),
                            "status": state.get("sppower_battery_full_charge_capacity"),
                            "cycle_count": batt.get("sppower_battery_cycle_count"),
                        }
            else:
                for bat in Path("/sys/class/power_supply").glob("BAT*"):
                    try:
                        def _bval(name):
                            p = bat / name
                            return p.read_text().strip() if p.exists() else None
                        cap = _bval("capacity")
                        status = _bval("status")
                        return {
                            "name": bat.name,
                            "charge_pct": int(cap) if cap else None,
                            "status": status,
                            "energy_now_uwh": _bval("energy_now"),
                            "energy_full_uwh": _bval("energy_full"),
                        }
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    # ── All Devices (Device Manager equivalent) ───────────────────────────────

    def _detect_all_devices(self) -> Dict:
        """
        Full PnP device tree grouped by class.

        Windows:  Get-PnpDevice  — the same database Device Manager reads.
        macOS:    system_profiler across all hardware data types.
        Linux:    lshw (if available), else /sys/bus/ summary.
        """
        try:
            if self._os == "Windows":
                return self._all_devices_windows()
            elif self._os == "Darwin":
                return self._all_devices_macos()
            else:
                return self._all_devices_linux()
        except Exception:
            return {}

    def _all_devices_windows(self) -> Dict:
        result = self._ps(
            "Get-PnpDevice -Status OK | "
            "Select-Object Class,FriendlyName,Manufacturer,InstanceId | "
            "ConvertTo-Json -Depth 2",
            timeout=30,
        )
        if not result:
            return {}
        if not isinstance(result, list):
            result = [result]
        grouped: Dict[str, List] = {}
        for dev in result:
            cls = dev.get("Class") or "Unknown"
            entry = {k: dev.get(k) for k in ("FriendlyName", "Manufacturer", "InstanceId") if dev.get(k)}
            grouped.setdefault(cls, []).append(entry)
        return dict(sorted(grouped.items()))

    def _all_devices_macos(self) -> Dict:
        types = [
            "SPHardwareDataType", "SPNetworkDataType", "SPAudioDataType",
            "SPStorageDataType", "SPUSBDataType", "SPBluetoothDataType",
            "SPPCIDataType", "SPPowerDataType", "SPCameraDataType",
        ]
        result = {}
        for sp_type in types:
            raw = self._run(["system_profiler", sp_type, "-json"], timeout=10)
            if raw:
                try:
                    result[sp_type] = json.loads(raw).get(sp_type, [])
                except (json.JSONDecodeError, KeyError):
                    pass
        return result

    def _all_devices_linux(self) -> Dict:
        # lshw gives a structured hardware tree if available
        raw = self._run(["lshw", "-json", "-quiet"], timeout=30)
        if raw:
            try:
                return {"lshw": json.loads(raw)}
            except json.JSONDecodeError:
                pass
        # Fallback: list PCI and USB devices
        result = {}
        lspci = self._run(["lspci", "-vmm"])
        if lspci:
            result["pci"] = lspci.strip()
        lsusb = self._run(["lsusb"])
        if lsusb:
            result["usb"] = [line.strip() for line in lsusb.splitlines() if line.strip()]
        return result

    # ── Formatters ────────────────────────────────────────────────────────────

    def _fmt_llm(self, data: Dict) -> Dict:
        """Compact, token-efficient JSON for LLM inference decisions."""
        cpu = data.get("cpu", {})
        ram = data.get("ram", {})
        gpu_data = data.get("gpu", {})
        plat = data.get("platform", {})
        runtimes = data.get("inference_runtimes", {})

        gpus_out = []
        for g in gpu_data.get("all", []):
            entry: Dict = {
                "name": g["name"], "vendor": g["vendor"],
                "role": g["role"], "vram_gb": g.get("vram_gb"),
            }
            if g.get("cuda_device_index") is not None:
                entry["cuda_device"] = g["cuda_device_index"]
            if g.get("compute_capability"):
                entry["compute_sm"] = g["compute_capability"]
            if g.get("cuda_version"):
                entry["cuda_ver"] = g["cuda_version"]
            if g.get("unified_memory"):
                entry["unified_memory"] = True
            gpus_out.append(entry)

        avx = [k for k in ("avx2", "avx512") if cpu.get(k)]

        vols = [{"path": v["path"], "free_gb": v["free_gb"], "total_gb": v["total_gb"]}
                for v in data.get("storage", {}).get("volumes", [])
                if (v.get("total_gb") or 0) > 1]

        # Active network adapters (status Up/connected)
        net_out = []
        for a in data.get("network", []):
            st = (a.get("status") or "").lower()
            if st in ("up", "active", "connected", "linkup"):
                net_out.append({
                    "name": a.get("description") or a.get("name"),
                    "media": a.get("media_type") or a.get("speed"),
                })

        battery = data.get("battery")
        battery_out = None
        if battery:
            battery_out = {"charge_pct": battery.get("charge_pct"), "status": battery.get("status")}

        cpu_out = {"name": cpu.get("name"), "threads": cpu.get("threads"), "avx": avx}
        if cpu.get("cores"):
            cpu_out["cores"] = cpu.get("cores")

        out = {
            "platform": f"{plat.get('os')} {plat.get('machine')}",
            "cpu": cpu_out,
            "ram_gb": ram.get("total_gb"),
            "ram_free_gb": ram.get("available_gb"),
            "gpus": gpus_out,
            "storage": vols,
            "runtimes": [k for k, v in runtimes.items() if v],
        }
        if net_out:
            out["network"] = net_out
        if battery_out:
            out["battery"] = battery_out
        return out

    def _fmt_standard(self, data: Dict) -> str:
        """Human-readable hardware summary."""
        W = 60
        sep = "─" * W
        lines = []

        def row(label, value):
            lines.append(f"  {label:<10}{value}")

        ts = data.get("detected_at", "")[:16].replace("T", " ")
        lines += [sep, f"  Hardware Report — {ts}", sep]

        plat = data.get("platform", {})
        row("OS", f"{plat.get('os')} {plat.get('os_release', '')}  ({plat.get('machine')})")
        row("Python", plat.get("python_version", ""))
        lines.append("")

        cpu = data.get("cpu", {})
        avx = " + ".join(k.upper().replace("AVX", "AVX-") for k in ("avx2", "avx512") if cpu.get(k))
        row("CPU", cpu.get("name", "Unknown"))
        if cpu.get("cores"):
            cpu_topology = f"{cpu.get('cores')} cores / {cpu.get('threads')} threads"
        else:
            cpu_topology = f"{cpu.get('threads')} logical threads"
        row("", cpu_topology + (f"  ·  {avx}" if avx else ""))

        ram = data.get("ram", {})
        row("RAM", f"{ram.get('total_gb')} GB total  /  {ram.get('available_gb')} GB available")
        lines.append("")

        gpu_data = data.get("gpu", {})
        primary_name = (gpu_data.get("primary") or {}).get("name")
        for i, g in enumerate(gpu_data.get("all", [])):
            is_primary = g["name"] == primary_name
            marker = "►" if is_primary else " "
            vram = f"{g['vram_gb']} GB" if g.get("vram_gb") else "shared"
            extras = []
            if g.get("cuda_device_index") is not None:
                extras.append(f"CUDA device {g['cuda_device_index']}")
            if g.get("compute_capability"):
                extras.append(f"SM {g['compute_capability']}")
            if g.get("cuda_version"):
                extras.append(f"CUDA {g['cuda_version']}")
            extra_str = "  ·  " + "  ·  ".join(extras) if extras else ""
            lines.append(f"  {marker} GPU[{i}]  {g['name']}")
            lines.append(f"           {vram} VRAM  ·  {g['role']}{extra_str}")
            if g.get("driver_version"):
                lines.append(f"           Driver {g['driver_version']}")
        lines.append("")

        storage = data.get("storage", {})
        vols = storage.get("volumes", [])
        pdisks = storage.get("physical_disks", [])
        for v in vols:
            row("Storage", f"{v['path']}  {v['free_gb']} GB free / {v['total_gb']} GB"
                + (f"  ({v['type']})" if v.get("type") else ""))
        if pdisks:
            for d in pdisks:
                row("", f"{d['name']}  ·  {d['type']}  ·  {d['size_gb']} GB")
        lines.append("")

        displays = data.get("displays", [])
        if displays:
            disp_str = "  |  ".join(
                f"{d['width']}×{d['height']}" + (" (primary)" if d.get("primary") else "")
                for d in displays
            )
            row("Display", disp_str)

        board = data.get("motherboard", {})
        if board:
            sys_str = " ".join(filter(None, [board.get("manufacturer"), board.get("model")]))
            bios_str = f"  ·  BIOS {board['bios_version']}" if board.get("bios_version") else ""
            if sys_str:
                row("Board", sys_str + bios_str)

        # Network — show only active adapters
        net_active = [
            a for a in data.get("network", [])
            if (a.get("status") or "").lower() in ("up", "active", "connected", "linkup")
        ]
        if net_active:
            for a in net_active:
                label = a.get("description") or a.get("name") or ""
                speed = f"  ·  {a['speed']}" if a.get("speed") else ""
                row("Network", f"{label}{speed}")

        # Audio
        audio = data.get("audio", [])
        if audio:
            row("Audio", "  |  ".join(a.get("name", "") for a in audio if a.get("name")))

        # Battery
        battery = data.get("battery")
        if battery:
            pct = battery.get("charge_pct")
            status = battery.get("status", "")
            name = battery.get("name", "Battery")
            row("Battery", f"{name}  ·  {pct}%  ·  {status}" if pct is not None else status)

        runtimes = data.get("inference_runtimes", {})
        if runtimes:
            rt_str = "  |  ".join(
                f"{k.capitalize()} {'✓' if v else '✗'}" for k, v in runtimes.items()
            )
            row("Runtimes", rt_str)

        # all_devices summary (count by class)
        all_dev = data.get("all_devices", {})
        if all_dev and self._os == "Windows":
            counts = {cls: len(devs) for cls, devs in all_dev.items() if devs}
            summary = "  ".join(f"{cls}:{n}" for cls, n in sorted(counts.items()) if n > 0)
            if summary:
                lines.append("")
                lines.append(f"  Device classes (OK):  {summary}")

        lines.append(sep)
        return "\n".join(lines)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _run(self, cmd: List[str], timeout: int = 15) -> Optional[str]:
        """Run a command and return stdout, or None on failure/timeout.

        Uses a daemon thread instead of subprocess.run(timeout=) to avoid a
        Windows bug where the stdout-reading thread outlives the killed process,
        making KeyboardInterrupt unable to interrupt thread.join().
        """
        _buf: List[Optional[bytes]] = [None]

        def _target():
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, _ = p.communicate()
                if p.returncode == 0:
                    _buf[0] = stdout
            except Exception:
                pass

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout)
        raw = _buf[0]
        return raw.decode("utf-8", errors="replace") if raw and raw.strip() else None

    def _ps(self, cmd: str, timeout: int = 15) -> Any:
        # -NoProfile skips loading the user profile, saving ~0.5-1s per call
        for ps_exe in ("pwsh", "powershell"):
            raw = self._run([ps_exe, "-NoProfile", "-Command", cmd], timeout=timeout)
            if raw:
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    pass
        return None

    def _sysctl(self, key: str) -> Optional[str]:
        raw = self._run(["sysctl", "-n", key])
        return raw.strip() if raw else None

    # ── Persistence ───────────────────────────────────────────────────────────

    def save_to_settings(self, hardware: Dict = None) -> Path:
        if hardware is None:
            hardware = self.detect()
        settings = {}
        if self.settings_path.exists():
            try:
                settings = json.loads(self.settings_path.read_text())
            except Exception:
                pass
        settings["hardware"] = hardware
        self.settings_path.write_text(json.dumps(settings, indent=2))
        return self.settings_path

    def load_from_settings(self) -> Optional[Dict]:
        if self.settings_path.exists():
            try:
                return json.loads(self.settings_path.read_text()).get("hardware")
            except Exception:
                pass
        return None


def detect_and_save_hardware(settings_path: Optional[Union[str, Path]] = None) -> Dict:
    detector = HardwareDetector(settings_path)
    hardware = detector.detect()
    detector.save_to_settings(hardware)
    return hardware


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Detect system hardware")
    parser.add_argument(
        "--mode", choices=["verbose", "standard", "llm"], default="standard",
        help="verbose: full JSON | standard: human-readable text | llm: compact JSON"
    )
    parser.add_argument("--save", action="store_true", help="Save to LLM_Tools/Data/settings.json")
    args = parser.parse_args()

    detector = HardwareDetector()
    data = detector.detect()
    if args.save:
        detector.save_to_settings(data)

    result = detector.format(data, args.mode)
    print(result if isinstance(result, str) else json.dumps(result, indent=2))
