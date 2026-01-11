# Creality Farm Manager

> 🤖 **AI-Assisted Development Project**
> 
> This project was developed through collaboration between human creativity and Claude AI. The original concept and requirements came from practical experience with Linux systems and 3D printer hardware, then brought to life with guidance and coding assistance from Claude AI.

A comprehensive management system for Creality 3D printer farms, supporting batch operations, remote monitoring, and automated workflow.

## Features

### 🖨️ Printer Management
- **Auto Discovery**: Automatically scan and detect printers on your network
- **Fast Scan Mode**: Quick network scanning with ping-based detection
- **Status Monitoring**: Real-time monitoring of printer status, temperature, and progress
- **Color-coded UI**: Easy identification of printer states (Standby, Printing, Error, etc.)
- **Smart Sorting**: Standby printers automatically sorted to the top

### 📤 Batch Operations
- **Bulk Upload & Print**: Upload and start printing on multiple printers simultaneously
- **Batch Settings**: Apply configurations to multiple printers at once
  - Bed Leveling (Mesh Calibration)
  - Material Loading (Extrude)
  - Material Unloading (Retract)
- **File Management**: Delete files from multiple printers in bulk

### 🌐 Static IP Management
- **SSH-based Configuration**: Set static IP directly on printers via SSH
- **No Router Access Required**: Configure IPs without router admin access
- **Auto-detection**: Automatically detects Buildroot-based systems (Creality printers)
- **Batch IP Assignment**: Set static IPs for multiple printers at once
- **Verification**: Automatic verification after IP configuration

### 📊 Statistics & Monitoring
- **Print History**: Track all print jobs with success/failure rates
- **Usage Statistics**: Monitor total prints, files uploaded, and deleted
- **Success Rate Analysis**: Calculate and display print success percentages
- **Session Tracking**: Record first use and last use dates

### 💾 Profile Management
- **Save Printer Groups**: Save frequently used printer combinations
- **Quick Load**: Quickly load saved printer profiles
- **Settings Persistence**: Window geometry and preferences saved between sessions

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.11 or higher
- **Network**: Local network connection to printers
- **Printers**: Creality K1/K1 Max or any Klipper-based printer with Moonraker API

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/akali997/Creality_Farm.git
cd Creality_Farm
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python main.py
```

## Dependencies

- **PyQt6**: Modern UI framework
- **requests**: HTTP client for Moonraker API
- **paramiko**: SSH client for static IP configuration
- **python-dateutil**: Date/time utilities

## Configuration

### First Time Setup

1. Launch the application
2. Click "Scan Printers" to discover printers on your network
3. Select printers you want to manage
4. Start printing!

### Static IP Configuration (Optional)

For improved reliability and profile usage:

1. Go to IP Tools (IP_Tools.bat)
2. Open "Static IP Manager"
3. Configure SSH credentials (usually root/creality3d)
4. Scan printers and assign static IPs
5. Apply configuration

## Usage

### Scanning Printers

**Normal Scan** (Default):
- Full Moonraker API verification
- Most accurate but slightly slower (~12s for 254 IPs)

**Fast Scan**:
- Ping-based detection (~3-5s)
- Background verification
- Shows results faster

### Uploading G-code

1. Select target printers (multi-select supported)
2. Click "Upload & Print"
3. Choose G-code file
4. System automatically:
   - Skips completed printers
   - Uploads files in parallel
   - Verifies print start
   - Shows detailed results

### Batch Settings

1. Select printers
2. Click "Settings" button
3. Choose operations:
   - 🔧 Leveling
   - ➡️ Load Material
   - ⬅️ Unload Material
4. Operations sent in parallel for efficiency

## Network Requirements

- Printers must be on the same local network
- Moonraker API port 7125 accessible
- For SSH configuration: SSH port 22 accessible

## Printer Compatibility

### Tested & Verified
- ✅ Creality K1
- ✅ Creality K1 Max
- ✅ Creality Ender-3 V3 (with Moonraker)

### Should Work (Klipper + Moonraker)
- Any Klipper-based printer with Moonraker API
- Voron printers
- Custom Klipper builds

## Project Structure

```
creality-farm-manager/
├── main.py                     # Application entry point
├── ui/
│   └── printer_manager_app.py  # Main UI application
├── printer/
│   ├── api.py                  # Moonraker API client
│   ├── discovery.py            # Network scanning
│   └── file_manager.py         # File operations
├── threads/
│   ├── upload_thread.py        # Upload worker
│   ├── verify_print_worker.py  # Print verification
│   └── batch_operations_worker.py
├── config/
│   ├── settings.py             # Configuration
│   └── app_settings.py         # Application settings
└── IP/
    └── static_ip_manager.py    # Static IP configuration tool
```

## Development

## Development Story

This project was born from:
- **Need**: Managing multiple Creality K1/K1 Max printers efficiently
- **Foundation**: Practical experience with Linux systems and 3D printer hardware
- **Execution**: Built with guidance and coding assistance from Claude AI (Anthropic)

The development process showcases how human domain knowledge combined with AI assistance can create practical, production-ready tools.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Troubleshooting

### Printers Not Detected

- Verify printers are on same network
- Check Moonraker is running (http://printer-ip:7125)
- Try Fast Scan mode
- Check firewall settings

### Upload Fails

- Verify printer status (not in error state)
- Check network connection
- Ensure sufficient storage on printer
- Verify G-code file is valid

### SSH Configuration Fails

- Verify SSH credentials (default: root/creality3d)
- Check SSH is enabled on printer
- Ensure network connectivity
- Try manual SSH connection first

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **Claude AI (Anthropic)** - Development guidance and coding assistance
- **Klipper & Moonraker teams** - Excellent 3D printer firmware
- **Creality** - K1/K1 Max hardware
- **PyQt team** - Powerful UI framework

## Support

For issues, questions, or feature requests:
- Open an issue on [GitHub Issues](https://github.com/akali997/Creality_Farm/issues)
- Check existing issues first
- Provide detailed information (printer model, OS, error logs)

## Roadmap

- [ ] WiFi management for printers
- [ ] Advanced statistics and analytics
- [ ] Remote access via cloud
- [ ] Mobile app companion
- [ ] Multi-language support
- [ ] Dark mode theme

---

**Made with ❤️ for the 3D printing community**

