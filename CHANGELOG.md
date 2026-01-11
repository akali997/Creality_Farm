# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- WiFi configuration management
- Advanced analytics dashboard
- Cloud-based remote access
- Mobile companion app
- Multi-language support
- Dark mode theme

## [1.0.0] - 2026-01-11

### Added
- **Printer Management**
  - Auto-discovery of printers on local network
  - Fast scan mode with ping-based detection
  - Real-time status monitoring (temperature, progress, state)
  - Color-coded UI for easy printer state identification
  - Smart sorting (standby printers on top)

- **Batch Operations**
  - Bulk upload and print to multiple printers
  - Batch printer settings:
    - Bed leveling (mesh calibration)
    - Material loading (extrude)
    - Material unloading (retract)
  - Batch file deletion

- **Static IP Management**
  - SSH-based IP configuration
  - No router access required
  - Auto-detection of Buildroot systems
  - Batch IP assignment
  - Automatic verification after configuration

- **Statistics & Monitoring**
  - Print history tracking
  - Success/failure rate analysis
  - Usage statistics (uploads, prints, deletes)
  - Session tracking

- **Profile Management**
  - Save printer groups
  - Quick load saved profiles
  - Settings persistence

- **UI Features**
  - Modern PyQt6 interface
  - Multi-select support
  - Progress indicators
  - Status indicators with colors
  - Tooltips and help text

### Technical
- Moonraker API integration
- Multi-threaded operations for performance
- SSH client for printer configuration
- Network scanning with concurrent requests
- Error handling and user feedback
- Data persistence between sessions

### Compatibility
- Windows 10/11 support
- Python 3.11+ support
- Tested with Creality K1, K1 Max
- Compatible with all Klipper+Moonraker printers

---

## Version History

### Development Process

This project was developed through an AI-assisted workflow:

1. **Initial Concept** - Idea originated from the need to manage multiple Creality K1/K1 Max printers efficiently
2. **Requirements Gathering** - Based on practical experience with Linux systems and 3D printer hardware
3. **Development** - Guided implementation with Claude AI assistance
4. **Testing & Refinement** - Iterative improvements based on real-world usage

### Credits

- **Concept & Direction**: Human user with Linux and 3D printing expertise
- **Development & Coding**: Claude AI (Anthropic)
- **Testing**: Real-world printer farm usage

---

## How to Update

To update to the latest version:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
python main.py
```

## Reporting Issues

Found a bug or have a suggestion? Please [open an issue](https://github.com/akali997/Creality_Farm/issues) on GitHub.

---

[Unreleased]: https://github.com/akali997/Creality_Farm/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/akali997/Creality_Farm/releases/tag/v1.0.0

