# Frequently Asked Questions (FAQ)

## General Questions

### What is Creality Farm Manager?

Creality Farm Manager is a desktop application for managing multiple Creality 3D printers (or any Klipper-based printers) simultaneously. It allows you to monitor printer status, upload files, start prints, and configure settings across multiple printers at once.

### Who developed this?

This project was developed through a collaboration between a user with Linux and 3D printing expertise (providing ideas and requirements) and Claude AI (providing development and coding assistance).

### Is it free?

Yes! This is completely free and open-source software under the MIT License.

### What printers are supported?

**Tested and verified:**
- Creality K1
- Creality K1 Max
- Creality Ender-3 V3 (with Moonraker)

**Should work:**
- Any printer running Klipper with Moonraker API
- Voron printers
- Custom Klipper installations

## Installation & Setup

### What operating system is supported?

Currently only Windows 10/11 (64-bit). Linux and macOS support may come in the future.

### Do I need to install anything on my printers?

No! The printers must already have Klipper and Moonraker installed (which Creality K1/K1 Max have by default). No additional software is needed on the printers.

### What is the default login for SSH?

For Creality printers:
- Username: `root`
- Password: `creality3d`

### Can I use this without static IPs?

Yes! The application can scan and find printers even with DHCP (dynamic IPs). However, static IPs are recommended for:
- More reliable connections
- Saving printer profiles
- Faster startup

## Features & Usage

### How many printers can I manage?

There's no hard limit. The application has been designed to handle multiple printers efficiently. Performance may vary based on your network and PC specifications.

### Can I upload different files to different printers?

Currently, batch upload sends the same file to all selected printers. For different files, you need to upload them individually or in different batches.

### Does it work over the internet?

No, this is designed for local network use only. Printers and the PC running this application must be on the same local network.

### Can I monitor prints remotely?

Only if you're on the same local network. For remote access, you would need to set up a VPN to your home network.

### What happens if a print fails?

The application tracks print success/failure in statistics. You can view the history and see which prints succeeded or failed.

## Troubleshooting

### Printers not detected during scan

**Possible causes:**
1. Printers not on same network
2. Firewall blocking port 7125
3. Moonraker not running on printers
4. Wrong IP range

**Solutions:**
- Verify printer IPs manually (check on printer screen)
- Try accessing `http://printer-ip:7125/server/info` in browser
- Try "Fast Scan" mode
- Temporarily disable firewall to test
- Check printer is powered on and connected to network

### Upload fails

**Possible causes:**
1. Printer in error state
2. Network connection lost
3. Insufficient storage on printer
4. File too large
5. Invalid G-code file

**Solutions:**
- Check printer status (not in error/emergency stop)
- Verify network connection
- Check printer storage space
- Try smaller file
- Verify G-code is valid

### Static IP configuration fails

**Possible causes:**
1. Wrong SSH credentials
2. SSH not enabled
3. Network connectivity issues
4. IP already in use

**Solutions:**
- Verify credentials (default: root/creality3d)
- Try manual SSH connection first: `ssh root@printer-ip`
- Check network connection
- Choose different IP address
- Restart printer after configuration

### Application crashes on startup

**Solutions:**
1. Check Python version: `python --version` (must be 3.11+)
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check for error messages in console
4. Delete config files and try again
5. Try running from command line to see errors

### Slow performance

**Possible causes:**
1. Many printers on network
2. Slow network connection
3. PC performance limitations

**Solutions:**
- Use "Fast Scan" mode
- Use static IPs (faster than scanning)
- Close other network-intensive applications
- Consider network upgrade if managing many printers

## Technical Questions

### What ports does it use?

- **Port 7125**: Moonraker API (required)
- **Port 22**: SSH (only for static IP configuration)

### Does it collect any data?

No! The application:
- Doesn't collect any telemetry
- Doesn't send data anywhere
- Stores everything locally
- No internet connection required (except to printers on LAN)

### Can I run multiple instances?

Yes, you can run multiple instances, but it's not recommended as they may conflict when accessing the same configuration files.

### How is data stored?

All data is stored locally in:
- Application directory for settings
- Configuration files for printer profiles
- No cloud storage or external databases

### Is my data secure?

Your data never leaves your computer. However:
- Ensure your local network is secure
- Use strong passwords for SSH
- Don't expose Moonraker API to the internet
- See [SECURITY.md](SECURITY.md) for more details

## Development & Contributing

### Can I contribute?

Yes! Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How do I report bugs?

Open an issue on GitHub with:
- Clear description of the bug
- Steps to reproduce
- System information
- Error logs if available

### Can I request features?

Absolutely! Open a feature request issue on GitHub with:
- Description of the feature
- Why it would be useful
- How you would use it

### What programming language is it written in?

Python 3.11+ with PyQt6 for the UI.

### Can I modify it for my needs?

Yes! It's open-source under MIT License. You can modify, distribute, and use it however you like.

## Licensing & Legal

### What license is it under?

MIT License - very permissive. You can use, modify, and distribute freely.

### Can I use it commercially?

Yes, the MIT License allows commercial use.

### Do I need to credit the authors?

Not required, but appreciated! The MIT License only requires that you include the license text if you distribute the software.

### Can I sell it?

Technically yes (MIT License allows it), but it's already free and open-source, so please don't. Instead, consider contributing improvements back to the community.

## Future Plans

### What features are planned?

See [CHANGELOG.md](CHANGELOG.md) for the roadmap. Current plans include:
- WiFi configuration management
- Advanced analytics
- Cloud-based remote access
- Mobile companion app
- Multi-language support
- Dark mode theme

### Will there be a macOS/Linux version?

Possibly! The code is mostly cross-platform already. Main work needed is testing and packaging for those platforms.

### Will there be a mobile app?

It's on the roadmap! A companion mobile app would be useful for monitoring prints on the go.

## Getting Help

### Where can I get support?

1. Check this FAQ
2. Read [README.md](README.md) and [INSTALL.md](INSTALL.md)
3. Search [existing issues](https://github.com/akali997/Creality_Farm/issues)
4. Open a new issue if needed
5. Start a discussion on GitHub

### How do I update the application?

```bash
cd Creality_Farm
git pull origin main
pip install -r requirements.txt --upgrade
```

### Is there a community/forum?

Use GitHub Discussions for:
- Questions
- Sharing tips
- Showing your setup
- General discussion

---

**Still have questions? [Open an issue](https://github.com/akali997/Creality_Farm/issues) or [start a discussion](https://github.com/akali997/Creality_Farm/discussions)!**

