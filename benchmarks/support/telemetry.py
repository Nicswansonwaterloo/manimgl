"""Best-effort process and device-wide GPU counters; no privileged monitoring."""
import csv
import plistlib
import shutil
import subprocess
import sys
import time

import psutil


def apple_gpu_samples():
    """Best-effort device-wide counters; IORegistry fields are driver-dependent."""
    reply = subprocess.run(["ioreg", "-r", "-d", "1", "-c", "IOAccelerator", "-a"],
                           capture_output=True, check=True, timeout=2)
    samples = []
    for index, item in enumerate(plistlib.loads(reply.stdout)):
        utilization = item.get("PerformanceStatistics", {}).get("Device Utilization %")
        if isinstance(utilization, (int, float)) and not isinstance(utilization, bool) and 0 <= utilization <= 100:
            samples.append({"id": f"ioreg:{item.get('IORegistryEntryID', index)}",
                            "name": item.get("IOClass", "Apple GPU"), "utilization": float(utilization)})
    return samples


def monitor_resources(pid, stop, readings, notes):
    """Sample in a thread so telemetry does not delay process-exit timing."""
    try:
        root = psutil.Process(pid)
    except (psutil.Error, OSError) as error:
        notes.add(f"Process counters unavailable: {error}")
        return
    nvidia = shutil.which("nvidia-smi")
    apple = sys.platform == "darwin" and shutil.which("ioreg")
    next_gpu = 0
    while not stop.is_set():
        try:
            processes = [root, *root.children(recursive=True)]
            readings["rss"].append(sum(p.memory_info().rss for p in processes if p.is_running()))
        except psutil.NoSuchProcess:
            pass
        except (psutil.AccessDenied, OSError) as error:
            notes.add(f"Process-tree RSS unavailable: {error}")
        if (nvidia or apple) and time.monotonic() >= next_gpu:
            try:
                if nvidia:
                    reply = subprocess.run([nvidia, "--query-gpu=uuid,name,utilization.gpu,memory.used",
                                            "--format=csv,noheader,nounits"],
                                           capture_output=True, text=True, check=True, timeout=2)
                    for row in csv.reader(reply.stdout.splitlines()):
                        uuid, name, utilization, memory = [field.strip() for field in row]
                        values = readings["gpu"].setdefault(uuid, {"name": name, "provider": "nvidia-smi", "utilization": [], "memory": []})
                        if utilization.replace(".", "", 1).isdigit():
                            values["utilization"].append(float(utilization))
                        if memory.replace(".", "", 1).isdigit():
                            values["memory"].append(float(memory))
                else:
                    samples = apple_gpu_samples()
                    if not samples:
                        notes.add("Apple GPU utilization unavailable: IORegistry has no usable counters")
                    for sample in samples:
                        values = readings["gpu"].setdefault(sample["id"], {"name": sample["name"], "provider": "apple-ioreg", "utilization": [], "memory": []})
                        values["utilization"].append(sample["utilization"])
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                notes.add(f"GPU counters unavailable: {error}")
            next_gpu = time.monotonic() + 1
        stop.wait(0.1)
