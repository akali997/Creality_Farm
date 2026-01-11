# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Considerations

### Network Security

This application communicates with 3D printers on your local network:

- **Local Network Only**: Designed for local network use. Do not expose to the internet without proper security measures.
- **No Authentication**: Moonraker API typically has no authentication. Ensure your network is secured.
- **SSH Credentials**: SSH passwords are used for IP configuration. These are not stored permanently.

### Data Privacy

- **No Data Collection**: This application does not collect or transmit any data outside your local network.
- **Local Storage**: All settings and statistics are stored locally on your computer.
- **No Telemetry**: No usage statistics or telemetry data is collected.

### Best Practices

1. **Use on Trusted Networks**: Only run on networks you trust and control
2. **Firewall Configuration**: Ensure proper firewall rules are in place
3. **Keep Printers Updated**: Regularly update printer firmware
4. **Strong SSH Passwords**: Use strong passwords for printer SSH access
5. **Static IPs**: Consider using static IPs for better security and reliability

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

### How to Report

1. **DO NOT** open a public GitHub issue
2. Send details to: **chinhpcs@gmail.com** with subject line "SECURITY - Creality Farm Manager"
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We'll acknowledge receipt within 48 hours
- **Updates**: Regular updates on progress
- **Timeline**: We aim to address critical issues within 7 days
- **Credit**: Security researchers will be credited (unless anonymity is requested)

### Disclosure Policy

- We follow responsible disclosure principles
- Security fixes will be released as patches
- Users will be notified of security updates
- Details will be disclosed after fixes are available

## Known Security Considerations

### Moonraker API

- Default Moonraker installations have no authentication
- API is accessible to anyone on the local network
- Consider enabling Moonraker authentication if available

### SSH Access

- SSH credentials are required for static IP configuration
- Credentials are only used during configuration and not stored
- Default Creality credentials are well-known (root/creality3d)
- Consider changing default SSH passwords

### Local File Access

- Application has access to local filesystem for G-code files
- Only accesses files explicitly selected by user
- No automatic file scanning or uploading

## Secure Configuration Recommendations

### Network Segmentation

Consider placing printers on a separate network segment:

```
Internet <-> Router <-> Main Network (computers, phones)
                  |
                  └-> Printer Network (printers only)
```

### Firewall Rules

Recommended firewall rules for printers:

- **Allow**: Port 7125 (Moonraker) from management PC only
- **Allow**: Port 22 (SSH) from management PC only
- **Block**: All incoming connections from internet
- **Block**: Printer-initiated outbound connections (optional)

### SSH Hardening

For Creality printers (if you have shell access):

1. Change default password:
   ```bash
   passwd root
   ```

2. Disable root login (after creating user account):
   ```bash
   # Edit /etc/ssh/sshd_config
   PermitRootLogin no
   ```

3. Use key-based authentication instead of passwords

## Third-Party Dependencies

This application uses several third-party libraries. Security updates:

- Regularly update dependencies: `pip install -r requirements.txt --upgrade`
- Check for security advisories on used packages
- Report dependency vulnerabilities through normal channels

## Updates and Patches

- Security patches will be released as soon as possible
- Check GitHub releases regularly for updates
- Enable GitHub watch notifications for security updates

## Questions?

For security-related questions (non-vulnerabilities):
- Open a GitHub discussion
- Tag with `security` label

---

**Security is a shared responsibility. Thank you for helping keep this project and its users safe! 🔒**

