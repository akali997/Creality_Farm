"""
Chương trình quản lý IP tĩnh cho máy in qua SSH
Giao diện PyQt6 - Quét máy in và set IP tĩnh trực tiếp
"""
import sys
import os
import csv
import time
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QLineEdit, QGroupBox, QMessageBox, QProgressBar,
                             QHeaderView, QDialog, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

# Thêm đường dẫn để import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from printer.discovery import discover_printers
from printer.api import get_printer_model, is_printer

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

# ==================== Worker Threads ====================

class ScanWorker(QThread):
    """Worker thread để quét máy in"""
    progress = pyqtSignal(int, int, int)  # progress, scanned, total
    result = pyqtSignal(list)  # danh sách máy in
    
    def __init__(self, network_prefix, start_ip, end_ip):
        super().__init__()
        self.network_prefix = network_prefix
        self.start_ip = start_ip
        self.end_ip = end_ip
    
    def run(self):
        discovered = []
        
        def progress_callback(prog, scanned, total):
            self.progress.emit(int(prog), scanned, total)
        
        def result_callback(printers, error=None):
            nonlocal discovered
            discovered = printers
        
        discover_printers(self.network_prefix, self.start_ip, self.end_ip, 
                         result_callback, progress_callback)
        
        # Lấy thông tin chi tiết
        printers_info = []
        for ip in discovered:
            try:
                model = get_printer_model(ip)
            except:
                model = "Unknown"
            
            printers_info.append({
                'ip': ip,
                'model': model,
                'static_ip': ip,  # Mặc định giữ nguyên IP
                'status': 'Chưa cấu hình'
            })
        
        self.result.emit(printers_info)

class SetStaticIPWorker(QThread):
    """Worker thread để set IP tĩnh qua SSH"""
    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, ip, new_ip, ssh_user, ssh_pass, gateway, dns, netmask):
        super().__init__()
        self.ip = ip
        self.new_ip = new_ip
        self.ssh_user = ssh_user
        self.ssh_pass = ssh_pass
        self.gateway = gateway
        self.dns = dns
        self.netmask = netmask
    
    def run(self):
        if not PARAMIKO_AVAILABLE:
            self.finished.emit(False, "Chưa cài đặt thư viện paramiko. Chạy: pip install paramiko")
            return
        
        try:
            # Kết nối SSH
            self.progress.emit("Đang kết nối SSH...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, username=self.ssh_user, password=self.ssh_pass, timeout=10)
            
            # Phát hiện network interface
            self.progress.emit("Phát hiện network interface...")
            stdin, stdout, stderr = ssh.exec_command("ip -o link show | awk -F': ' '{print $2}'")
            interfaces = stdout.read().decode().strip().split('\n')
            interfaces = [iface for iface in interfaces if iface and iface != 'lo']
            
            if not interfaces:
                ssh.close()
                self.finished.emit(False, "Không tìm thấy network interface")
                return
            
            # Ưu tiên wlan0 (WiFi), eth0, end0
            interface = None
            for priority in ['wlan0', 'eth0', 'end0', 'enp']:
                for iface in interfaces:
                    if priority in iface:
                        interface = iface
                        break
                if interface:
                    break
            
            if not interface:
                interface = interfaces[0]
            
            self.progress.emit(f"Interface: {interface}")
            
            # Phát hiện OS type
            self.progress.emit("Phát hiện hệ thống...")
            stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release 2>/dev/null | grep '^ID=' | cut -d= -f2")
            os_id = stdout.read().decode().strip().replace('"', '')
            
            self.progress.emit(f"OS: {os_id if os_id else 'unknown'}")
            
            # Cấu hình cho Buildroot (Creality printers)
            if os_id == 'buildroot' or not os_id:
                self.progress.emit("Cấu hình cho Buildroot...")
                success = self.configure_buildroot(ssh, interface)
            else:
                # Cấu hình cho các OS khác (Ubuntu, Debian, etc.)
                self.progress.emit("Cấu hình cho Linux thông thường...")
                success = self.configure_standard_linux(ssh, interface)
            
            ssh.close()
            
            if not success:
                self.finished.emit(False, "Cấu hình thất bại. Kiểm tra log SSH.")
                return
            
            # Verify - Đợi một chút để network ổn định
            self.progress.emit("Đợi network ổn định...")
            time.sleep(3)
            
            self.progress.emit("Kiểm tra kết nối tới IP mới...")
            max_attempts = 10
            for attempt in range(1, max_attempts + 1):
                self.progress.emit(f"Thử kết nối ({attempt}/{max_attempts})...")
                if is_printer(self.new_ip):
                    self.finished.emit(True, "✅ Cấu hình thành công!")
                    return
                time.sleep(2)
            
            # Nếu vẫn chưa kết nối được, có thể IP đã đổi nhưng máy in đang bận
            self.progress.emit("Kiểm tra IP cũ còn hoạt động không...")
            if not is_printer(self.ip):
                # IP cũ không còn phản hồi = đã đổi IP thành công
                self.finished.emit(True, "⚠️ Đã đổi IP nhưng máy in đang bận. Hãy đợi và thử ping " + self.new_ip)
            else:
                # IP cũ vẫn phản hồi = chưa đổi được
                self.finished.emit(False, "❌ Máy in vẫn dùng IP cũ. Có thể cần reboot.")
        
        except paramiko.AuthenticationException:
            self.finished.emit(False, "Sai SSH username/password")
        except Exception as e:
            self.finished.emit(False, f"Lỗi: {str(e)}")
    
    def configure_buildroot(self, ssh, interface):
        """Cấu hình IP tĩnh cho Buildroot (Creality printers)"""
        try:
            cidr = sum([bin(int(x)).count('1') for x in self.netmask.split('.')])
            
            # 1. Backup file interfaces
            self.progress.emit("Backup cấu hình cũ...")
            ssh.exec_command("cp /etc/network/interfaces /etc/network/interfaces.bak")
            time.sleep(0.5)
            
            # 2. Tạo cấu hình wlan0 static
            self.progress.emit("Tạo cấu hình IP tĩnh...")
            static_config = f"""

# Static IP configuration for {interface}
auto {interface}
iface {interface} inet static
    address {self.new_ip}
    netmask {self.netmask}
    gateway {self.gateway}
    dns-nameservers {self.dns}
"""
            
            # Thêm cấu hình vào file
            cmd = f"echo '{static_config}' >> /etc/network/interfaces"
            ssh.exec_command(cmd)
            time.sleep(0.5)
            
            # 3. Comment dòng udhcpc trong wifi_up.sh
            self.progress.emit("Tắt DHCP client...")
            ssh.exec_command("sed -i 's/^[[:space:]]*udhcpc/#udhcpc/g' /usr/bin/wifi_up.sh 2>/dev/null || true")
            time.sleep(0.5)
            
            # 4. Kill udhcpc process hiện tại
            self.progress.emit("Dừng DHCP client...")
            ssh.exec_command(f"killall udhcpc 2>/dev/null || true")
            time.sleep(0.5)
            
            # 5. Đặt IP tĩnh ngay lập tức (chạy trong background vì sẽ mất kết nối)
            self.progress.emit("Áp dụng IP tĩnh...")
            
            # Tạo script để chạy trong background
            change_ip_script = f"""#!/bin/sh
sleep 1
ifconfig {interface} {self.new_ip} netmask {self.netmask}
route del default 2>/dev/null
route add default gw {self.gateway}
echo 'nameserver {self.dns}' > /etc/resolv.conf
"""
            
            # Upload script
            ssh.exec_command(f"cat > /tmp/change_ip.sh << 'EOFSCRIPT'\n{change_ip_script}\nEOFSCRIPT")
            ssh.exec_command("chmod +x /tmp/change_ip.sh")
            time.sleep(0.3)
            
            # Chạy script trong background và đóng SSH ngay
            # Không đợi kết quả vì connection sẽ mất
            self.progress.emit("Khởi động lại network...")
            stdin, stdout, stderr = ssh.exec_command("nohup /tmp/change_ip.sh > /dev/null 2>&1 &")
            
            # Đóng SSH ngay không đợi
            time.sleep(0.5)
            
            self.progress.emit("Hoàn tất cấu hình!")
            return True
            
        except Exception as e:
            self.progress.emit(f"Lỗi: {str(e)}")
            return False
    
    def configure_standard_linux(self, ssh, interface):
        """Cấu hình IP tĩnh cho Linux thông thường (Ubuntu/Debian)"""
        try:
            cidr = sum([bin(int(x)).count('1') for x in self.netmask.split('.')])
            
            # Thử NetworkManager
            self.progress.emit("Thử NetworkManager...")
            stdin, stdout, stderr = ssh.exec_command("which nmcli")
            if stdout.read().decode().strip():
                commands = [
                    f"nmcli connection delete {interface} 2>/dev/null || true",
                    f"nmcli connection add type ethernet con-name {interface} ifname {interface}",
                    f"nmcli connection modify {interface} ipv4.method manual",
                    f"nmcli connection modify {interface} ipv4.addresses {self.new_ip}/{cidr}",
                    f"nmcli connection modify {interface} ipv4.gateway {self.gateway}",
                    f"nmcli connection modify {interface} ipv4.dns \"{self.dns}\"",
                    f"nmcli connection up {interface}",
                ]
                
                for cmd in commands:
                    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code != 0:
                        return False
                
                return True
            
            # Fallback: /etc/network/interfaces
            self.progress.emit("Dùng /etc/network/interfaces...")
            static_config = f"""
auto {interface}
iface {interface} inet static
    address {self.new_ip}
    netmask {self.netmask}
    gateway {self.gateway}
    dns-nameservers {self.dns}
"""
            
            ssh.exec_command("cp /etc/network/interfaces /etc/network/interfaces.bak")
            cmd = f"echo '{static_config}' >> /etc/network/interfaces"
            ssh.exec_command(cmd)
            ssh.exec_command(f"ifdown {interface} && ifup {interface}")
            
            return True
            
        except Exception as e:
            self.progress.emit(f"Lỗi: {str(e)}")
            return False

# ==================== Settings Dialog ====================

class SettingsDialog(QDialog):
    """Dialog cài đặt thông số SSH và Network"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài Đặt SSH & Network")
        self.setMinimumWidth(400)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QFormLayout()
        
        # SSH Settings
        ssh_group = QGroupBox("Thông Tin SSH")
        ssh_layout = QFormLayout()
        
        self.ssh_user_input = QLineEdit()
        self.ssh_user_input.setPlaceholderText("root")
        ssh_layout.addRow("Username:", self.ssh_user_input)
        
        self.ssh_pass_input = QLineEdit()
        self.ssh_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ssh_pass_input.setPlaceholderText("creality3d")
        ssh_layout.addRow("Password:", self.ssh_pass_input)
        
        self.ssh_port_input = QSpinBox()
        self.ssh_port_input.setRange(1, 65535)
        self.ssh_port_input.setValue(22)
        ssh_layout.addRow("Port:", self.ssh_port_input)
        
        ssh_group.setLayout(ssh_layout)
        
        # Network Settings
        network_group = QGroupBox("Cấu Hình Mạng")
        network_layout = QFormLayout()
        
        self.gateway_input = QLineEdit()
        self.gateway_input.setPlaceholderText("192.168.1.1")
        network_layout.addRow("Gateway:", self.gateway_input)
        
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("192.168.1.1")
        network_layout.addRow("DNS Server:", self.dns_input)
        
        self.netmask_input = QLineEdit()
        self.netmask_input.setPlaceholderText("255.255.255.0")
        network_layout.addRow("Netmask:", self.netmask_input)
        
        network_group.setLayout(network_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Lưu")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(ssh_group)
        main_layout.addWidget(network_group)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load settings từ file"""
        config_file = os.path.join('IP', 'ssh_config.txt')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            if key == 'ssh_user':
                                self.ssh_user_input.setText(value)
                            elif key == 'ssh_pass':
                                self.ssh_pass_input.setText(value)
                            elif key == 'ssh_port':
                                self.ssh_port_input.setValue(int(value))
                            elif key == 'gateway':
                                self.gateway_input.setText(value)
                            elif key == 'dns':
                                self.dns_input.setText(value)
                            elif key == 'netmask':
                                self.netmask_input.setText(value)
            except:
                pass
        
        # Default values
        if not self.ssh_user_input.text():
            self.ssh_user_input.setText("root")
        if not self.ssh_pass_input.text():
            self.ssh_pass_input.setText("creality3d")
        if not self.gateway_input.text():
            self.gateway_input.setText("192.168.1.1")
        if not self.dns_input.text():
            self.dns_input.setText("192.168.1.1")
        if not self.netmask_input.text():
            self.netmask_input.setText("255.255.255.0")
    
    def save_settings(self):
        """Lưu settings vào file"""
        config_file = os.path.join('IP', 'ssh_config.txt')
        try:
            with open(config_file, 'w') as f:
                f.write(f"ssh_user={self.ssh_user_input.text()}\n")
                f.write(f"ssh_pass={self.ssh_pass_input.text()}\n")
                f.write(f"ssh_port={self.ssh_port_input.value()}\n")
                f.write(f"gateway={self.gateway_input.text()}\n")
                f.write(f"dns={self.dns_input.text()}\n")
                f.write(f"netmask={self.netmask_input.text()}\n")
            
            QMessageBox.information(self, "Thành Công", "Đã lưu cài đặt!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
    
    def get_settings(self):
        """Trả về dict settings"""
        return {
            'ssh_user': self.ssh_user_input.text(),
            'ssh_pass': self.ssh_pass_input.text(),
            'ssh_port': self.ssh_port_input.value(),
            'gateway': self.gateway_input.text(),
            'dns': self.dns_input.text(),
            'netmask': self.netmask_input.text()
        }

# ==================== Main Window ====================

class StaticIPManager(QMainWindow):
    """Chương trình chính quản lý IP tĩnh"""
    
    def __init__(self):
        super().__init__()
        self.printers = []
        self.settings = {}
        self.setWindowTitle("Quản Lý IP Tĩnh Máy In")
        self.setMinimumSize(1000, 600)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🔧 QUẢN LÝ IP TĨNH MÁY IN QUA SSH")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)
        
        # Scan controls
        scan_group = QGroupBox("Quét Máy In")
        scan_layout = QHBoxLayout()
        
        scan_layout.addWidget(QLabel("Network:"))
        self.network_input = QLineEdit("192.168.1.")
        self.network_input.setMaximumWidth(150)
        scan_layout.addWidget(self.network_input)
        
        scan_layout.addWidget(QLabel("Từ:"))
        self.start_ip_input = QLineEdit("1")
        self.start_ip_input.setMaximumWidth(50)
        scan_layout.addWidget(self.start_ip_input)
        
        scan_layout.addWidget(QLabel("Đến:"))
        self.end_ip_input = QLineEdit("254")
        self.end_ip_input.setMaximumWidth(50)
        scan_layout.addWidget(self.end_ip_input)
        
        self.scan_btn = QPushButton("🔍 Quét Máy In")
        self.scan_btn.clicked.connect(self.start_scan)
        scan_layout.addWidget(self.scan_btn)
        
        self.settings_btn = QPushButton("⚙️ Cài Đặt SSH")
        self.settings_btn.clicked.connect(self.open_settings)
        scan_layout.addWidget(self.settings_btn)
        
        scan_layout.addStretch()
        scan_group.setLayout(scan_layout)
        main_layout.addWidget(scan_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "IP Hiện Tại", "Model", "IP Tĩnh Mới", "Trạng Thái", "Thao Tác"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        
        self.set_all_btn = QPushButton("⚡ Set IP Tất Cả")
        self.set_all_btn.clicked.connect(self.set_all_static_ip)
        self.set_all_btn.setEnabled(False)
        bottom_layout.addWidget(self.set_all_btn)
        
        self.save_csv_btn = QPushButton("💾 Lưu CSV")
        self.save_csv_btn.clicked.connect(self.save_to_csv)
        self.save_csv_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_csv_btn)
        
        self.load_csv_btn = QPushButton("📂 Load CSV")
        self.load_csv_btn.clicked.connect(self.load_from_csv)
        bottom_layout.addWidget(self.load_csv_btn)
        
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)
    
    def load_settings(self):
        """Load settings từ file"""
        config_file = os.path.join('IP', 'ssh_config.txt')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            self.settings[key] = value
            except:
                pass
        
        # Default settings
        if 'ssh_user' not in self.settings:
            self.settings = {
                'ssh_user': 'root',
                'ssh_pass': 'creality3d',
                'ssh_port': '22',
                'gateway': '192.168.1.1',
                'dns': '192.168.1.1',
                'netmask': '255.255.255.0'
            }
    
    def open_settings(self):
        """Mở dialog cài đặt"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.settings = dialog.get_settings()
    
    def start_scan(self):
        """Bắt đầu quét máy in"""
        network = self.network_input.text()
        start = self.start_ip_input.text()
        end = self.end_ip_input.text()
        
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Đang quét mạng...")
        
        self.scan_worker = ScanWorker(network, start, end)
        self.scan_worker.progress.connect(self.update_scan_progress)
        self.scan_worker.result.connect(self.scan_finished)
        self.scan_worker.start()
    
    def update_scan_progress(self, progress, scanned, total):
        """Cập nhật progress bar"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Đang quét: {scanned}/{total} ({progress}%)")
    
    def scan_finished(self, printers):
        """Xử lý kết quả quét"""
        self.printers = printers
        self.scan_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if not printers:
            self.status_label.setText("❌ Không tìm thấy máy in nào!")
            return
        
        self.status_label.setText(f"✅ Tìm thấy {len(printers)} máy in")
        self.populate_table()
        self.set_all_btn.setEnabled(True)
        self.save_csv_btn.setEnabled(True)
    
    def populate_table(self):
        """Hiển thị danh sách máy in lên table"""
        self.table.setRowCount(len(self.printers))
        
        for row, printer in enumerate(self.printers):
            # IP hiện tại
            ip_item = QTableWidgetItem(printer['ip'])
            ip_item.setFlags(ip_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, ip_item)
            
            # Model
            model_item = QTableWidgetItem(printer['model'])
            model_item.setFlags(model_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, model_item)
            
            # IP tĩnh mới (editable)
            static_ip_item = QTableWidgetItem(printer['static_ip'])
            self.table.setItem(row, 2, static_ip_item)
            
            # Trạng thái
            status_item = QTableWidgetItem(printer['status'])
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, status_item)
            
            # Button Set IP
            set_btn = QPushButton("Set IP")
            set_btn.clicked.connect(lambda checked, r=row: self.set_single_static_ip(r))
            self.table.setCellWidget(row, 4, set_btn)
    
    def set_single_static_ip(self, row):
        """Set IP tĩnh cho 1 máy"""
        printer = self.printers[row]
        new_ip = self.table.item(row, 2).text()
        
        # Validate IP
        if not self.validate_ip(new_ip):
            QMessageBox.warning(self, "Lỗi", "IP không hợp lệ!")
            return
        
        # Cập nhật printer data
        printer['static_ip'] = new_ip
        
        # Disable button
        btn = self.table.cellWidget(row, 4)
        btn.setEnabled(False)
        btn.setText("Đang set...")
        
        # Update status
        self.table.item(row, 3).setText("Đang cấu hình...")
        self.table.item(row, 3).setBackground(QColor(255, 255, 200))
        
        # Start worker
        self.current_row = row
        self.worker = SetStaticIPWorker(
            printer['ip'],
            new_ip,
            self.settings.get('ssh_user', 'root'),
            self.settings.get('ssh_pass', 'creality3d'),
            self.settings.get('gateway', '192.168.1.1'),
            self.settings.get('dns', '192.168.1.1'),
            self.settings.get('netmask', '255.255.255.0')
        )
        self.worker.progress.connect(lambda msg, r=row: self.update_progress(r, msg))
        self.worker.finished.connect(lambda success, msg, r=row: self.set_ip_finished(r, success, msg))
        self.worker.start()
    
    def update_progress(self, row, message):
        """Cập nhật progress message"""
        if row < self.table.rowCount():
            item = self.table.item(row, 3)
            if item:
                item.setText(message)
    
    def set_ip_finished(self, row, success, message):
        """Callback khi set IP xong"""
        btn = self.table.cellWidget(row, 4)
        if btn:
            btn.setEnabled(True)
            btn.setText("Set IP")
        
        status_item = self.table.item(row, 3)
        
        if success:
            status_item.setText("✅ " + message)
            status_item.setBackground(QColor(200, 255, 200))
            self.printers[row]['status'] = "Đã cấu hình"
            
            # Cập nhật IP hiện tại
            new_ip = self.table.item(row, 2).text()
            self.table.item(row, 0).setText(new_ip)
            self.printers[row]['ip'] = new_ip
        else:
            status_item.setText("❌ " + message)
            status_item.setBackground(QColor(255, 200, 200))
        
        # Nếu đang chạy set all, tiếp tục máy tiếp theo
        if hasattr(self, 'is_setting_all') and self.is_setting_all:
            self.set_next_printer()
    
    def set_all_static_ip(self):
        """Set IP tĩnh cho tất cả máy"""
        reply = QMessageBox.question(
            self,
            "Xác Nhận",
            f"Bạn có chắc muốn set IP tĩnh cho {len(self.printers)} máy in?\n\n"
            f"Quá trình này sẽ mất khoảng {len(self.printers) * 30} giây.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.is_setting_all = True
            self.set_all_index = 0
            self.set_all_btn.setEnabled(False)
            self.set_all_btn.setText("Đang set tất cả...")
            self.set_next_printer()
    
    def set_next_printer(self):
        """Set IP cho máy tiếp theo (tuần tự)"""
        if self.set_all_index >= len(self.printers):
            self.is_setting_all = False
            self.set_all_btn.setEnabled(True)
            self.set_all_btn.setText("⚡ Set IP Tất Cả")
            
            # Đếm thành công/thất bại
            success_count = sum(1 for p in self.printers if p['status'] == "Đã cấu hình")
            failed_count = len(self.printers) - success_count
            
            QMessageBox.information(
                self, 
                "Hoàn Thành", 
                f"Đã hoàn thành!\n\n"
                f"✅ Thành công: {success_count}/{len(self.printers)}\n"
                f"❌ Thất bại: {failed_count}/{len(self.printers)}"
            )
            return
        
        # Set máy hiện tại
        self.set_single_static_ip(self.set_all_index)
        self.set_all_index += 1
    
    def save_to_csv(self):
        """Lưu danh sách ra CSV"""
        csv_file = os.path.join('IP', 'printer_ip_mapping.csv')
        
        # Cập nhật data từ table
        for row in range(self.table.rowCount()):
            self.printers[row]['static_ip'] = self.table.item(row, 2).text()
        
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['ip', 'model', 'static_ip', 'status'])
                writer.writeheader()
                writer.writerows(self.printers)
            
            QMessageBox.information(self, "Thành Công", f"Đã lưu vào: {csv_file}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu: {str(e)}")
    
    def load_from_csv(self):
        """Load danh sách từ CSV"""
        csv_file = os.path.join('IP', 'printer_ip_mapping.csv')
        
        if not os.path.exists(csv_file):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy file CSV!")
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.printers = list(reader)
            
            self.populate_table()
            self.set_all_btn.setEnabled(True)
            self.save_csv_btn.setEnabled(True)
            self.status_label.setText(f"✅ Đã load {len(self.printers)} máy từ CSV")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể load: {str(e)}")
    
    def validate_ip(self, ip):
        """Validate IP address"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

# ==================== Main ====================

def main():
    app = QApplication(sys.argv)
    
    # Kiểm tra paramiko
    if not PARAMIKO_AVAILABLE:
        QMessageBox.warning(
            None,
            "Thiếu Thư Viện",
            "Chưa cài đặt thư viện 'paramiko'.\n\n"
            "Vui lòng chạy: pip install paramiko"
        )
    
    window = StaticIPManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

