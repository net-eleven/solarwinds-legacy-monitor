# Orion NOC Outage Reporter

An asynchronous, thread-safe Python automation tool designed for ISP Network Operations Centers (NOC) to extract live outage information from legacy **SolarWinds Orion v8.5** environments.

## ⚠️ Operational Notice

This project is designed for legacy **IIS/ASP.NET** deployments that do not expose modern **SWIS/REST APIs**. Instead, it authenticates through the web interface and retrieves data using concurrent HTTP requests.

To avoid overloading the target IIS server, **do not exceed 10 concurrent worker threads**. Increasing the thread pool beyond this limit may cause thread exhaustion, degraded performance, or temporary service disruption.

---

## ✨ Features

* **Works Around Legacy Limitations**
  Collects outage information directly from the Orion web interface when API or database access is unavailable.

* **Automatic ASP.NET Authentication**
  Handles legacy **ViewState** login tokens and maintains authenticated sessions throughout execution.

* **Accurate HTML Parsing**
  Filters unnecessary UI elements and extracts verified outage records using the `small-Down.gif` status indicator.

* **Concurrent Detail Collection**
  Fetches node and interface detail pages in parallel to retrieve precise **Last Database Update** timestamps, allowing fast processing even during large-scale outages such as backbone or fiber failures.

---

## 📂 Project Structure

```text
solarwinds-legacy-monitor/
├── main.py        # Application entry point and thread pool manager
├── login.py       # ASP.NET ViewState authentication
├── fetch.py       # Session management and HTTP requests
├── parse.py       # HTML parsing and data extraction
├── config.py      # Git-ignored configuration and credentials
└── .gitignore     # Prevents sensitive files from being committed
```

---

## 🛠 Installation

### 1. Clone the repository

```bash
git clone https://github.com/tarekrahman-coder/solarwinds-legacy-monitor.git
cd solarwinds-legacy-monitor
```

### 2. Install dependencies

```bash
pip install requests beautifulsoup4
```

### 3. Configure credentials

Create a `config.py` file in the project root.

> **Note:** This file is intentionally excluded from version control via `.gitignore` to prevent accidental exposure of NOC credentials.

```python
# config.py

BASE_URL = "http://YOUR_SERVER_IP"

LOGIN_URL = f"{BASE_URL}/Orion/Login.aspx"
DOWN_INTERFACES_URL = f"{BASE_URL}/NetPerfMon/Report.asp?Report=Down+Interfaces"
DOWN_NODE_URL = f"{BASE_URL}/NetPerfMon/Report.asp?Report=Down+Nodes"

USERNAME = "your_username"
PASSWORD = "your_password"

TIMEOUT = 15
```

---

## 🚀 Usage

Run the application from the project directory:

```bash
python main.py
```

---

## 🏗 Technical Highlights

* Thread-safe concurrent execution
* Persistent authenticated HTTP sessions
* Legacy ASP.NET ViewState authentication
* HTML parsing using BeautifulSoup
* Regular expression-based timestamp extraction
* Optimized for SolarWinds Orion v8.5 web interfaces
* Suitable for ISP NOC environments where API access is restricted

---

## 🔒 Security

* Credentials are stored locally in `config.py`.
* `config.py` should **never** be committed to source control.
* `.gitignore` is configured to exclude sensitive configuration files.

---

## 📄 License

This project is intended for educational purposes and internal automation within authorized environments. Ensure you have permission before running it against any SolarWinds Orion deployment.
