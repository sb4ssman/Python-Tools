"""
Hardware Detection Utility

Detects system hardware capabilities (CPU, GPU, RAM) and saves to settings.
Designed for use as a drop-in tool for LLMs to assess local inference capability.
"""

import json
import platform
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Optional


class HardwareDetector:
    """Detect and report system hardware capabilities."""

    def __init__(self, settings_path: str = "Data/settings.json"):
        self.settings_path = Path(settings_path)
        self._ensure_settings_dir()

    def _ensure_settings_dir(self):
        """Ensure settings directory exists."""
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

    def detect(self) -> Dict:
        """
        Detect all hardware information.

        Returns:
            Dictionary with hardware details
        """
        hardware = {
            "id": str(uuid.uuid4()),
            "platform": self._detect_platform(),
            "cpu": self._detect_cpu(),
            "gpu": self._detect_gpu(),
            "ram": self._detect_ram(),
            "ollama_installed": self._check_ollama(),
            "lmstudio_installed": self._check_lmstudio(),
            "detected_at": self._get_timestamp()
        }

        return hardware

    def _detect_platform(self) -> Dict:
        """Detect platform information."""
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }

    def _detect_cpu(self) -> Dict:
        """Detect CPU information."""
        cpu_info = {
            "name": "Unknown",
            "cores": 0,
            "threads": 0,
            "arch": platform.machine()
        }

        try:
            os_name = platform.system()

            if os_name == "Windows":
                ps_cmd = "Get-CimInstance -ClassName Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | ConvertTo-Json"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        if isinstance(data, list):
                            data = data[0]
                        cpu_info["name"] = data.get("Name", "Unknown")
                        cpu_info["cores"] = data.get("NumberOfCores", 0)
                        cpu_info["threads"] = data.get("NumberOfLogicalProcessors", 0)
                    except json.JSONDecodeError:
                        pass

            elif os_name == "Darwin":
                # CPU name
                r = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    cpu_info["name"] = r.stdout.strip()
                # Physical cores
                r = subprocess.run(["sysctl", "-n", "hw.physicalcpu"],
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    cpu_info["cores"] = int(r.stdout.strip())
                # Logical threads
                r = subprocess.run(["sysctl", "-n", "hw.logicalcpu"],
                                   capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    cpu_info["threads"] = int(r.stdout.strip())

            else:  # Linux
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        cpuinfo = f.read()
                    for line in cpuinfo.splitlines():
                        if "model name" in line and cpu_info["name"] == "Unknown":
                            cpu_info["name"] = line.split(":", 1)[1].strip()
                        if "cpu cores" in line and cpu_info["cores"] == 0:
                            cpu_info["cores"] = int(line.split(":", 1)[1].strip())
                        if "siblings" in line and cpu_info["threads"] == 0:
                            cpu_info["threads"] = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
                # Fallback thread count
                if cpu_info["threads"] == 0:
                    r = subprocess.run(["nproc"], capture_output=True, text=True, timeout=5)
                    if r.returncode == 0:
                        cpu_info["threads"] = int(r.stdout.strip())
                        if cpu_info["cores"] == 0:
                            cpu_info["cores"] = cpu_info["threads"]

        except Exception:
            pass

        return cpu_info

    def _detect_gpu(self) -> Dict:
        """Detect GPU information."""
        gpu_info = {
            "name": None,
            "vendor": None,
            "vram_gb": None,
            "cuda_capable": False,
            "unified_memory": False,  # True for Apple Silicon (GPU shares system RAM)
            "gpus": []
        }

        try:
            os_name = platform.system()

            if os_name == "Windows":
                ps_cmd = "Get-CimInstance -ClassName Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        data = json.loads(result.stdout)
                        if not isinstance(data, list):
                            data = [data]
                        gpus = []
                        for gpu in data:
                            gpu_name = gpu.get("Name")
                            if gpu_name:
                                vram_bytes = gpu.get("AdapterRAM")
                                vram_gb = round(vram_bytes / (1024**3), 2) if vram_bytes else None
                                gpu_lower = gpu_name.lower()
                                if "nvidia" in gpu_lower:
                                    vendor, cuda = "NVIDIA", True
                                elif "amd" in gpu_lower or "radeon" in gpu_lower:
                                    vendor, cuda = "AMD", False
                                elif "intel" in gpu_lower:
                                    vendor, cuda = "Intel", False
                                else:
                                    vendor, cuda = "Unknown", False
                                gpus.append({
                                    "name": gpu_name, "vendor": vendor,
                                    "vram_gb": vram_gb, "cuda_capable": cuda,
                                    "unified_memory": False
                                })
                        if gpus:
                            primary = next((g for g in gpus if g["vendor"] == "NVIDIA"), gpus[0])
                            gpu_info.update({k: primary[k] for k in ("name", "vendor", "vram_gb", "cuda_capable")})
                            gpu_info["gpus"] = gpus
                    except json.JSONDecodeError:
                        pass

            elif os_name == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType", "-json"],
                    capture_output=True, text=True, timeout=30
                )
                gpus = []
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        sp_data = json.loads(result.stdout)
                        displays = sp_data.get("SPDisplaysDataType", [])
                        for entry in displays:
                            gpu_name = entry.get("sppci_model") or entry.get("_name", "Unknown GPU")
                            gpu_lower = gpu_name.lower()
                            is_apple = "apple" in gpu_lower
                            if "nvidia" in gpu_lower:
                                vendor, cuda = "NVIDIA", True
                            elif "amd" in gpu_lower or "radeon" in gpu_lower:
                                vendor, cuda = "AMD", False
                            elif is_apple:
                                vendor, cuda = "Apple", False
                            elif "intel" in gpu_lower:
                                vendor, cuda = "Intel", False
                            else:
                                vendor, cuda = "Unknown", False

                            # VRAM: discrete GPUs report it; Apple Silicon uses unified memory
                            vram_gb = None
                            unified = False
                            if is_apple:
                                unified = True
                                # Unified memory = system RAM; we'll fill this in from RAM detection
                            else:
                                vram_str = entry.get("spdisplays_vram") or entry.get("spdisplays_vram_shared", "")
                                if vram_str:
                                    # e.g. "8192 MB" or "16 GB"
                                    parts = vram_str.split()
                                    try:
                                        val = float(parts[0])
                                        unit = parts[1].upper() if len(parts) > 1 else "MB"
                                        vram_gb = round(val / 1024, 2) if "MB" in unit else round(val, 2)
                                    except (ValueError, IndexError):
                                        pass

                            gpus.append({
                                "name": gpu_name, "vendor": vendor,
                                "vram_gb": vram_gb, "cuda_capable": cuda,
                                "unified_memory": unified
                            })
                    except (json.JSONDecodeError, KeyError):
                        pass

                if not gpus:
                    # Fallback: text parsing
                    result = subprocess.run(
                        ["system_profiler", "SPDisplaysDataType"],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0 and "Apple" in result.stdout:
                        gpus = [{"name": "Apple Silicon", "vendor": "Apple",
                                 "vram_gb": None, "cuda_capable": False, "unified_memory": True}]

                if gpus:
                    primary = next((g for g in gpus if g["vendor"] == "NVIDIA"),
                                   next((g for g in gpus if g["vendor"] == "AMD"), gpus[0]))
                    gpu_info.update({k: primary[k] for k in ("name", "vendor", "vram_gb", "cuda_capable", "unified_memory")})
                    gpu_info["gpus"] = gpus

            else:  # Linux
                # Try nvidia-smi first (most reliable for NVIDIA)
                nvidia_result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10
                )
                if nvidia_result.returncode == 0 and nvidia_result.stdout.strip():
                    gpus = []
                    for line in nvidia_result.stdout.strip().splitlines():
                        parts = line.split(", ", 1)
                        if parts:
                            name = parts[0].strip()
                            vram_gb = None
                            if len(parts) > 1:
                                try:
                                    vram_mb = float(parts[1].strip())
                                    vram_gb = round(vram_mb / 1024, 2)
                                except ValueError:
                                    pass
                            gpus.append({
                                "name": name, "vendor": "NVIDIA",
                                "vram_gb": vram_gb, "cuda_capable": True,
                                "unified_memory": False
                            })
                    if gpus:
                        gpu_info.update({k: gpus[0][k] for k in ("name", "vendor", "vram_gb", "cuda_capable", "unified_memory")})
                        gpu_info["gpus"] = gpus

                # Also try lspci for AMD/Intel/other (even if NVIDIA found, collect all)
                if not gpu_info["gpus"]:
                    lspci_result = subprocess.run(
                        ["lspci"],
                        capture_output=True, text=True, timeout=10
                    )
                    if lspci_result.returncode == 0:
                        gpus = []
                        for line in lspci_result.stdout.splitlines():
                            line_lower = line.lower()
                            if "vga" in line_lower or "display" in line_lower or "3d controller" in line_lower:
                                # Extract the description after the class
                                desc = line.split(":", 2)[-1].strip() if ":" in line else line
                                if "nvidia" in line_lower:
                                    vendor, cuda = "NVIDIA", True
                                elif "amd" in line_lower or "radeon" in line_lower or "ati" in line_lower:
                                    vendor, cuda = "AMD", False
                                elif "intel" in line_lower:
                                    vendor, cuda = "Intel", False
                                else:
                                    vendor, cuda = "Unknown", False
                                gpus.append({
                                    "name": desc, "vendor": vendor,
                                    "vram_gb": None, "cuda_capable": cuda,
                                    "unified_memory": False
                                })
                        if gpus:
                            primary = next((g for g in gpus if g["vendor"] == "NVIDIA"),
                                           next((g for g in gpus if g["vendor"] == "AMD"), gpus[0]))
                            gpu_info.update({k: primary[k] for k in ("name", "vendor", "vram_gb", "cuda_capable", "unified_memory")})
                            gpu_info["gpus"] = gpus

        except Exception:
            pass

        return gpu_info

    def _detect_ram(self) -> Dict:
        """Detect RAM information."""
        ram_info = {
            "total_gb": 0,
            "available_gb": 0
        }

        try:
            # psutil is the most reliable cross-platform method
            try:
                import psutil
                mem = psutil.virtual_memory()
                ram_info["total_gb"] = round(mem.total / (1024**3), 2)
                ram_info["available_gb"] = round(mem.available / (1024**3), 2)
                return ram_info
            except ImportError:
                pass

            os_name = platform.system()

            if os_name == "Windows":
                ps_cmd = "(Get-CimInstance -ClassName Win32_ComputerSystem).TotalPhysicalMemory"
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        ram_info["total_gb"] = round(int(result.stdout.strip()) / (1024**3), 2)
                    except ValueError:
                        pass

            elif os_name == "Darwin":
                result = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    try:
                        ram_info["total_gb"] = round(int(result.stdout.strip()) / (1024**3), 2)
                    except ValueError:
                        pass

            else:  # Linux
                try:
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                kb = int(line.split()[1])
                                ram_info["total_gb"] = round(kb / (1024**2), 2)
                            elif line.startswith("MemAvailable:"):
                                kb = int(line.split()[1])
                                ram_info["available_gb"] = round(kb / (1024**2), 2)
                except Exception:
                    pass

        except Exception:
            pass

        return ram_info

    def _check_ollama(self) -> bool:
        """Check if Ollama is installed."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _check_lmstudio(self) -> bool:
        """Check if LM Studio is installed."""
        possible_paths = []
        home = Path.home()
        os_name = platform.system()

        if os_name == "Windows":
            possible_paths = [
                home / "AppData" / "Local" / "LM Studio",
                home / "LM Studio",
            ]
        elif os_name == "Darwin":
            possible_paths = [
                Path("/Applications/LM Studio.app"),
                home / "Applications" / "LM Studio.app",
            ]
        else:  # Linux
            possible_paths = [
                home / ".local" / "share" / "lmstudio",
                home / ".lmstudio",
            ]
            # Also check if the CLI is on PATH
            try:
                result = subprocess.run(["which", "lms"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return True
            except Exception:
                pass

        return any(p.exists() for p in possible_paths)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def save_to_settings(self, hardware: Dict = None) -> Path:
        """
        Save hardware detection results to settings file.

        Args:
            hardware: Hardware info dict (if None, will detect)

        Returns:
            Path to settings file
        """
        if hardware is None:
            hardware = self.detect()

        settings = {}
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
            except Exception:
                pass

        settings["hardware"] = hardware

        with open(self.settings_path, "w") as f:
            json.dump(settings, f, indent=2)

        return self.settings_path

    def load_settings(self) -> Optional[Dict]:
        """Load hardware settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                    return settings.get("hardware")
            except Exception:
                pass
        return None


def detect_and_save_hardware(settings_path: str = "Data/settings.json") -> Dict:
    """
    Convenience function to detect hardware and save to settings.

    Args:
        settings_path: Path to settings file

    Returns:
        Hardware detection results
    """
    detector = HardwareDetector(settings_path)
    hardware = detector.detect()
    detector.save_to_settings(hardware)
    return hardware


if __name__ == "__main__":
    hardware = detect_and_save_hardware()
    print(json.dumps(hardware, indent=2))
