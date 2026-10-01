"""Read capacity without confusing an APFS volume with its shared container."""
import datetime as dt
import math
import plistlib
import subprocess
from xml.parsers.expat import ExpatError
from pathlib import Path


def _integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Invalid {label}: expected a nonnegative integer")
    return value


def _metrics(total, free, target_percent, source, warnings):
    total = _integer(total, "total capacity")
    free = _integer(free, "free capacity")
    if total == 0 or free > total:
        raise ValueError("Invalid disk capacity: total must be positive and free <= total")
    used = total - free
    target = math.floor(total * target_percent / 100)
    return {
        "total_bytes": total, "free_bytes": free, "used_bytes": used,
        "used_percent": used * 100 / total, "target_percent": target_percent,
        "target_used_bytes": target, "reclaim_needed_bytes": max(0, used - target),
        "source": source, "warnings": warnings,
        "measured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def measure(volume: Path, target_percent: float = 50) -> dict:
    """Prefer APFS container capacity; fall back explicitly to df volume accounting."""
    if not isinstance(target_percent, (int, float)) or isinstance(target_percent, bool):
        raise ValueError("Target percentage must be a number")
    if not math.isfinite(target_percent) or not 0 < target_percent <= 100:
        raise ValueError("Target percentage must be greater than 0 and at most 100")
    warnings = []
    try:
        result = subprocess.run(
            ["diskutil", "info", "-plist", str(volume)], check=True,
            capture_output=True, timeout=15,
        )
        info = plistlib.loads(result.stdout)
        if not isinstance(info, dict):
            raise ValueError("diskutil returned a non-dictionary plist")
        if "APFSContainerSize" in info and "APFSContainerFree" in info:
            # Invalid reported metrics fail; quietly switching sources would hide corruption.
            return _metrics(info["APFSContainerSize"], info["APFSContainerFree"],
                            target_percent, "diskutil APFS container", warnings)
        warnings.append("APFS container capacity was unavailable from diskutil.")
    except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException, ExpatError) as exc:
        warnings.append(f"diskutil capacity lookup failed ({type(exc).__name__}).")
    except ValueError as exc:
        if "Invalid disk capacity" in str(exc) or "Invalid total" in str(exc) or "Invalid free" in str(exc):
            raise
        warnings.append(f"diskutil capacity lookup failed ({type(exc).__name__}).")
    try:
        result = subprocess.run(
            ["df", "-kP", str(volume)], check=True, capture_output=True, timeout=15,
        )
        rows = result.stdout.decode("utf-8", errors="replace").strip().splitlines()
        fields = rows[-1].split()
        if len(rows) < 2 or len(fields) < 6:
            raise ValueError("df did not return a usable capacity row")
        total, used, free = (int(fields[i]) * 1024 for i in (1, 2, 3))
        _integer(used, "df used capacity")
        if used > total:
            raise ValueError("Invalid df used capacity")
        warnings.append("Fallback is volume-only df accounting; shared APFS container usage may differ.")
        # df's independently reported used/free values can differ slightly; the target
        # requires one internally consistent total-minus-available calculation.
        return _metrics(total, free, target_percent, "df volume-only (total minus available)", warnings)
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as exc:
        raise RuntimeError(f"Could not measure disk capacity for {volume}: {exc}") from exc
