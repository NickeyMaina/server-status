"""Cloud Lab Dashboard: a small server-monitoring web app.

Uses the Python standard library plus psutil.

Routes:
  /             Dark dashboard that refreshes every 5 seconds
  /api/hello    JSON greeting and server time
  /api/status   JSON: server details, resources, top 2 processes

Run:  python3 app.py            (PORT env var overrides the default 8080)
"""
import datetime
import json
import os
import platform
import socket
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psutil

PORT = int(os.environ.get("PORT", 8080))
HOST = "0.0.0.0"  # all interfaces, so the app is reachable from outside
STARTED = time.time()
visits = 0

GB = 1024 ** 3


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def get_os_name():
    try:
        return platform.freedesktop_os_release().get(
            "PRETTY_NAME", platform.system()
        )
    except (AttributeError, OSError):
        return f"{platform.system()} {platform.release()}"


def get_uptime():
    seconds = int(time.time() - psutil.boot_time())
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"


def get_resources():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_total_gb": round(memory.total / GB, 2),
        "ram_used_gb": round(memory.used / GB, 2),
        "ram_available_gb": round(memory.available / GB, 2),
        "ram_percent": memory.percent,
        "disk_total_gb": round(disk.total / GB, 2),
        "disk_used_gb": round(disk.used / GB, 2),
        "disk_free_gb": round(disk.free / GB, 2),
        "disk_percent": disk.percent,
    }


def get_top_processes():
    processes = []
    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            info = process.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"] or "Unknown",
                "cpu_percent": info["cpu_percent"] or 0.0,
                "memory_percent": round(info["memory_percent"] or 0, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    processes.sort(key=lambda p: p["cpu_percent"], reverse=True)
    return processes[:2]


def get_status():
    return {
        "status": "Online",
        "message": "Hello from my cloud lab!",
        "time": now(),
        "hostname": socket.gethostname(),
        "os": get_os_name(),
        "python": platform.python_version(),
        "uptime": get_uptime(),
        "visits": visits,
        "resources": get_resources(),
        "top_processes": get_top_processes(),
    }


DASHBOARD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cloud Lab Dashboard</title>
<style>
  :root {
    --bg: #0b1020; --card: #141b34; --text: #e8ecff; --muted: #8b94b8;
    --cyan: #22d3ee; --pink: #f472b6; --lime: #a3e635; --amber: #fbbf24;
    --violet: #a78bfa;
  }
  * { box-sizing: border-box; }
  body { margin: 0; padding: 1.5rem; background: radial-gradient(circle at top, #1a2250, var(--bg) 60%);
         color: var(--text); font-family: system-ui, sans-serif; min-height: 100vh; }
  header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
           gap: .5rem; max-width: 70rem; margin: 0 auto 1.25rem; }
  h1 { margin: 0; font-size: 1.6rem; background: linear-gradient(90deg, var(--cyan), var(--pink));
       -webkit-background-clip: text; background-clip: text; color: transparent; }
  .badge { background: #0f2a1d; color: var(--lime); padding: .25rem .75rem; border-radius: 999px;
           font-size: .85rem; border: 1px solid #1f5a3a; }
  .badge.down { background: #2a0f14; color: var(--pink); border-color: #5a1f2c; }
  .grid { display: grid; gap: 1rem; max-width: 70rem; margin: 0 auto;
          grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); }
  .card { background: var(--card); border-radius: 1rem; padding: 1.1rem 1.25rem;
          border: 1px solid #232c52; }
  .label { color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; }
  .value { font-size: 2rem; font-weight: 700; margin: .25rem 0 .5rem; }
  .sub { color: var(--muted); font-size: .85rem; }
  .bar { height: .6rem; background: #0b1020; border-radius: 999px; overflow: hidden; }
  .fill { height: 100%; width: 0; border-radius: 999px; transition: width .6s ease; }
  .cpu .value { color: var(--cyan); }  .cpu .fill { background: linear-gradient(90deg, #0891b2, var(--cyan)); }
  .ram .value { color: var(--pink); }  .ram .fill { background: linear-gradient(90deg, #db2777, var(--pink)); }
  .disk .value { color: var(--amber); } .disk .fill { background: linear-gradient(90deg, #d97706, var(--amber)); }
  .info .value { color: var(--lime); font-size: 1.4rem; }
  .violet { color: var(--violet); }
  table { width: 100%; border-collapse: collapse; margin-top: .5rem; font-size: .9rem; }
  th { text-align: left; color: var(--muted); font-weight: 500; padding: .35rem 0; }
  td { padding: .4rem 0; border-top: 1px solid #232c52; }
  .wide { grid-column: 1 / -1; }
  footer { max-width: 70rem; margin: 1rem auto 0; color: var(--muted); font-size: .85rem; }
  a { color: var(--cyan); }
</style>
</head>
<body>
<header>
  <h1>Cloud Lab Dashboard</h1>
  <span id="badge" class="badge">Connecting...</span>
</header>

<div class="grid">
  <div class="card cpu">
    <div class="label">CPU usage</div>
    <div class="value" id="cpu">-</div>
    <div class="bar"><div class="fill" id="cpuBar"></div></div>
  </div>
  <div class="card ram">
    <div class="label">RAM usage</div>
    <div class="value" id="ram">-</div>
    <div class="bar"><div class="fill" id="ramBar"></div></div>
    <div class="sub" id="ramSub"></div>
  </div>
  <div class="card disk">
    <div class="label">Disk usage</div>
    <div class="value" id="disk">-</div>
    <div class="bar"><div class="fill" id="diskBar"></div></div>
    <div class="sub" id="diskSub"></div>
  </div>
  <div class="card info">
    <div class="label">Uptime</div>
    <div class="value" id="uptime">-</div>
    <div class="sub">Page visits: <strong class="violet" id="visits">-</strong></div>
  </div>
  <div class="card info">
    <div class="label">System</div>
    <div class="value" id="os">-</div>
    <div class="sub">Python <span id="py"></span> on <span id="host"></span></div>
  </div>
  <div class="card wide">
    <div class="label">Top 2 processes by CPU</div>
    <table>
      <thead><tr><th>PID</th><th>Name</th><th>CPU %</th><th>Memory %</th></tr></thead>
      <tbody id="procs"></tbody>
    </table>
  </div>
</div>

<footer>
  Refreshes every 5 seconds. Last update: <span id="updated">never</span> |
  <a href="/api/status">/api/status</a> | <a href="/api/hello">/api/hello</a>
</footer>

<script>
  const $ = (id) => document.getElementById(id);
  const setBar = (id, pct) => { $(id).style.width = Math.min(pct, 100) + "%"; };

  async function refresh() {
    try {
      const res = await fetch("/api/status");
      const d = await res.json();
      const r = d.resources;

      $("badge").textContent = d.status;
      $("badge").className = "badge";
      $("cpu").textContent = r.cpu_percent + "%";      setBar("cpuBar", r.cpu_percent);
      $("ram").textContent = r.ram_percent + "%";      setBar("ramBar", r.ram_percent);
      $("ramSub").textContent = r.ram_used_gb + " GB used, " + r.ram_available_gb +
                                " GB available of " + r.ram_total_gb + " GB";
      $("disk").textContent = r.disk_percent + "%";    setBar("diskBar", r.disk_percent);
      $("diskSub").textContent = r.disk_used_gb + " GB used, " + r.disk_free_gb +
                                 " GB free of " + r.disk_total_gb + " GB";
      $("uptime").textContent = d.uptime;
      $("visits").textContent = d.visits;
      $("os").textContent = d.os;
      $("py").textContent = d.python;
      $("host").textContent = d.hostname;

      const body = $("procs");
      body.replaceChildren();
      d.top_processes.forEach((p) => {
        const tr = document.createElement("tr");
        [p.pid, p.name, p.cpu_percent + "%", p.memory_percent + "%"].forEach((v) => {
          const td = document.createElement("td");
          td.textContent = v;          // textContent, so process names are never parsed as HTML
          tr.appendChild(td);
        });
        body.appendChild(tr);
      });
      $("updated").textContent = new Date().toLocaleTimeString();
    } catch (err) {
      $("badge").textContent = "Offline";
      $("badge").className = "badge down";
    }
  }

  refresh();
  setInterval(refresh, 5000);
</script>
</body>
</html>
"""


class App(BaseHTTPRequestHandler):
    def _send(self, body, kind, status=200):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        global visits
        path = self.path.split("?", 1)[0]
        if path == "/":
            visits += 1  # only dashboard page loads count, not API refreshes
            self._send(DASHBOARD, "text/html; charset=utf-8")
        elif path == "/api/hello":
            self._send(json.dumps({"message": "Hello from my cloud lab!", "time": now()}),
                       "application/json")
        elif path == "/api/status":
            self._send(json.dumps(get_status()), "application/json")
        else:
            self._send(json.dumps({"error": "not found"}), "application/json", 404)


if __name__ == "__main__":
    # Prime psutil: the first CPU readings are always 0.0, so read once at startup.
    psutil.cpu_percent(interval=None)
    get_top_processes()
    print(f"Dashboard running on http://{HOST}:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer((HOST, PORT), App).serve_forever()
