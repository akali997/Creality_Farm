# Installation Guide

Detailed installation instructions for Creality Farm Manager.

## Table of Contents
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Operating System
- **Windows 10** (64-bit) or newer
- **Windows 11** (recommended)

### Software Requirements
- **Python 3.11 or higher** (3.12 recommended)
  - Download from [python.org](https://www.python.org/downloads/)
  - Make sure to check "Add Python to PATH" during installation

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space
- **Network**: Ethernet or WiFi connection to local network

### Network Requirements
- Printers must be on the same local network as your PC
- Port 7125 (Moonraker API) must be accessible
- For static IP configuration: Port 22 (SSH) must be accessible

## Quick Start

### 1. Install Python

Download and install Python 3.11+ from [python.org](https://www.python.org/downloads/)

**Important**: Check "Add Python to PATH" during installation!

### 2. Clone or Download

**Option A: Using Git**
```bash
git clone https://github.com/akali997/Creality_Farm.git
cd Creality_Farm
```

**Option B: Download ZIP**
1. Download ZIP from GitHub
2. Extract to desired location
3. Open terminal in extracted folder

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Application

```bash
python main.py
```

That's it! The application should now start.

## Detailed Installation

### Step 1: Python Installation

1. **Download Python**
   - Go to [python.org/downloads](https://www.python.org/downloads/)
   - Download Python 3.11 or newer for Windows

2. **Run Installer**
   - ✅ Check "Add Python to PATH"
   - ✅ Check "Install pip"
   - Click "Install Now"

3. **Verify Installation**
   ```bash
   python --version
   # Should show: Python 3.11.x or higher
   
   pip --version
   # Should show pip version
   ```

### Step 2: Download Application

**Method 1: Git Clone (Recommended)**

1. Install Git from [git-scm.com](https://git-scm.com/)

2. Clone repository:
   ```bash
   git clone https://github.com/yourusername/Creality_Farm.git
   cd Creality_Farm
   ```

**Method 2: Direct Download**

1. Go to GitHub repository
2. Click "Code" → "Download ZIP"
3. Extract ZIP to desired location
4. Open Command Prompt in that folder

### Step 3: Install Dependencies

Open Command Prompt or PowerShell in the project folder:

```bash
# Upgrade pip first (recommended)
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Dependencies that will be installed:**
- PyQt6 (6.10.0) - UI framework
- requests (2.31.0) - HTTP client
- paramiko (3.4.0) - SSH client
- python-dateutil (2.8.2) - Date utilities

### Step 4: First Run

```bash
python main.py
```

The application window should appear!

## Configuration

### Initial Setup

1. **Launch Application**
   ```bash
   python main.py
   ```

2. **Scan for Printers**
   - Click "Scan Printers" button
   - Wait for scan to complete
   - Printers will appear in the list

3. **Test Connection**
   - Click on a printer to select it
   - Check if status updates (temperature, state, etc.)

### Optional: Static IP Configuration

For better reliability, configure static IPs:

1. **Open IP Tools**
   - Run `IP_Tools.bat` or
   - Navigate to `IP/` folder and run `python static_ip_manager.py`

2. **Configure SSH Credentials**
   - Default for Creality: `root` / `creality3d`

3. **Scan and Configure**
   - Scan for printers
   - Assign desired IP addresses
   - Apply configuration

### Optional: Create Desktop Shortcut

**Windows:**

1. Right-click on `main.py`
2. Select "Create shortcut"
3. Edit shortcut properties:
   - Target: `"C:\Path\To\Python\python.exe" "C:\Path\To\Creality_Farm\main.py"`
   - Start in: `C:\Path\To\Creality_Farm`
   - Icon: Choose `icon.ico` from project folder

## Troubleshooting

### Python Not Found

**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
1. Reinstall Python with "Add to PATH" checked
2. Or add Python to PATH manually:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python311`

### Module Not Found Error

**Error**: `ModuleNotFoundError: No module named 'PyQt6'`

**Solution**:
```bash
pip install -r requirements.txt
```

If that fails:
```bash
pip install PyQt6 requests paramiko python-dateutil
```

### Multiple Python Versions

If you have multiple Python versions:

```bash
# Use specific version
python3.11 -m pip install -r requirements.txt
python3.11 main.py
```

### Permission Errors

**Error**: Permission denied during pip install

**Solution**: Run as administrator or use:
```bash
pip install --user -r requirements.txt
```

### Printers Not Detected

1. **Check Network Connection**
   - Ensure PC and printers are on same network
   - Verify printer IPs are accessible

2. **Test Moonraker API**
   - Open browser: `http://printer-ip:7125/server/info`
   - Should show JSON response

3. **Firewall Issues**
   - Temporarily disable firewall to test
   - Add exception for port 7125

4. **Try Fast Scan Mode**
   - Enable "Fast Scan" in application
   - This uses ping instead of API

### Application Crashes on Start

1. **Check Python Version**
   ```bash
   python --version
   ```
   Must be 3.11 or higher

2. **Reinstall Dependencies**
   ```bash
   pip uninstall PyQt6
   pip install PyQt6==6.10.0
   ```

3. **Check for Errors**
   - Run from command line to see error messages
   - Check for missing files

### Virtual Environment (Optional)

For isolated installation:

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

## Updating

### Update Application

```bash
cd Creality_Farm
git pull origin main
pip install -r requirements.txt --upgrade
```

### Update Dependencies Only

```bash
pip install -r requirements.txt --upgrade
```

## Uninstallation

### Remove Application

Simply delete the `Creality_Farm` folder.

### Remove Python Packages

```bash
pip uninstall PyQt6 requests paramiko python-dateutil -y
```

### Remove Python (Optional)

Use Windows "Add or Remove Programs" to uninstall Python.

## Next Steps

After installation:

1. Read the [README.md](README.md) for feature overview
2. Check [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute
3. Report issues on [GitHub Issues](https://github.com/yourusername/Creality_Farm/issues)

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/akali997/Creality_Farm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/akali997/Creality_Farm/discussions)
- **Documentation**: [README.md](README.md)

---

**Happy Printing! 🖨️**

