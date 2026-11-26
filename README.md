# Deploy Demo

A small Python web app for demonstrating deployment basics: a dark server-monitoring dashboard that refreshes every 5 seconds. It uses the standard library plus one dependency, `psutil`, for resource and process monitoring.

| Route | Returns |
|---|---|
| `/` | Dashboard: CPU, RAM, disk, uptime, OS, Python version, page visits, top 2 processes |
| `/api/hello` | JSON greeting and server time |
| `/api/status` | JSON: server details, resources and top 2 processes |

## Requirements

- Python 3.8 or newer (3.10+ shows the Linux distro name on the dashboard; older versions show the kernel name)
- Git

Check with:

```bash
python3 --version
git --version
```

## 1. Get the code

```bash
git clone https://github.com/YOUR-NAME/deploy-demo.git
cd deploy-demo
```

## 2. Create a virtual environment

A virtual environment keeps this project's packages separate from the rest of the system.

```bash
python3 -m venv venv
```

Activate it:

```bash
# Linux / macOS
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

Your prompt now starts with `(venv)`. To leave it later, run `deactivate`.

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs `psutil`, which the app uses to report CPU, memory and disk usage. Make sure the venv is active first (your prompt shows `(venv)`), otherwise the package installs system-wide. Add more packages to `requirements.txt` as the app grows.

## 4. Run the app

```bash
python3 app.py
```

You should see:

```
Dashboard running on http://0.0.0.0:8080  (Ctrl+C to stop)
```

Use another port with the `PORT` variable:

```bash
PORT=3000 python3 app.py
```

Run it in the background and keep the terminal free:

```bash
python3 app.py > server.log 2>&1 &
```

Stop a background run with `kill %1`, or find it with `ps aux | grep app.py`.

## 5. Test it

In a second terminal:

```bash
curl http://localhost:8080/
curl http://localhost:8080/api/hello
curl http://localhost:8080/api/status
```

Or open `http://localhost:8080` in a browser to see the dashboard. Each request, including the dashboard's 5-second refresh calls to `/api/status`, appears in the server's terminal output.

## Sharing it

The app listens on `0.0.0.0`, which means it accepts connections from outside the machine. An app bound to `127.0.0.1` or `localhost` can only be reached locally, and cannot be shared with a public link.

In a cloud lab, publish port `8080` using the lab's "Share a web app" panel. Port `7681` is reserved for the lab terminal.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Address already in use` | Another program is using the port. Stop it, or run with `PORT=3000`. |
| `502 Bad Gateway` on the public link | The app is not running, is on a different port, or listens on `127.0.0.1`. Check with `ss -ltn`. |
| `python3: command not found` | Install Python 3, or try `python`. |
| `ModuleNotFoundError: No module named 'psutil'` | The venv is not active or dependencies are not installed. Run `source venv/bin/activate`, then `pip install -r requirements.txt`. |
| `No module named venv` | On Debian/Ubuntu run `sudo apt install python3-venv`. |
| `pip install psutil` fails to build | Install build tools: `sudo apt install python3-dev build-essential`. Most platforms use prebuilt wheels and do not need this. |
| Top processes show `0.0%` CPU | Normal on an idle machine. Generate load to see it change, for example `yes > /dev/null &` (stop it with `kill %1`). |
| Visit counter resets | It is stored in memory, so it resets when the app restarts. A database would keep it. |

## Notes

- This uses Python's built-in `http.server`, which is fine for demos and learning. For production use a proper server such as gunicorn behind Nginx or Caddy, with HTTPS and a process manager.
- Environment-specific settings (ports, secrets) belong in environment variables, not in the code.
