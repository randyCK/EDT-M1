#!/usr/bin/env python3
import json, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
cfg = json.loads((ROOT/"filter_config.json").read_text(encoding="utf-8"))
req = urllib.request.Request(cfg["source_url"], headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    raw = r.read().decode("utf-8", errors="replace")

blocks = re.findall(r"BEGIN:VEVENT.*?END:VEVENT", raw, re.S)
kept = [b for b in blocks if any(c in b for c in cfg["course_codes"])]

def field(b, n):
    m = re.search(r"^"+re.escape(n)+r"(?:;[^:]*)?:(.*)$", b, re.M)
    return m.group(1).strip() if m else ""

seen, unique = set(), []
for b in kept:
    key = (field(b,"UID"),field(b,"DTSTART"),field(b,"DTEND"),field(b,"SUMMARY"),field(b,"LOCATION"))
    if key not in seen:
        seen.add(key); unique.append(b)

header = raw.split("BEGIN:VEVENT",1)[0]
header = re.sub(r"^X-WR-CALNAME:.*$", "X-WR-CALNAME:"+cfg["calendar_name"], header, flags=re.M)
if "X-WR-CALNAME:" not in header:
    header = header.replace("BEGIN:VCALENDAR","BEGIN:VCALENDAR\nX-WR-CALNAME:"+cfg["calendar_name"],1)

out = (header + "".join(unique) + "END:VCALENDAR\r\n").replace("\r\n","\n").replace("\n","\r\n")
(ROOT/"public").mkdir(exist_ok=True)
(ROOT/"public/edt.ics").write_bytes(out.encode("utf-8"))
print(f"{len(unique)} événements conservés")
