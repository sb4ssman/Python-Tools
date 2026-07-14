/**
 * Hardware detector — TypeScript port of tools/hardware_detector.py.
 *
 * What it does
 *   Collects a point-in-time hardware inventory and formats it for three common
 *   audiences: a readable terminal report, compact JSON for LLM context, and full
 *   JSON for debugging or archival snapshots. It is useful when choosing local
 *   inference models, checking GPU/VRAM availability, or giving an agent enough
 *   machine context to make sane tool recommendations.
 *
 * Platform support
 *   Windows   PowerShell/WMI (CIM), nvidia-smi
 *   macOS     sysctl, system_profiler, nvidia-smi
 *   Linux     /proc, /sys, nvidia-smi, lspci/lshw/lsusb
 *
 * Runtime
 *   Server-side Node ONLY. Uses child_process + fs, so it cannot run in the
 *   browser or on an `edge` runtime. RAM is read from Node's `os` module
 *   (replaces the Python script's psutil / WMI / ctypes ladder with one
 *   reliable cross-platform built-in).
 *
 * Usage (import API)
 *   import { HardwareDetector } from '@/lib/hardware/hardwareDetector';
 *   const det = new HardwareDetector();
 *   const data = await det.detect();
 *   console.log(det.format(data, 'standard'));
 *   const llm = det.format(data, 'llm');     // compact object for model-fit logic
 *
 * Usage (CLI, via tsx)
 *   tsx apps/thermonode-lab/lib/hardware/hardwareDetector.ts --mode llm
 *   tsx apps/thermonode-lab/lib/hardware/hardwareDetector.ts --mode verbose --save
 *
 * JSON shape note
 *   The emitted objects keep the SAME snake_case keys as the Python `--mode llm`
 *   / verbose output, so this is a drop-in replacement for any consumer of the
 *   original tool.
 */

import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { randomUUID } from 'node:crypto';
import * as os from 'node:os';
import * as fs from 'node:fs';
import * as path from 'node:path';

const execFileAsync = promisify(execFile);

type OsName = 'Windows' | 'Darwin' | 'Linux';

export interface GpuInfo {
  name: string;
  vendor: 'NVIDIA' | 'AMD' | 'Apple' | 'Intel' | 'Unknown';
  role: 'discrete' | 'integrated' | 'unified';
  vram_gb: number | null;
  cuda_capable: boolean;
  cuda_device_index: number | null;
  unified_memory: boolean;
  compute_capability?: string | null;
  cuda_version?: string | null;
  driver_version?: string | null;
  active_display?: { width: number; height: number; refresh_hz: number | null };
}

export interface HardwareData {
  id: string;
  detected_at: string;
  platform: Record<string, unknown>;
  cpu: { name: string; cores: number; threads: number; arch: string; avx2: boolean; avx512: boolean };
  gpu: { primary: GpuInfo | null; all: GpuInfo[] };
  ram: { total_gb: number; available_gb: number };
  storage: { volumes: Array<Record<string, unknown>>; physical_disks: Array<Record<string, unknown>> };
  displays: Array<Record<string, unknown>>;
  motherboard: Record<string, unknown>;
  network: Array<Record<string, unknown>>;
  audio: Array<Record<string, unknown>>;
  battery: Record<string, unknown> | null;
  all_devices: Record<string, unknown>;
  inference_runtimes: { ollama: boolean; lmstudio: boolean };
}

export type LlmHardware = {
  platform: string;
  cpu: { name?: string; threads?: number; avx: string[]; cores?: number };
  ram_gb: number;
  ram_free_gb: number;
  gpus: Array<Record<string, unknown>>;
  storage: Array<{ path: string; free_gb: number; total_gb: number }>;
  runtimes: string[];
  network?: Array<Record<string, unknown>>;
  battery?: { charge_pct: unknown; status: unknown };
};

const GB = 1024 ** 3;
const round2 = (n: number) => Math.round(n * 100) / 100;

// ── Low-level command helpers ────────────────────────────────────────────────

/** Run a command, return stdout or null on failure/timeout/non-zero exit. */
async function run(cmd: string[], timeoutMs = 15000): Promise<string | null> {
  const [file, ...args] = cmd;
  try {
    const { stdout } = await execFileAsync(file, args, {
      timeout: timeoutMs,
      maxBuffer: 32 * 1024 * 1024,
      windowsHide: true,
    });
    const out = typeof stdout === 'string' ? stdout : Buffer.from(stdout).toString('utf8');
    return out && out.trim() ? out : null;
  } catch {
    return null;
  }
}

/** Run a PowerShell command (pwsh first, then powershell) and JSON.parse stdout. */
async function ps(cmd: string, timeoutMs = 15000): Promise<any> {
  for (const exe of ['pwsh', 'powershell']) {
    // -NoProfile skips loading the user profile, saving ~0.5-1s per call
    const raw = await run([exe, '-NoProfile', '-Command', cmd], timeoutMs);
    if (raw) {
      try {
        return JSON.parse(raw);
      } catch {
        /* not JSON — try next exe */
      }
    }
  }
  return null;
}

async function sysctl(key: string): Promise<string | null> {
  const raw = await run(['sysctl', '-n', key]);
  return raw ? raw.trim() : null;
}

function detectOs(): OsName {
  if (process.platform === 'win32') return 'Windows';
  if (process.platform === 'darwin') return 'Darwin';
  return 'Linux';
}

function machine(): string {
  try {
    return (os as unknown as { machine?: () => string }).machine?.() ?? process.arch;
  } catch {
    return process.arch;
  }
}

// ── Detector ─────────────────────────────────────────────────────────────────

export class HardwareDetector {
  private readonly os: OsName;
  readonly settingsPath: string;

  constructor(settingsPath?: string) {
    this.os = detectOs();
    this.settingsPath = settingsPath ?? path.join(process.cwd(), 'Data', 'settings.json');
  }

  // ── Public API ──────────────────────────────────────────────────────────

  async detect(): Promise<HardwareData> {
    const [
      cpu, gpu, ram, storage, displays, motherboard, network, audio, battery, allDevices, runtimes,
    ] = await Promise.all([
      this.detectCpu(),
      this.detectGpu(),
      this.detectRam(),
      this.detectStorage(),
      this.detectDisplays(),
      this.detectMotherboard(),
      this.detectNetwork(),
      this.detectAudio(),
      this.detectBattery(),
      this.detectAllDevices(),
      this.checkRuntimes(),
    ]);
    return {
      id: randomUUID(),
      detected_at: new Date().toISOString(),
      platform: this.detectPlatform(),
      cpu, gpu, ram, storage, displays, motherboard, network, audio, battery,
      all_devices: allDevices,
      inference_runtimes: runtimes,
    };
  }

  format(data: HardwareData, mode: 'llm'): LlmHardware;
  format(data: HardwareData, mode: 'standard'): string;
  format(data: HardwareData, mode: 'verbose'): HardwareData;
  format(data: HardwareData, mode: 'llm' | 'standard' | 'verbose' = 'standard'): LlmHardware | string | HardwareData {
    if (mode === 'llm') return this.fmtLlm(data);
    if (mode === 'standard') return this.fmtStandard(data);
    return data;
  }

  async output(mode: 'llm'): Promise<LlmHardware>;
  async output(mode: 'standard'): Promise<string>;
  async output(mode: 'verbose'): Promise<HardwareData>;
  async output(mode: 'llm' | 'standard' | 'verbose' = 'standard'): Promise<LlmHardware | string | HardwareData> {
    return this.format(await this.detect(), mode as 'standard');
  }

  // ── Platform ────────────────────────────────────────────────────────────

  private detectPlatform(): Record<string, unknown> {
    return {
      os: this.os,
      os_version: os.version(),
      os_release: os.release(),
      machine: machine(),
      processor: process.env.PROCESSOR_IDENTIFIER ?? '',
      node_version: process.version,
    };
  }

  // ── CPU ─────────────────────────────────────────────────────────────────

  private async detectCpu(): Promise<HardwareData['cpu']> {
    const info: HardwareData['cpu'] = {
      name: 'Unknown', cores: 0, threads: 0, arch: machine(), avx2: false, avx512: false,
    };
    try {
      if (this.os === 'Windows') await this.cpuWindows(info);
      else if (this.os === 'Darwin') await this.cpuMacos(info);
      else await this.cpuLinux(info);
    } catch {
      /* ignore */
    }
    if (info.name === 'Unknown') {
      info.name = process.env.PROCESSOR_IDENTIFIER || os.cpus()[0]?.model?.trim() || machine() || 'Unknown';
    }
    if (info.threads === 0) info.threads = os.cpus().length || 0;
    return info;
  }

  private async cpuWindows(info: HardwareData['cpu']): Promise<void> {
    const result = await ps(
      'Get-CimInstance Win32_Processor | ' +
      'Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json',
    );
    if (result) {
      const data = Array.isArray(result) ? result[0] : result;
      info.name = (data.Name ?? 'Unknown').trim();
      info.cores = data.NumberOfCores ?? 0;
      info.threads = data.NumberOfLogicalProcessors ?? 0;
    }
    // System.Runtime.Intrinsics requires .NET 5+ (pwsh/PS7); fall through to powershell otherwise
    for (const exe of ['pwsh', 'powershell']) {
      const avxRaw = await run(
        [exe, '-NoProfile', '-Command',
          '@{avx2=[System.Runtime.Intrinsics.X86.Avx2]::IsSupported;' +
          'avx512=[System.Runtime.Intrinsics.X86.Avx512F]::IsSupported} | ConvertTo-Json'],
        8000,
      );
      if (avxRaw != null) {
        try {
          const avx = JSON.parse(avxRaw);
          info.avx2 = Boolean(avx.avx2);
          info.avx512 = Boolean(avx.avx512);
        } catch {
          /* ignore */
        }
        break;
      }
    }
  }

  private async cpuMacos(info: HardwareData['cpu']): Promise<void> {
    info.name = (await sysctl('machdep.cpu.brand_string')) || 'Apple Silicon';
    const cores = await sysctl('hw.physicalcpu');
    if (cores) info.cores = parseInt(cores, 10);
    const threads = await sysctl('hw.logicalcpu');
    if (threads) info.threads = parseInt(threads, 10);
    if (machine() === 'x86_64') {
      info.avx2 = (await sysctl('hw.optional.avx2_0')) === '1';
      info.avx512 = (await sysctl('hw.optional.avx512f')) === '1';
    }
    // Apple Silicon: no AVX; avx2/avx512 remain false
  }

  private async cpuLinux(info: HardwareData['cpu']): Promise<void> {
    try {
      const cpuinfo = fs.readFileSync('/proc/cpuinfo', 'utf8');
      for (const line of cpuinfo.split('\n')) {
        if (line.includes('model name') && info.name === 'Unknown') {
          info.name = line.split(':').slice(1).join(':').trim();
        }
        if (line.includes('cpu cores') && info.cores === 0) {
          info.cores = parseInt(line.split(':')[1].trim(), 10);
        }
        if (line.includes('siblings') && info.threads === 0) {
          info.threads = parseInt(line.split(':')[1].trim(), 10);
        }
      }
      const flags = cpuinfo.match(/^flags\s*:(.+)/m);
      if (flags) {
        const flagList = flags[1].split(/\s+/);
        info.avx2 = flagList.includes('avx2');
        info.avx512 = flagList.includes('avx512f');
      }
    } catch {
      /* ignore */
    }
    if (info.threads === 0) {
      const r = await run(['nproc']);
      if (r) {
        info.threads = parseInt(r.trim(), 10);
        if (info.cores === 0) info.cores = info.threads;
      }
    }
  }

  // ── GPU ─────────────────────────────────────────────────────────────────

  private async detectGpu(): Promise<HardwareData['gpu']> {
    let gpus: GpuInfo[] = [];
    try {
      if (this.os === 'Windows') gpus = await this.gpuWindows();
      else if (this.os === 'Darwin') gpus = await this.gpuMacos();
      else gpus = await this.gpuLinux();
    } catch {
      /* ignore */
    }
    const primary =
      gpus.find(g => g.vendor === 'NVIDIA' && g.role === 'discrete') ??
      gpus.find(g => g.vendor === 'AMD' && g.role === 'discrete') ??
      (gpus[0] ?? null);
    return { primary, all: gpus };
  }

  private makeGpu(name: string, vramGb: number | null = null, unified = false): GpuInfo {
    const low = name.toLowerCase();
    let vendor: GpuInfo['vendor'];
    let cudaCapable = false;
    let role: GpuInfo['role'];
    if (low.includes('nvidia')) {
      vendor = 'NVIDIA'; cudaCapable = true; role = 'discrete';
    } else if (low.includes('amd') || low.includes('radeon') || low.includes('ati')) {
      vendor = 'AMD';
      // Common iGPU naming: "Radeon(TM) 610M/780M/890M" without "RX"/"Pro"
      role = ['rx ', 'pro w', ' pro ', 'vega '].some(x => low.includes(x)) ? 'discrete' : 'integrated';
    } else if (low.includes('apple')) {
      vendor = 'Apple'; role = 'unified';
    } else if (low.includes('intel')) {
      vendor = 'Intel'; role = 'integrated';
    } else {
      vendor = 'Unknown'; role = 'discrete';
    }
    return {
      name, vendor, role,
      vram_gb: vramGb,
      cuda_capable: cudaCapable,
      cuda_device_index: null,
      unified_memory: unified,
    };
  }

  private async gpuWindows(): Promise<GpuInfo[]> {
    const gpus: GpuInfo[] = [];
    let result = await ps(
      'Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,' +
      'CurrentHorizontalResolution,CurrentVerticalResolution,CurrentRefreshRate | ConvertTo-Json',
    );
    if (result) {
      if (!Array.isArray(result)) result = [result];
      for (const entry of result) {
        const name = entry.Name;
        if (!name) continue;
        // AdapterRAM is a 32-bit WMI field — caps at ~4 GB; nvidia-smi corrects it below
        const vramBytes = entry.AdapterRAM;
        const vramGb = vramBytes ? round2(Number(vramBytes) / GB) : null;
        const gpu = this.makeGpu(name, vramGb);
        const w = entry.CurrentHorizontalResolution;
        const h = entry.CurrentVerticalResolution;
        const hz = entry.CurrentRefreshRate;
        if (w && h) gpu.active_display = { width: w, height: h, refresh_hz: hz ?? null };
        gpus.push(gpu);
      }
    }
    await this.enrichNvidia(gpus);
    return gpus;
  }

  private async gpuMacos(): Promise<GpuInfo[]> {
    const gpus: GpuInfo[] = [];
    const result = await run(['system_profiler', 'SPDisplaysDataType', '-json']);
    if (result) {
      try {
        const data = JSON.parse(result);
        for (const entry of data.SPDisplaysDataType ?? []) {
          const name = entry.sppci_model || entry._name || 'Unknown GPU';
          const isApple = name.toLowerCase().includes('apple');
          let vramGb: number | null = null;
          if (!isApple) {
            const vramStr: string = entry.spdisplays_vram || entry.spdisplays_vram_shared || '';
            if (vramStr) {
              const parts = vramStr.split(/\s+/);
              const val = parseFloat(parts[0]);
              if (!Number.isNaN(val)) {
                const unit = (parts[1] ?? 'MB').toUpperCase();
                vramGb = unit.includes('MB') ? round2(val / 1024) : round2(val);
              }
            }
          }
          gpus.push(this.makeGpu(name, vramGb, isApple));
        }
      } catch {
        /* ignore */
      }
    }
    if (gpus.length === 0) {
      const raw = (await run(['system_profiler', 'SPDisplaysDataType'])) ?? '';
      if (raw.includes('Apple')) gpus.push(this.makeGpu('Apple Silicon', null, true));
    }
    return gpus;
  }

  private async gpuLinux(): Promise<GpuInfo[]> {
    const gpus: GpuInfo[] = [];
    await this.enrichNvidia(gpus);
    if (gpus.length === 0) {
      const lspci = await run(['lspci']);
      if (lspci) {
        for (const line of lspci.split('\n')) {
          const low = line.toLowerCase();
          if (low.includes('vga') || low.includes('display') || low.includes('3d controller')) {
            const desc = line.includes(':') ? line.split(':').slice(2).join(':').trim() : line;
            gpus.push(this.makeGpu(desc));
          }
        }
      }
    }
    return gpus;
  }

  /** Overlay accurate VRAM, CUDA device index, compute capability, driver via nvidia-smi. */
  private async enrichNvidia(gpus: GpuInfo[]): Promise<void> {
    const smi = await run([
      'nvidia-smi',
      '--query-gpu=index,name,memory.total,compute_cap,driver_version',
      '--format=csv,noheader,nounits',
    ]);
    if (!smi) return;
    const cudaVersion = await this.nvidiaCudaVersion();
    const alreadyEnriched = new Set<number>();
    for (const line of smi.trim().split('\n')) {
      const parts = line.split(', ').map(p => p.trim());
      if (parts.length < 3) continue;
      const cudaIdx = Number.isNaN(parseInt(parts[0], 10)) ? null : parseInt(parts[0], 10);
      const smiName = parts[1];
      const vramVal = parseFloat(parts[2]);
      const vramGb = Number.isNaN(vramVal) ? null : round2(vramVal / 1024);
      const computeCap = parts[3] ?? null;
      const driverVer = parts[4] ?? null;

      let matchIdx = -1;
      for (let i = 0; i < gpus.length; i++) {
        if (!alreadyEnriched.has(i) && gpus[i].vendor === 'NVIDIA' && gpus[i].name.includes(smiName)) {
          matchIdx = i;
          break;
        }
      }
      if (matchIdx !== -1) {
        alreadyEnriched.add(matchIdx);
        Object.assign(gpus[matchIdx], {
          vram_gb: vramGb, cuda_device_index: cudaIdx,
          compute_capability: computeCap, cuda_version: cudaVersion, driver_version: driverVer,
        });
      } else {
        const gpu = this.makeGpu(smiName, vramGb);
        Object.assign(gpu, {
          cuda_device_index: cudaIdx, compute_capability: computeCap,
          cuda_version: cudaVersion, driver_version: driverVer,
        });
        gpus.push(gpu);
      }
    }
  }

  private async nvidiaCudaVersion(): Promise<string | null> {
    const raw = await run(['nvidia-smi']);
    if (raw) {
      const m = raw.match(/CUDA Version:\s*(\d+\.\d+)/);
      if (m) return m[1];
    }
    return null;
  }

  // ── RAM ─────────────────────────────────────────────────────────────────
  // Node's os module gives reliable cross-platform totals, replacing the
  // Python script's psutil → WMI → ctypes ladder.

  private async detectRam(): Promise<HardwareData['ram']> {
    return {
      total_gb: round2(os.totalmem() / GB),
      available_gb: round2(os.freemem() / GB),
    };
  }

  // ── Storage ─────────────────────────────────────────────────────────────

  private async detectStorage(): Promise<HardwareData['storage']> {
    const volumes: Array<Record<string, unknown>> = [];
    const physicalDisks: Array<Record<string, unknown>> = [];
    try {
      if (this.os === 'Windows') {
        let vols = await ps(
          "Get-PSDrive -PSProvider FileSystem | Select-Object Root," +
          "@{N='Free';E={$_.Free}},@{N='Used';E={$_.Used}} | ConvertTo-Json",
        );
        if (vols) {
          if (!Array.isArray(vols)) vols = [vols];
          for (const v of vols) {
            if (typeof v !== 'object' || v == null) continue;
            const free = v.Free || 0;
            const used = v.Used || 0;
            const total = free + used;
            if (total > 0) {
              volumes.push({ path: v.Root ?? '', free_gb: round2(free / GB), total_gb: round2(total / GB) });
            }
          }
        }
        // Separate call — Get-PhysicalDisk can be slow on some systems
        let pdisks = await ps(
          'Get-PhysicalDisk | Select-Object FriendlyName,MediaType,BusType,Size | ConvertTo-Json',
          20000,
        );
        if (pdisks) {
          if (!Array.isArray(pdisks)) pdisks = [pdisks];
          for (const d of pdisks) {
            if (typeof d !== 'object' || d == null) continue;
            const size = d.Size || 0;
            const bus = d.BusType || '';
            const media = d.MediaType || '';
            // BusType is more specific (NVMe, SATA, USB); MediaType = SSD/HDD/Unspecified
            const diskType = ['NVMe', 'USB', 'RAID'].includes(bus) ? bus : (media || 'Unknown');
            physicalDisks.push({ name: d.FriendlyName ?? 'Unknown', type: diskType, size_gb: round2(size / GB) });
          }
        }
      } else if (this.os === 'Darwin') {
        const raw = await run(['system_profiler', 'SPStorageDataType', '-json']);
        if (raw) {
          for (const vol of JSON.parse(raw).SPStorageDataType ?? []) {
            const free = vol.free_space_in_bytes || 0;
            const total = vol.size_in_bytes || 0;
            const medium = vol.physical_drive?.medium_type ?? '';
            volumes.push({
              path: vol.mount_point ?? vol._name ?? '',
              free_gb: round2(free / GB), total_gb: round2(total / GB), type: medium,
            });
          }
        }
      } else {
        const lsblk = await run(['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,ROTA']);
        if (lsblk) {
          for (const dev of JSON.parse(lsblk).blockdevices ?? []) {
            if (dev.type === 'disk') {
              physicalDisks.push({
                name: dev.name ?? '',
                type: String(dev.rota ?? '1') === '1' ? 'HDD' : 'SSD/NVMe',
                size_gb: 0,
              });
            }
          }
        }
        const df = await run(['df', '-BG', '--output=target,avail,size']);
        if (df) {
          for (const line of df.split('\n').slice(1)) {
            const parts = line.split(/\s+/);
            if (parts.length >= 3 && parts[0].startsWith('/')) {
              const free = parseFloat(parts[1].replace(/G$/, ''));
              const total = parseFloat(parts[2].replace(/G$/, ''));
              if (!Number.isNaN(free) && !Number.isNaN(total)) {
                volumes.push({ path: parts[0], free_gb: free, total_gb: total });
              }
            }
          }
        }
      }
    } catch {
      /* ignore */
    }

    // Stdlib fallback for home drive if nothing detected
    if (volumes.length === 0) {
      try {
        const stat = (fs as unknown as { statfsSync?: (p: string) => { bsize: number; blocks: number; bfree: number } }).statfsSync;
        if (stat) {
          const u = stat(os.homedir());
          volumes.push({
            path: path.parse(os.homedir()).root,
            free_gb: round2((u.bsize * u.bfree) / GB),
            total_gb: round2((u.bsize * u.blocks) / GB),
          });
        }
      } catch {
        /* ignore */
      }
    }

    return { volumes, physical_disks: physicalDisks };
  }

  // ── Displays ────────────────────────────────────────────────────────────

  private async detectDisplays(): Promise<Array<Record<string, unknown>>> {
    const displays: Array<Record<string, unknown>> = [];
    try {
      if (this.os === 'Windows') {
        let result = await ps(
          'Add-Type -AssemblyName System.Windows.Forms; ' +
          '[System.Windows.Forms.Screen]::AllScreens | ' +
          "Select-Object @{N='Width';E={$_.Bounds.Width}}," +
          "@{N='Height';E={$_.Bounds.Height}},Primary | ConvertTo-Json",
        );
        if (result) {
          if (!Array.isArray(result)) result = [result];
          for (const d of result) {
            displays.push({ width: d.Width, height: d.Height, primary: Boolean(d.Primary) });
          }
        }
      } else if (this.os === 'Darwin') {
        const raw = await run(['system_profiler', 'SPDisplaysDataType', '-json']);
        if (raw) {
          for (const entry of JSON.parse(raw).SPDisplaysDataType ?? []) {
            for (const d of entry.spdisplays_ndrvs ?? []) {
              const res: string = d._spdisplays_resolution ?? '';
              const m = res.match(/(\d+)\s*x\s*(\d+)/);
              if (m) displays.push({ width: parseInt(m[1], 10), height: parseInt(m[2], 10), name: d._name ?? '' });
            }
          }
        }
      } else {
        const xrandr = await run(['xrandr', '--query']);
        if (xrandr) {
          for (const line of xrandr.split('\n')) {
            const m = line.match(/(\d+)x(\d+)\+\d+\+\d+/);
            if (m) displays.push({ width: parseInt(m[1], 10), height: parseInt(m[2], 10) });
          }
        }
      }
    } catch {
      /* ignore */
    }
    return displays;
  }

  // ── Motherboard ─────────────────────────────────────────────────────────

  private async detectMotherboard(): Promise<Record<string, unknown>> {
    const info: Record<string, unknown> = {};
    try {
      if (this.os === 'Windows') {
        const result = await ps(
          '@{' +
          'CS=(Get-CimInstance Win32_ComputerSystem|Select-Object Manufacturer,Model);' +
          'BB=(Get-CimInstance Win32_BaseBoard|Select-Object Manufacturer,Product,Version);' +
          'BIOS=(Get-CimInstance Win32_BIOS|Select-Object SMBIOSBIOSVersion,Manufacturer)' +
          '} | ConvertTo-Json -Depth 3',
        );
        if (result) {
          const cs = result.CS || {};
          const bb = result.BB || {};
          const bios = result.BIOS || {};
          info.manufacturer = cs.Manufacturer;
          info.model = cs.Model;
          info.board_manufacturer = bb.Manufacturer;
          info.board_model = bb.Product;
          info.board_version = bb.Version;
          info.bios_version = bios.SMBIOSBIOSVersion;
          info.bios_vendor = bios.Manufacturer;
        }
      } else if (this.os === 'Darwin') {
        const raw = await run(['system_profiler', 'SPHardwareDataType', '-json']);
        if (raw) {
          const hw = (JSON.parse(raw).SPHardwareDataType ?? [{}])[0];
          info.manufacturer = 'Apple';
          info.model = hw.machine_model;
          info.serial = hw.serial_number;
          info.bios_version = hw.boot_rom_version;
        }
      } else {
        const dmi = '/sys/class/dmi/id';
        if (fs.existsSync(dmi)) {
          const r = (name: string): string | null => {
            try {
              return fs.readFileSync(path.join(dmi, name), 'utf8').trim();
            } catch {
              return null;
            }
          };
          info.manufacturer = r('sys_vendor');
          info.model = r('product_name');
          info.board_manufacturer = r('board_vendor');
          info.board_model = r('board_name');
          info.bios_version = r('bios_version');
          info.bios_vendor = r('bios_vendor');
        }
      }
    } catch {
      /* ignore */
    }
    return info;
  }

  // ── Inference Runtimes ──────────────────────────────────────────────────

  private async checkRuntimes(): Promise<{ ollama: boolean; lmstudio: boolean }> {
    return { ollama: await this.checkOllama(), lmstudio: await this.checkLmStudio() };
  }

  private async checkOllama(): Promise<boolean> {
    return (await run(['ollama', 'list'], 10000)) != null;
  }

  private async checkLmStudio(): Promise<boolean> {
    const home = os.homedir();
    let paths: string[];
    if (this.os === 'Windows') {
      paths = [
        path.join(home, '.lmstudio'),
        path.join(home, 'AppData', 'Local', 'LM Studio'),
        path.join(home, 'AppData', 'Local', 'Programs', 'LM Studio'),
      ];
    } else if (this.os === 'Darwin') {
      paths = [
        '/Applications/LM Studio.app',
        path.join(home, 'Applications', 'LM Studio.app'),
        path.join(home, '.lmstudio'),
      ];
    } else {
      paths = [path.join(home, '.lmstudio'), path.join(home, '.local', 'share', 'lmstudio')];
      if (await run(['which', 'lms'])) return true;
    }
    return paths.some(p => fs.existsSync(p));
  }

  // ── Network ─────────────────────────────────────────────────────────────

  private async detectNetwork(): Promise<Array<Record<string, unknown>>> {
    const adapters: Array<Record<string, unknown>> = [];
    try {
      if (this.os === 'Windows') {
        let result = await ps(
          'Get-NetAdapter | Select-Object Name,InterfaceDescription,' +
          'MacAddress,LinkSpeed,MediaType,PhysicalMediaType,Status | ConvertTo-Json',
        );
        if (result) {
          if (!Array.isArray(result)) result = [result];
          for (const a of result) {
            adapters.push({
              name: a.Name, description: a.InterfaceDescription, mac: a.MacAddress,
              speed: a.LinkSpeed, media_type: a.PhysicalMediaType, status: a.Status,
            });
          }
        }
      } else if (this.os === 'Darwin') {
        const raw = await run(['system_profiler', 'SPNetworkDataType', '-json']);
        if (raw) {
          for (const iface of JSON.parse(raw).SPNetworkDataType ?? []) {
            adapters.push({
              name: iface._name, description: iface.type,
              mac: iface.Ethernet?.['MAC Address'],
              status: iface.IPv4 || iface.IPv6 ? 'active' : 'inactive',
            });
          }
        }
      } else {
        const net = '/sys/class/net';
        if (fs.existsSync(net)) {
          for (const iface of fs.readdirSync(net)) {
            try {
              const mac = fs.readFileSync(path.join(net, iface, 'address'), 'utf8').trim();
              const operstate = fs.readFileSync(path.join(net, iface, 'operstate'), 'utf8').trim();
              let speed: number | null = null;
              const speedPath = path.join(net, iface, 'speed');
              if (fs.existsSync(speedPath)) {
                const s = parseInt(fs.readFileSync(speedPath, 'utf8').trim(), 10);
                if (!Number.isNaN(s)) speed = s;
              }
              adapters.push({ name: iface, mac, status: operstate, speed_mbps: speed });
            } catch {
              /* ignore */
            }
          }
        }
      }
    } catch {
      /* ignore */
    }
    return adapters;
  }

  // ── Audio ───────────────────────────────────────────────────────────────

  private async detectAudio(): Promise<Array<Record<string, unknown>>> {
    const devices: Array<Record<string, unknown>> = [];
    try {
      if (this.os === 'Windows') {
        let result = await ps(
          'Get-CimInstance Win32_SoundDevice | Select-Object Name,Manufacturer,Status | ConvertTo-Json',
        );
        if (result) {
          if (!Array.isArray(result)) result = [result];
          for (const d of result) devices.push({ name: d.Name, manufacturer: d.Manufacturer, status: d.Status });
        }
      } else if (this.os === 'Darwin') {
        const raw = await run(['system_profiler', 'SPAudioDataType', '-json']);
        if (raw) {
          for (const entry of JSON.parse(raw).SPAudioDataType ?? []) {
            for (const item of entry._items ?? []) devices.push({ name: item._name });
          }
        }
      } else {
        const cards = await run(['aplay', '-l']);
        if (cards) {
          for (const line of cards.split('\n')) {
            if (line.startsWith('card ')) devices.push({ name: line.trim() });
          }
        }
      }
    } catch {
      /* ignore */
    }
    return devices;
  }

  // ── Battery ─────────────────────────────────────────────────────────────

  private static readonly BATTERY_STATUS: Record<number, string> = {
    1: 'Discharging', 2: 'AC (plugged in)', 3: 'Fully charged',
    4: 'Low', 5: 'Critical', 6: 'Charging', 7: 'Charging (high)',
    8: 'Charging (low)', 9: 'Charging (critical)', 10: 'Unknown',
    11: 'Partially charged',
  };

  private async detectBattery(): Promise<Record<string, unknown> | null> {
    try {
      if (this.os === 'Windows') {
        const result = await ps(
          'Get-CimInstance Win32_Battery | ' +
          'Select-Object Name,EstimatedChargeRemaining,BatteryStatus,' +
          'DesignCapacity,FullChargeCapacity | ConvertTo-Json',
        );
        if (result) {
          const data = Array.isArray(result) ? result[0] : result;
          return {
            name: data.Name,
            charge_pct: data.EstimatedChargeRemaining,
            status: HardwareDetector.BATTERY_STATUS[data.BatteryStatus] ?? 'Unknown',
            design_capacity_mwh: data.DesignCapacity,
            full_capacity_mwh: data.FullChargeCapacity,
          };
        }
      } else if (this.os === 'Darwin') {
        const raw = await run(['system_profiler', 'SPPowerDataType', '-json']);
        if (raw) {
          const power = (JSON.parse(raw).SPPowerDataType ?? [{}])[0];
          const batt = power.sppower_battery_model_info ?? {};
          const state = power.sppower_battery_charge_info ?? {};
          if (Object.keys(batt).length || Object.keys(state).length) {
            return {
              name: batt.sppower_battery_model_name,
              charge_pct: state.sppower_battery_state_of_charge,
              status: state.sppower_battery_full_charge_capacity,
              cycle_count: batt.sppower_battery_cycle_count,
            };
          }
        }
      } else {
        const base = '/sys/class/power_supply';
        if (fs.existsSync(base)) {
          for (const bat of fs.readdirSync(base).filter(n => n.startsWith('BAT'))) {
            try {
              const bval = (name: string): string | null => {
                const p = path.join(base, bat, name);
                return fs.existsSync(p) ? fs.readFileSync(p, 'utf8').trim() : null;
              };
              const cap = bval('capacity');
              return {
                name: bat,
                charge_pct: cap ? parseInt(cap, 10) : null,
                status: bval('status'),
                energy_now_uwh: bval('energy_now'),
                energy_full_uwh: bval('energy_full'),
              };
            } catch {
              /* ignore */
            }
          }
        }
      }
    } catch {
      /* ignore */
    }
    return null;
  }

  // ── All Devices (Device Manager equivalent) ─────────────────────────────

  private async detectAllDevices(): Promise<Record<string, unknown>> {
    try {
      if (this.os === 'Windows') return await this.allDevicesWindows();
      if (this.os === 'Darwin') return await this.allDevicesMacos();
      return await this.allDevicesLinux();
    } catch {
      return {};
    }
  }

  private async allDevicesWindows(): Promise<Record<string, unknown>> {
    let result = await ps(
      'Get-PnpDevice -Status OK | ' +
      'Select-Object Class,FriendlyName,Manufacturer,InstanceId | ConvertTo-Json -Depth 2',
      30000,
    );
    if (!result) return {};
    if (!Array.isArray(result)) result = [result];
    const grouped: Record<string, Array<Record<string, unknown>>> = {};
    for (const dev of result) {
      const cls = dev.Class || 'Unknown';
      const entry: Record<string, unknown> = {};
      for (const k of ['FriendlyName', 'Manufacturer', 'InstanceId']) {
        if (dev[k]) entry[k] = dev[k];
      }
      (grouped[cls] ??= []).push(entry);
    }
    return Object.fromEntries(Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)));
  }

  private async allDevicesMacos(): Promise<Record<string, unknown>> {
    const types = [
      'SPHardwareDataType', 'SPNetworkDataType', 'SPAudioDataType',
      'SPStorageDataType', 'SPUSBDataType', 'SPBluetoothDataType',
      'SPPCIDataType', 'SPPowerDataType', 'SPCameraDataType',
    ];
    const result: Record<string, unknown> = {};
    for (const spType of types) {
      const raw = await run(['system_profiler', spType, '-json'], 10000);
      if (raw) {
        try {
          result[spType] = JSON.parse(raw)[spType] ?? [];
        } catch {
          /* ignore */
        }
      }
    }
    return result;
  }

  private async allDevicesLinux(): Promise<Record<string, unknown>> {
    const raw = await run(['lshw', '-json', '-quiet'], 30000);
    if (raw) {
      try {
        return { lshw: JSON.parse(raw) };
      } catch {
        /* ignore */
      }
    }
    const result: Record<string, unknown> = {};
    const lspci = await run(['lspci', '-vmm']);
    if (lspci) result.pci = lspci.trim();
    const lsusb = await run(['lsusb']);
    if (lsusb) result.usb = lsusb.split('\n').map(l => l.trim()).filter(Boolean);
    return result;
  }

  // ── Formatters ──────────────────────────────────────────────────────────

  private fmtLlm(data: HardwareData): LlmHardware {
    const cpu = data.cpu;
    const ram = data.ram;
    const gpuData = data.gpu;
    const plat = data.platform;
    const runtimes = data.inference_runtimes;

    const gpusOut: Array<Record<string, unknown>> = [];
    for (const g of gpuData.all) {
      const entry: Record<string, unknown> = {
        name: g.name, vendor: g.vendor, role: g.role, vram_gb: g.vram_gb,
      };
      if (g.cuda_device_index != null) entry.cuda_device = g.cuda_device_index;
      if (g.compute_capability) entry.compute_sm = g.compute_capability;
      if (g.cuda_version) entry.cuda_ver = g.cuda_version;
      if (g.unified_memory) entry.unified_memory = true;
      gpusOut.push(entry);
    }

    const avx = (['avx2', 'avx512'] as const).filter(k => cpu[k]);

    const vols = data.storage.volumes
      .filter(v => Number(v.total_gb || 0) > 1)
      .map(v => ({ path: v.path as string, free_gb: v.free_gb as number, total_gb: v.total_gb as number }));

    const netOut: Array<Record<string, unknown>> = [];
    for (const a of data.network) {
      const st = String(a.status ?? '').toLowerCase();
      if (['up', 'active', 'connected', 'linkup'].includes(st)) {
        netOut.push({ name: a.description || a.name, media: a.media_type || a.speed });
      }
    }

    const battery = data.battery;
    const batteryOut = battery ? { charge_pct: battery.charge_pct, status: battery.status } : null;

    const cpuOut: LlmHardware['cpu'] = { name: cpu.name, threads: cpu.threads, avx };
    if (cpu.cores) cpuOut.cores = cpu.cores;

    const out: LlmHardware = {
      platform: `${plat.os} ${plat.machine}`,
      cpu: cpuOut,
      ram_gb: ram.total_gb,
      ram_free_gb: ram.available_gb,
      gpus: gpusOut,
      storage: vols,
      runtimes: Object.entries(runtimes).filter(([, v]) => v).map(([k]) => k),
    };
    if (netOut.length) out.network = netOut;
    if (batteryOut) out.battery = batteryOut;
    return out;
  }

  private fmtStandard(data: HardwareData): string {
    const W = 60;
    const sep = '─'.repeat(W);
    const lines: string[] = [];
    const row = (label: string, value: string) => lines.push(`  ${label.padEnd(10)}${value}`);

    const ts = (data.detected_at ?? '').slice(0, 16).replace('T', ' ');
    lines.push(sep, `  Hardware Report — ${ts}`, sep);

    const plat = data.platform;
    row('OS', `${plat.os} ${plat.os_release ?? ''}  (${plat.machine})`);
    row('Node', String(plat.node_version ?? ''));
    lines.push('');

    const cpu = data.cpu;
    const avx = (['avx2', 'avx512'] as const).filter(k => cpu[k]).map(k => k.toUpperCase().replace('AVX', 'AVX-')).join(' + ');
    row('CPU', cpu.name || 'Unknown');
    const cpuTopology = cpu.cores ? `${cpu.cores} cores / ${cpu.threads} threads` : `${cpu.threads} logical threads`;
    row('', cpuTopology + (avx ? `  ·  ${avx}` : ''));

    const ram = data.ram;
    row('RAM', `${ram.total_gb} GB total  /  ${ram.available_gb} GB available`);
    lines.push('');

    const gpuData = data.gpu;
    const primaryName = gpuData.primary?.name;
    gpuData.all.forEach((g, i) => {
      const marker = g.name === primaryName ? '►' : ' ';
      const vram = g.vram_gb ? `${g.vram_gb} GB` : 'shared';
      const extras: string[] = [];
      if (g.cuda_device_index != null) extras.push(`CUDA device ${g.cuda_device_index}`);
      if (g.compute_capability) extras.push(`SM ${g.compute_capability}`);
      if (g.cuda_version) extras.push(`CUDA ${g.cuda_version}`);
      const extraStr = extras.length ? '  ·  ' + extras.join('  ·  ') : '';
      lines.push(`  ${marker} GPU[${i}]  ${g.name}`);
      lines.push(`           ${vram} VRAM  ·  ${g.role}${extraStr}`);
      if (g.driver_version) lines.push(`           Driver ${g.driver_version}`);
    });
    lines.push('');

    for (const v of data.storage.volumes) {
      row('Storage', `${v.path}  ${v.free_gb} GB free / ${v.total_gb} GB` + (v.type ? `  (${v.type})` : ''));
    }
    for (const d of data.storage.physical_disks) {
      row('', `${d.name}  ·  ${d.type}  ·  ${d.size_gb} GB`);
    }
    lines.push('');

    if (data.displays.length) {
      const dispStr = data.displays
        .map(d => `${d.width}×${d.height}` + (d.primary ? ' (primary)' : ''))
        .join('  |  ');
      row('Display', dispStr);
    }

    const board = data.motherboard;
    if (Object.keys(board).length) {
      const sysStr = [board.manufacturer, board.model].filter(Boolean).join(' ');
      const biosStr = board.bios_version ? `  ·  BIOS ${board.bios_version}` : '';
      if (sysStr) row('Board', sysStr + biosStr);
    }

    const netActive = data.network.filter(a =>
      ['up', 'active', 'connected', 'linkup'].includes(String(a.status ?? '').toLowerCase()));
    for (const a of netActive) {
      const label = a.description || a.name || '';
      const speed = a.speed ? `  ·  ${a.speed}` : '';
      row('Network', `${label}${speed}`);
    }

    if (data.audio.length) {
      row('Audio', data.audio.map(a => a.name ?? '').filter(Boolean).join('  |  '));
    }

    const battery = data.battery;
    if (battery) {
      const pct = battery.charge_pct;
      const status = battery.status ?? '';
      const name = battery.name ?? 'Battery';
      row('Battery', pct != null ? `${name}  ·  ${pct}%  ·  ${status}` : String(status));
    }

    const runtimes = data.inference_runtimes;
    const rtStr = Object.entries(runtimes)
      .map(([k, v]) => `${k[0].toUpperCase()}${k.slice(1)} ${v ? '✓' : '✗'}`)
      .join('  |  ');
    row('Runtimes', rtStr);

    const allDev = data.all_devices;
    if (Object.keys(allDev).length && this.os === 'Windows') {
      const counts = Object.entries(allDev)
        .filter(([, devs]) => Array.isArray(devs) && devs.length)
        .map(([cls, devs]) => `${cls}:${(devs as unknown[]).length}`);
      if (counts.length) {
        lines.push('');
        lines.push(`  Device classes (OK):  ${counts.sort().join('  ')}`);
      }
    }

    lines.push(sep);
    return lines.join('\n');
  }

  // ── Persistence ─────────────────────────────────────────────────────────

  async saveToSettings(hardware?: HardwareData): Promise<string> {
    const hw = hardware ?? (await this.detect());
    let settings: Record<string, unknown> = {};
    if (fs.existsSync(this.settingsPath)) {
      try {
        settings = JSON.parse(fs.readFileSync(this.settingsPath, 'utf8'));
      } catch {
        /* ignore */
      }
    }
    settings.hardware = hw;
    fs.mkdirSync(path.dirname(this.settingsPath), { recursive: true });
    fs.writeFileSync(this.settingsPath, JSON.stringify(settings, null, 2));
    return this.settingsPath;
  }

  loadFromSettings(): HardwareData | null {
    if (fs.existsSync(this.settingsPath)) {
      try {
        return JSON.parse(fs.readFileSync(this.settingsPath, 'utf8')).hardware ?? null;
      } catch {
        /* ignore */
      }
    }
    return null;
  }
}

export async function detectAndSaveHardware(settingsPath?: string): Promise<HardwareData> {
  const detector = new HardwareDetector(settingsPath);
  const hardware = await detector.detect();
  await detector.saveToSettings(hardware);
  return hardware;
}

// ── CLI entry (tsx apps/.../hardwareDetector.ts --mode llm [--save]) ──────────

const isCliRun = (() => {
  try {
    const invoked = process.argv[1] ? path.resolve(process.argv[1]) : '';
    return invoked.endsWith('hardwareDetector.ts') || invoked.endsWith('hardwareDetector.js');
  } catch {
    return false;
  }
})();

if (isCliRun) {
  void (async () => {
    const argv = process.argv.slice(2);
    const modeIdx = argv.indexOf('--mode');
    const mode = (modeIdx !== -1 ? argv[modeIdx + 1] : 'standard') as 'verbose' | 'standard' | 'llm';
    const save = argv.includes('--save');

    const detector = new HardwareDetector();
    const data = await detector.detect();
    if (save) await detector.saveToSettings(data);

    const result = detector.format(data, mode as 'standard');
    process.stdout.write((typeof result === 'string' ? result : JSON.stringify(result, null, 2)) + '\n');
  })();
}
