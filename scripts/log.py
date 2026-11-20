#!/usr/bin/env python3
"""Add, edit, delete and list gym log entries, and save photos to the repo.

Every entry lives in data/log.json. Photos are shrunk to 1280px and stripped of all
metadata (including GPS location) before they are written into _photos/. Photos are kept
in the repo only: the site never shows them, and the deploy deletes _photos/ before publishing.

Examples (run from the repo root):
  python3 scripts/log.py uploads
  python3 scripts/log.py add set --photo latest --data '{"exercise":"Lat pulldown","weight":45,"reps":10}'
  python3 scripts/log.py add set --repeat 3 --data '{"exercise":"Push-up","weight":null,"reps":12}'
  python3 scripts/log.py add bodyweight --photo latest --data '{"weight":82.4}'
  python3 scripts/log.py add food --photo latest --confidence low \
      --data '{"meal":"lunch","description":"Chicken, rice, broccoli","kcal":650,"protein_g":45,"carbs_g":70,"fat_g":15}'
  python3 scripts/log.py add cardio --photo latest --data '{"machine":"Treadmill","minutes":20,"distance_km":3.1,"kcal":210}'
  python3 scripts/log.py add note --data '{"text":"Left shoulder a bit sore"}'
  python3 scripts/log.py add note --data '{"text":"Gym: lower day","session":"Legs"}'
  python3 scripts/log.py add steps --data '{"steps":10450}'
  python3 scripts/log.py add water --data '{"litres":0.75}'
  python3 scripts/log.py edit last --data '{"weight":50}'
  python3 scripts/log.py delete last
  python3 scripts/log.py today
  python3 scripts/log.py ref --photo latest --name lat-pulldown
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "log.json"
CONFIG = ROOT / "config.json"
# Photos sent from the Claude app land in /root/.claude/uploads/<session-id>/.
UPLOAD_DIRS = [Path(d) for d in os.environ.get("GYMLOG_UPLOADS", "/root/.claude/uploads:/mnt/user-data/uploads").split(":")]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".avif", ".gif", ".tif", ".tiff"}
MAX_SIDE = 1280
QUALITY = 78

TYPES = {
    "set": {"required": ["exercise"], "numbers": ["weight", "reps"]},
    "bodyweight": {"required": ["weight"], "numbers": ["weight"]},
    "food": {"required": ["description"], "numbers": ["kcal", "protein_g", "carbs_g", "fat_g", "sugar_g"]},
    "cardio": {"required": ["machine"], "numbers": ["minutes", "distance_km", "kcal"]},
    "note": {"required": ["text"], "numbers": []},
    "steps": {"required": ["steps"], "numbers": ["steps"]},
    "water": {"required": ["litres"], "numbers": ["litres"]},
}
PHOTO_DIR = "_photos"
CORE_KEYS = {"id", "time", "type", "photo", "src_hash", "confidence", "notes"}


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def config():
    try:
        return json.loads(CONFIG.read_text())
    except FileNotFoundError:
        return {}


def tz():
    return ZoneInfo(config().get("timezone", "UTC"))


def default_unit():
    return config().get("unit", "kg")


def load_log():
    if not LOG.exists():
        return []
    text = LOG.read_text().strip()
    return json.loads(text) if text else []


def save_log(entries):
    entries.sort(key=lambda e: datetime.fromisoformat(e["time"]))
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    text = "[\n" + body + ("\n" if body else "") + "]\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=LOG.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, LOG)


def parse_time(value):
    """None -> now; 'HH:MM' -> today at that time; otherwise ISO date-time (local tz if no offset)."""
    zone = tz()
    if not value:
        return datetime.now(zone).replace(microsecond=0)
    value = value.strip()
    if len(value) <= 5 and ":" in value:
        hh, mm = value.split(":")
        return datetime.now(zone).replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    dt = datetime.fromisoformat(value.replace(" ", "T"))
    return dt.replace(tzinfo=zone) if dt.tzinfo is None else dt.astimezone(zone)


def local_day(entry):
    return datetime.fromisoformat(entry["time"]).astimezone(tz()).date()


def upload_files():
    files = [p for d in UPLOAD_DIRS if d.is_dir() for p in d.rglob("*")
             if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def resolve_photo(arg):
    if arg == "latest":
        files = upload_files()
        if not files:
            die(f"no images found in {", ".join(map(str, UPLOAD_DIRS))}; pass the photo path explicitly")
        return files[0]
    p = Path(arg).expanduser()
    if not p.is_file():
        die(f"photo not found: {p}")
    return p


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def process_photo(src, dest):
    """Write a resized, metadata-free JPEG of src to dest. Returns size in bytes."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    im_bin = shutil.which("magick") or shutil.which("convert")
    ok = False
    if im_bin:
        cmd = [im_bin, f"{src}[0]", "-auto-orient", "-resize", f"{MAX_SIDE}x{MAX_SIDE}>",
               "-strip", "-sampling-factor", "4:2:0", "-interlace", "JPEG",
               "-quality", str(QUALITY), str(dest)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0 and dest.exists()
    if not ok:
        from PIL import Image, ImageOps
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            im.thumbnail((MAX_SIDE, MAX_SIDE))
            im.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    # Belt and braces: confirm nothing identifying survived.
    from PIL import Image
    with Image.open(dest) as im:
        leftover = len(im.getexif()) or ("exif" in im.info) or ("xmp" in im.info) or ("comment" in im.info)
        if leftover:
            clean = Image.new(im.mode, im.size)
            clean.paste(im)
            clean.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return dest.stat().st_size


def fmt_num(v):
    if v is None:
        return "?"
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def summary(e):
    t = e["type"]
    if t == "set":
        w = "bodyweight" if e.get("weight") is None else f"{fmt_num(e['weight'])} {e.get('unit', default_unit())}"
        reps = ""
        if e.get("reps") is not None:
            reps = f" x {'~' if e.get('reps_assumed') else ''}{fmt_num(e['reps'])}"
        return f"{e['exercise']} - {w}{reps}"
    if t == "bodyweight":
        return f"Body weight {fmt_num(e['weight'])} {e.get('unit', default_unit())}"
    if t == "food":
        macros = " ".join(f"{k[0].upper()}{fmt_num(e[k + '_g'])}" for k in ("protein", "carbs", "fat") if e.get(k + "_g") is not None)
        meal = f"{e['meal']}: " if e.get("meal") else ""
        kcal = f" ~{fmt_num(e['kcal'])} kcal" if e.get("kcal") is not None else ""
        return f"{meal}{e['description']}{kcal}{' (' + macros + ')' if macros else ''}"
    if t == "cardio":
        bits = [e["machine"]]
        for k, unit in (("minutes", "min"), ("distance_km", "km"), ("kcal", "kcal")):
            if e.get(k) is not None:
                bits.append(f"{fmt_num(e[k])} {unit}")
        return " ".join(bits)
    if t == "steps":
        return f"{fmt_num(e['steps'])} steps"
    if t == "water":
        return f"Water {fmt_num(e['litres'])} L"
    return e.get("text", "")


def set_number(entries, entry):
    day, name = local_day(entry), entry["exercise"].strip().casefold()
    same = [e for e in entries if e["type"] == "set" and local_day(e) == day and e["exercise"].strip().casefold() == name]
    same.sort(key=lambda e: datetime.fromisoformat(e["time"]))
    return same.index(entry) + 1


def line(entries, e):
    t = datetime.fromisoformat(e["time"]).astimezone(tz())
    extra = ""
    if e["type"] == "set":
        extra = f" (set {set_number(entries, e)})"
    flags = []
    if e.get("confidence") == "low":
        flags.append("low confidence")
    if e.get("photo"):
        flags.append("photo")
    flag_txt = f" [{', '.join(flags)}]" if flags else ""
    return f"{e['id']}  {t:%a %d %b %H:%M}  {e['type']:<10} {summary(e)}{extra}{flag_txt}"


def validate(etype, data):
    spec = TYPES[etype]
    for k in spec["required"]:
        if data.get(k) in ("", None):
            die(f"'{etype}' entries need '{k}'")
    for k in spec["numbers"]:
        if k in data and data[k] is not None and not isinstance(data[k], (int, float)):
            die(f"'{k}' must be a number (or null), got {data[k]!r}")
    clash = CORE_KEYS & set(data)
    if clash:
        die(f"use the command-line flags for {sorted(clash)}, not --data")


def new_id(entries, dt, etype):
    base = f"{dt:%Y%m%d-%H%M%S}-{etype}"
    taken = {e["id"] for e in entries}
    cand, n = base, 2
    while cand in taken:
        cand, n = f"{base}-{n}", n + 1
    return cand


def attach_photo(entry, src, entries):
    h = file_hash(src)
    dup = next((e for e in entries if e.get("src_hash") == h and e is not entry), None)
    if dup:
        print(f"warning: this exact photo is already attached to {dup['id']} ({summary(dup)})", file=sys.stderr)
    dt = datetime.fromisoformat(entry["time"]).astimezone(tz())
    rel = Path(PHOTO_DIR) / f"{dt:%Y}" / f"{dt:%m}" / f"{dt:%d}" / f"{entry['id'].split('-', 1)[1]}.jpg"
    size = process_photo(src, ROOT / rel)
    entry["photo"] = rel.as_posix()
    entry["src_hash"] = h
    return size


def find(entries, ident):
    if not entries:
        die("the log is empty")
    if ident == "last":
        return max(entries, key=lambda e: datetime.fromisoformat(e["time"]))
    for e in entries:
        if e["id"] == ident:
            return e
    die(f"no entry with id {ident}")


def remove_photo_file(entry):
    if entry.get("photo"):
        p = ROOT / entry["photo"]
        if p.exists():
            p.unlink()
        print("note: the photo file is removed, but if it was already pushed it stays in git history", file=sys.stderr)
    entry["photo"] = None
    entry.pop("src_hash", None)


def cmd_add(a):
    data = json.loads(a.data) if a.data else {}
    validate(a.type, data)
    if a.type in ("set", "bodyweight") and data.get("weight") is not None:
        data.setdefault("unit", default_unit())
    if a.type == "set" and data.get("reps") is not None and not data.get("reps_assumed"):
        data.pop("reps_assumed", None)
    entries = load_log()
    start = parse_time(a.time)
    added = []
    for i in range(max(1, a.repeat)):
        dt = start + timedelta(seconds=i)
        e = {"id": new_id(entries, dt, a.type), "time": dt.isoformat(), "type": a.type, **data,
             "photo": None, "confidence": a.confidence}
        if a.notes:
            e["notes"] = a.notes
        if a.photo and i == 0:
            src = resolve_photo(a.photo)
            size = attach_photo(e, src, entries)
            print(f"photo: {src.name} -> {e['photo']} ({size // 1024} KB, metadata stripped)")
        entries.append(e)
        added.append(e)
    save_log(entries)
    for e in added:
        print("added " + line(entries, e))


def cmd_edit(a):
    entries = load_log()
    e = find(entries, a.id)
    if a.data:
        data = json.loads(a.data)
        clash = CORE_KEYS & set(data)
        if clash:
            die(f"use the command-line flags for {sorted(clash)}, not --data")
        e.update(data)
        if "reps" in data and "reps_assumed" not in data:
            e.pop("reps_assumed", None)
    for k in a.unset or []:
        e.pop(k, None)
    if a.notes is not None:
        if a.notes:
            e["notes"] = a.notes
        else:
            e.pop("notes", None)
    if a.confidence:
        e["confidence"] = a.confidence
    if a.time:
        e["time"] = parse_time(a.time).isoformat()
    if a.remove_photo:
        remove_photo_file(e)
    if a.photo:
        if e.get("photo"):
            remove_photo_file(e)
        src = resolve_photo(a.photo)
        size = attach_photo(e, src, entries)
        print(f"photo: {src.name} -> {e['photo']} ({size // 1024} KB, metadata stripped)")
    validate(e["type"], {k: v for k, v in e.items() if k not in CORE_KEYS})
    save_log(entries)
    print("edited " + line(entries, e))


def cmd_delete(a):
    entries = load_log()
    e = find(entries, a.id)
    print("deleting " + line(entries, e))
    if e.get("photo"):
        remove_photo_file(e)
    entries.remove(e)
    save_log(entries)


def cmd_today(a):
    entries = load_log()
    day = parse_time(a.date + "T12:00" if a.date else None).date()
    todays = [e for e in entries if local_day(e) == day]
    print(f"{day:%A %d %B %Y}: {len(todays)} entries")
    for e in todays:
        print("  " + line(entries, e))


def cmd_recent(a):
    entries = load_log()
    for e in entries[-a.n:]:
        print(line(entries, e))


def cmd_uploads(a):
    files = upload_files()
    if not files:
        print(f"no images in {", ".join(map(str, UPLOAD_DIRS))}")
        return
    hashes = {e.get("src_hash"): e["id"] for e in load_log() if e.get("src_hash")}
    for p in files[: a.n]:
        st = p.stat()
        used = hashes.get(file_hash(p))
        when = datetime.fromtimestamp(st.st_mtime, tz())
        print(f"{when:%H:%M:%S}  {st.st_size // 1024:>6} KB  {p}{'  (already logged as ' + used + ')' if used else ''}")


def cmd_ref(a):
    src = resolve_photo(a.photo)
    slug = "".join(c if c.isalnum() else "-" for c in a.name.lower()).strip("-")
    dest = ROOT / PHOTO_DIR / "reference" / f"{slug}.jpg"
    n = 2
    while dest.exists():
        dest = ROOT / PHOTO_DIR / "reference" / f"{slug}-{n}.jpg"
        n += 1
    size = process_photo(src, dest)
    print(f"reference photo saved: {dest.relative_to(ROOT).as_posix()} ({size // 1024} KB, metadata stripped)")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add", help="add an entry")
    s.add_argument("type", choices=TYPES)
    s.add_argument("--data", help="JSON object of type-specific fields")
    s.add_argument("--photo", help="image path, or 'latest' for the newest upload")
    s.add_argument("--time", help="'HH:MM' today, or an ISO date-time; default now")
    s.add_argument("--confidence", choices=["high", "medium", "low"], default="high")
    s.add_argument("--notes")
    s.add_argument("--repeat", type=int, default=1, help="log this many identical entries (e.g. 3 sets)")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("edit", help="change an entry ('last' = most recent)")
    s.add_argument("id")
    s.add_argument("--data", help="JSON object of fields to set")
    s.add_argument("--unset", nargs="*", help="field names to remove")
    s.add_argument("--photo", help="attach/replace photo (path or 'latest')")
    s.add_argument("--remove-photo", action="store_true")
    s.add_argument("--time")
    s.add_argument("--confidence", choices=["high", "medium", "low"])
    s.add_argument("--notes", help="replace notes ('' clears)")
    s.set_defaults(func=cmd_edit)

    s = sub.add_parser("delete", help="delete an entry and its photo ('last' = most recent)")
    s.add_argument("id")
    s.set_defaults(func=cmd_delete)

    s = sub.add_parser("today", help="list today's entries (or --date YYYY-MM-DD)")
    s.add_argument("--date")
    s.set_defaults(func=cmd_today)

    s = sub.add_parser("recent", help="list the most recent entries")
    s.add_argument("n", type=int, nargs="?", default=15)
    s.set_defaults(func=cmd_recent)

    s = sub.add_parser("uploads", help="list uploaded images, newest first")
    s.add_argument("n", type=int, nargs="?", default=10)
    s.set_defaults(func=cmd_uploads)

    s = sub.add_parser("ref", help="save a reference photo of a machine")
    s.add_argument("--photo", required=True)
    s.add_argument("--name", required=True, help="e.g. lat-pulldown")
    s.set_defaults(func=cmd_ref)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
