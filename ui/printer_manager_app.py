from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QListWidget, QLineEdit, QProgressDialog, QListWidgetItem,
                             QProgressBar, QDialog, QTableWidget, QTableWidgetItem, QCheckBox, QDialogButtonBox,
                             QMessageBox, QTextEdit, QTabWidget)
from PyQt6.QtGui import QFont, QColor, QMovie
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from printer.api import get_printer_status, get_current_printing_file
from printer.file_manager import get_file_list, delete_file
from printer.discovery import discover_printers
from threads.upload_thread import UploadThread
from threads.batch_operations_worker import BatchOperationsWorker
from threads.delete_files_worker import DeleteFilesWorker
from threads.verify_print_worker import VerifyPrintWorker
from config.app_settings import get_app_settings
import threading
import socket
import os
from datetime import datetime

    # Đã loại bỏ ScanProgressDialog

class ScanWorker(QThread):
    progress = pyqtSignal(float, int, int)
    finished = pyqtSignal(list, str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        def progress_callback(progress, scanned, total):
            self.progress.emit(progress, scanned, total)
            
        def result_callback(discovered, error=None):
            self.finished.emit(discovered, error)
        
        # Lấy địa chỉ IP của máy tính
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
            
        discover_printers(network_prefix, "1", "254", 
                         result_callback, progress_callback)


class FastScanWorker(QThread):
    """Worker cho chế độ quét nhanh - Ping để tìm IP online"""
    progress = pyqtSignal(float, int, int)
    ip_found = pyqtSignal(str)  # Emit ngay khi tìm thấy IP online
    finished = pyqtSignal(list, str)
    
    def __init__(self):
        super().__init__()
    
    def run(self):
        import subprocess
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Lấy network
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_prefix = '.'.join(local_ip.split('.')[:-1]) + '.'
        
        # Tạo danh sách IP
        total_ips = 254
        ips = [f"{network_prefix}{i}" for i in range(1, 255)]
        
        scanned_count = 0
        online_ips = []
        
        def ping_ip(ip):
            """Ping nhanh để check IP online"""
            try:
                # Windows ping with timeout 1s, 1 packet
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', '500', ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1
                )
                return ip if result.returncode == 0 else None
            except:
                return None
        
        # Quét ping nhanh với nhiều threads
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(ping_ip, ip): ip for ip in ips}
            
            for future in as_completed(futures):
                scanned_count += 1
                progress = (scanned_count / total_ips) * 100
                self.progress.emit(progress, scanned_count, total_ips)
                
                result = future.result()
                if result:
                    online_ips.append(result)
                    self.ip_found.emit(result)  # Emit ngay để hiển thị
        
        # Xong phần ping
        self.finished.emit(online_ips, None)


class CheckCompletedWorker(QThread):
    """Worker thread để kiểm tra trạng thái completed không block UI"""
    finished = pyqtSignal(list, list)  # (completed_printers, valid_printers)
    
    def __init__(self, selected_printers, printer_status_dict):
        super().__init__()
        self.selected_printers = selected_printers
        self.printer_status_dict = printer_status_dict
        
    def run(self):
        completed_printers = []
        for ip in self.selected_printers:
            try:
                current_status = get_printer_status(ip).lower()
                self.printer_status_dict[ip] = current_status
            except:
                current_status = self.printer_status_dict.get(ip, "unknown")
            
            if current_status in ["complete", "completed"]:
                completed_printers.append(ip)
        
        valid_printers = [ip for ip in self.selected_printers if ip not in completed_printers]
        self.finished.emit(completed_printers, valid_printers)


class GetPrinterDetailsWorker(QThread):
    """Worker thread để lấy thông tin chi tiết máy in song song"""
    update_item = pyqtSignal(int, str, str, str, str)  # (row, ip, model, status, file_printing)
    finished = pyqtSignal()
    
    def __init__(self, ip_list):
        super().__init__()
        self.ip_list = ip_list
        
    def run(self):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from printer.api import get_current_printing_file, get_printer_model
        
        # Lấy thông tin song song với ThreadPoolExecutor
        max_workers = min(20, len(self.ip_list))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for row, ip in enumerate(self.ip_list):
                future = executor.submit(self._get_printer_info, ip)
                futures[future] = (row, ip)
            
            for future in as_completed(futures):
                row, ip = futures[future]
                try:
                    model, status, file_printing = future.result()
                    self.update_item.emit(row, ip, model, status, file_printing)
                except Exception as e:
                    self.update_item.emit(row, ip, "Error", "error", "")
        
        self.finished.emit()
    
    def _get_printer_info(self, ip):
        """Lấy thông tin của một máy in"""
        from printer.api import get_printer_model, get_current_printing_file
        try:
            status = get_printer_status(ip)
            model = get_printer_model(ip)
            file_printing = get_current_printing_file(ip)
            return model, status, file_printing
        except:
            return "Unknown", "error", ""

class PrinterManagerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Creality Farm")
        self.setMinimumSize(1200, 800)
        
        # Load app settings
        self.app_settings = get_app_settings()
        
        # Dictionary để lưu trạng thái máy in
        self.printer_status_dict = {}
        
        # Restore window geometry
        self._restore_window_geometry()
        
        # Thiết lập stylesheet chung cho toàn bộ app
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #e8eef5);
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        # Main layout với margins compact hơn
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ===== PANEL BÊN TRÁI =====
        left_panel = QWidget()
        left_panel.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)
        
        # Header với icon và title - compact hơn
        self.label = QLabel("🖨️ Danh Sách Máy In")
        self.label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        left_layout.addWidget(self.label)

        # Scan button với loading animation - compact hơn
        scan_layout = QHBoxLayout()
        scan_layout.setSpacing(8)
        
        # Radio buttons cho chế độ quét
        self.scan_mode_normal = QCheckBox("Quét Thường")
        self.scan_mode_normal.setChecked(True)
        self.scan_mode_normal.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #2c3e50;
                background: transparent;
            }
        """)
        self.scan_mode_fast = QCheckBox("Quét Nhanh")
        self.scan_mode_fast.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #2c3e50;
                background: transparent;
            }
        """)
        
        # Tạo behavior radio button (chỉ chọn 1)
        self.scan_mode_normal.clicked.connect(lambda: self.toggle_scan_mode(True))
        self.scan_mode_fast.clicked.connect(lambda: self.toggle_scan_mode(False))
        
        scan_layout.addWidget(self.scan_mode_normal)
        scan_layout.addWidget(self.scan_mode_fast)
        scan_layout.addSpacing(10)
        
        self.scan_button = QPushButton("🔍 Quét Máy In")
        self.scan_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6439a0);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bc4, stop:1 #5a3290);
            }
        """)
        self.scan_button.clicked.connect(self.start_scan)
        scan_layout.addWidget(self.scan_button)
        
        self.gif_label = QLabel()
        self.gif_label.setFixedSize(32, 32)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.movie = QMovie(r"D:\LinhTinh\Python Program\Creality_Dev\Creality_Project\v5 - dev\loading.gif")
        self.movie.setScaledSize(self.gif_label.size())
        self.gif_label.setMovie(self.movie)
        self.gif_label.hide()
        scan_layout.addWidget(self.gif_label)
        scan_layout.addStretch()
        left_layout.addLayout(scan_layout)

        # Printer list với style đẹp
        self.printer_list = QListWidget()
        self.printer_list.setStyleSheet("""
            QListWidget {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px 0;
                border-radius: 8px;
                background: white;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
            }
            QListWidget::item:hover {
                background: #e3e6ff;
            }
        """)
        self.printer_list.setMinimumHeight(400)
        self.printer_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        left_layout.addWidget(self.printer_list)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background: #e9ecef;
                height: 20px;
                text-align: center;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
            }
        """)
        left_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #667eea;
                font-size: 13px;
                background: transparent;
            }
        """)
        left_layout.addWidget(self.progress_label)
        
        self.printer_list.itemSelectionChanged.connect(self.highlight_selected_printers)
        main_layout.addWidget(left_panel, 2)

        # ===== PANEL BÊN PHẢI =====
        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)
        
        # Dashboard header - compact hơn
        self.dashboard_label = QLabel("📊 Trạng Thái Máy In")
        self.dashboard_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        right_layout.addWidget(self.dashboard_label)
        
        # Dashboard table
        self.dashboard = QTableWidget()
        self.dashboard.setColumnCount(4)
        self.dashboard.setHorizontalHeaderLabels(["IP", "Model", "Trạng thái", "File đang in"])
        self.dashboard.setStyleSheet("""
            QTableWidget {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                gridline-color: #dee2e6;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
            }
        """)
        self.dashboard.setMinimumHeight(350)
        self.dashboard.verticalHeader().setVisible(False)
        self.dashboard.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.dashboard.setColumnWidth(0, 140)
        self.dashboard.setColumnWidth(1, 80)
        self.dashboard.setColumnWidth(2, 120)
        self.dashboard.setColumnWidth(3, 300)
        self.dashboard.setWordWrap(False)
        self.dashboard.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        right_layout.addWidget(self.dashboard)
        
        # Action buttons với spacing compact hơn
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.upload_button = QPushButton("📤 Upload & In")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #56CCF2, stop:1 #2F80ED);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #45b8dd, stop:1 #2670d8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3aa5ca, stop:1 #1d60c3);
            }
        """)
        self.upload_button.clicked.connect(self.select_and_send_gcode)
        buttons_layout.addWidget(self.upload_button)
        
        self.batch_settings_button = QPushButton("⚙️ Cài Đặt")
        self.batch_settings_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #F093FB, stop:1 #F5576C);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e080e8, stop:1 #e04658);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d070d8, stop:1 #d03848);
            }
        """)
        self.batch_settings_button.clicked.connect(self.open_batch_settings_dialog)
        buttons_layout.addWidget(self.batch_settings_button)
        
        self.delete_files_button = QPushButton("🗑️ Xóa File")
        self.delete_files_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FA709A, stop:1 #FEE140);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e96088, stop:1 #edd030);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #d85078, stop:1 #dcc020);
            }
        """)
        self.delete_files_button.clicked.connect(self.delete_selected_files)
        buttons_layout.addWidget(self.delete_files_button)
        
        right_layout.addLayout(buttons_layout)
        main_layout.addWidget(right_panel, 3)
        
        self.setLayout(main_layout)
        
        # Status colors cho dashboard
        self.status_colors = {
            "standby": QColor("#d4edda"),
            "error": QColor("#f8d7da"),
            "printing": QColor("#fff3cd"),
            "unknown": QColor("#e2e3e5"),
            "completed": QColor("#d1ecf1")
        }
        self.status_text_colors = {
            "standby": QColor("#155724"),
            "error": QColor("#721c24"),
            "printing": QColor("#856404"),
            "unknown": QColor("#383d41"),
            "completed": QColor("#0c5460")
        }
        
        # Thêm nút Statistics
        self._add_stats_button(left_layout)
    
    def _add_stats_button(self, layout):
        """Thêm button Statistics"""
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)
        
        # Statistics button
        self.stats_btn = QPushButton("📊 Thống kê")
        self.stats_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #138496;
            }
        """)
        self.stats_btn.clicked.connect(self.show_statistics)
        stats_layout.addWidget(self.stats_btn)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
    
    def _restore_window_geometry(self):
        """Khôi phục kích thước và vị trí cửa sổ"""
        geometry = self.app_settings.get_window_geometry()
        
        # Restore size
        self.resize(geometry["width"], geometry["height"])
        
        # Restore position (nếu có)
        if geometry["x"] is not None and geometry["y"] is not None:
            self.move(geometry["x"], geometry["y"])
        
        # Restore maximized state
        if geometry.get("maximized", False):
            self.showMaximized()
    
    def closeEvent(self, event):
        """Override closeEvent để lưu window geometry khi đóng"""
        # Save window geometry
        if not self.isMaximized():
            self.app_settings.save_window_geometry(
                self.width(),
                self.height(),
                self.x(),
                self.y(),
                False
            )
        else:
            self.app_settings.save_window_geometry(
                1200, 800, None, None, True
            )
        
        # Update last use
        self.app_settings.update_last_use()
        
        event.accept()
    
    def show_statistics(self):
        """Hiển thị dialog thống kê"""
        dialog = StatisticsDialog(self.app_settings, self)
        dialog.exec()
    
    def highlight_selected_printers(self):
        # Màu sắc được xử lý bởi stylesheet, không cần custom logic
        pass
    def select_all_printers(self):
        if hasattr(self, 'printer_checkboxes'):
            for checkbox in self.printer_checkboxes.values():
                checkbox.setChecked(True)

    def deselect_all_printers(self):
        if hasattr(self, 'printer_checkboxes'):
            for checkbox in self.printer_checkboxes.values():
                checkbox.setChecked(False)
    def get_selected_printers(self):
        # Trả về danh sách IP máy in được chọn từ QListWidget
        selected = []
        for item in self.printer_list.selectedItems():
            ip = item.text().split(' - ')[0]
            selected.append(ip)
        return selected
    
    def check_completed_printers_async(self, selected_printers, callback):
        """
        Kiểm tra trạng thái completed không block UI - chạy trong worker thread
        callback: hàm sẽ được gọi với (completed_printers, valid_printers)
        """
        self.check_worker = CheckCompletedWorker(selected_printers, self.printer_status_dict)
        self.check_worker.finished.connect(callback)
        self.check_worker.start()
    
    def show_completed_warning(self, completed_printers, valid_printers):
        """
        Hiển thị thông báo khi có máy in ở trạng thái completed
        Các máy completed sẽ bị bỏ qua, chỉ thực hiện trên các máy còn lại
        """
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("⚠️ Cảnh Báo - Máy In Đã Hoàn Thành")
        
        completed_list = "\n".join([f"  • {ip}" for ip in completed_printers])
        valid_list = "\n".join([f"  • {ip}" for ip in valid_printers]) if valid_printers else "  (Không có)"
        
        msg.setText(
            f"Các máy in sau đã hoàn thành in và sẽ BỊ BỎ QUA:\n\n{completed_list}\n\n"
            f"Vui lòng thu sản phẩm và nhấn OK trên màn hình máy in.\n\n"
            f"Thao tác sẽ TIẾP TỤC trên các máy in còn lại:\n\n{valid_list}"
        )
        
        # Chỉ có nút OK
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Tùy chỉnh font size
        msg.setStyleSheet("""
            QMessageBox {
                font-size: 14px;
            }
            QMessageBox QLabel {
                font-size: 14px;
                min-width: 450px;
            }
            QPushButton {
                font-size: 13px;
                padding: 8px 15px;
                min-width: 100px;
            }
        """)
        
        msg.exec()

    def toggle_scan_mode(self, is_normal):
        """Toggle giữa 2 chế độ quét"""
        if is_normal:
            self.scan_mode_normal.setChecked(True)
            self.scan_mode_fast.setChecked(False)
        else:
            self.scan_mode_normal.setChecked(False)
            self.scan_mode_fast.setChecked(True)
    
    def start_scan(self):
        self.label.setText("Đang quét máy in...")
        self.gif_label.show()
        self.movie.start()
        
        # Kiểm tra chế độ quét
        if self.scan_mode_fast.isChecked():
            # Quét nhanh
            self.scan_worker = FastScanWorker()
            self.scan_worker.ip_found.connect(self.add_printer_quick)  # Thêm ngay khi tìm thấy
        else:
            # Quét thường
            self.scan_worker = ScanWorker()
        
        self.scan_worker.progress.connect(self.update_scan_progress)
        self.scan_worker.finished.connect(self.scan_finished)
        self.scan_worker.start()

    def update_scan_progress(self, progress, scanned, total):
        mode = "nhanh" if self.scan_mode_fast.isChecked() else "thường"
        self.label.setText(f"🔍 Đang quét ({mode}): {scanned}/{total} ({int(progress)}%)")
    
    def add_printer_quick(self, ip):
        """Thêm máy in ngay vào list khi tìm thấy (quét nhanh)"""
        # Thêm vào list ngay với status "đang kiểm tra"
        item = QListWidgetItem(f"{ip} - Đang kiểm tra...")
        item.setBackground(QColor(255, 255, 200))  # Màu vàng
        item.setForeground(QColor(100, 100, 100))
        self.printer_list.addItem(item)

    def scan_finished(self, discovered, error=None):
        if error:
            self.label.setText(f"❌ Lỗi: {error}")
            # Ẩn gif loading
            if hasattr(self, 'gif_label'):
                self.gif_label.hide()
                self.movie.stop()
        else:
            if self.scan_mode_fast.isChecked():
                # Quét nhanh - verify ngầm
                self.label.setText(f"✅ Tìm thấy {len(discovered)} IP - Đang verify...")
                self.verify_background_printers(discovered)
            else:
                # Quét thường - như cũ
                self.label.setText(f"🔍 Tìm thấy {len(discovered)} máy - Đang tải thông tin...")
                self.printer_list.clear()
                self.printers = discovered
                self.dashboard.setRowCount(len(discovered))
                
                # Hiển thị IP trước, thông tin chi tiết sẽ cập nhật sau
                for row, ip in enumerate(discovered):
                    self.dashboard.setItem(row, 0, QTableWidgetItem(ip))
                    self.dashboard.setItem(row, 1, QTableWidgetItem("⏳"))
                    self.dashboard.setItem(row, 2, QTableWidgetItem("⏳"))
                    self.dashboard.setItem(row, 3, QTableWidgetItem("⏳"))
                
                # Lấy thông tin chi tiết trong worker thread - không block UI
                self.details_worker = GetPrinterDetailsWorker(discovered)
                self.details_worker.update_item.connect(self.update_dashboard_item)
                self.details_worker.finished.connect(self.details_fetch_finished)
                self.details_worker.start()
    
    def verify_background_printers(self, ip_list):
        """Verify các IP online có phải máy in không (chạy ngầm)"""
        from printer.api import is_printer
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        verified_printers = []
        
        # Verify song song
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(is_printer, ip): ip for ip in ip_list}
            
            for future in as_completed(futures):
                if future.result():
                    verified_printers.append(futures[future])
        
        # Verify xong - hiển thị
        self.printer_list.clear()
        self.printers = verified_printers
        self.dashboard.setRowCount(len(verified_printers))
        
        # Hiển thị IP
        for row, ip in enumerate(verified_printers):
            self.dashboard.setItem(row, 0, QTableWidgetItem(ip))
            self.dashboard.setItem(row, 1, QTableWidgetItem("⏳"))
            self.dashboard.setItem(row, 2, QTableWidgetItem("⏳"))
            self.dashboard.setItem(row, 3, QTableWidgetItem("⏳"))
        
        self.label.setText(f"✅ Verified {len(verified_printers)} máy in - Đang tải chi tiết...")
        
        # Load chi tiết
        self.details_worker = GetPrinterDetailsWorker(verified_printers)
        self.details_worker.update_item.connect(self.update_dashboard_item)
        self.details_worker.finished.connect(self.details_fetch_finished)
        self.details_worker.start()
    
    def update_dashboard_item(self, row, ip, model, status, file_printing):
        """Cập nhật một dòng trong dashboard"""
        try:
            self.dashboard.setItem(row, 1, QTableWidgetItem(str(model)))
            
            # Status chỉ có chữ, không có icon
            status_item = QTableWidgetItem(str(status))
            self.dashboard.setItem(row, 2, status_item)
            self.dashboard.setItem(row, 3, QTableWidgetItem(str(file_printing)))
            
            # Đổi màu nền theo trạng thái
            bg_color = self.status_colors.get(status.lower(), self.status_colors["unknown"])
            text_color = self.status_text_colors.get(status.lower(), self.status_text_colors["unknown"])
            
            for col in range(4):
                item = self.dashboard.item(row, col)
                item.setBackground(bg_color)
                item.setForeground(text_color)
            
            # Thêm vào printer list VỚI MÀU theo trạng thái
            self.printer_status_dict[ip] = status.lower()
            item = QListWidgetItem(f"{ip} - {model} - {status}")
            
            # Tô màu cho item trong list
            item.setBackground(bg_color)
            item.setForeground(text_color)
            
            self.printer_list.addItem(item)
        except Exception as e:
            pass
    
    def details_fetch_finished(self):
        """Hoàn thành lấy thông tin chi tiết"""
        # Sắp xếp danh sách: standby lên đầu, sau đó theo trạng thái
        self.sort_printer_list()
        
        self.label.setText(f"✅ Hoàn tất! Tìm thấy {len(self.printers)} máy in")
        # Ẩn gif loading
        if hasattr(self, 'gif_label'):
            self.gif_label.hide()
            self.movie.stop()
    
    def sort_printer_list(self):
        """Sắp xếp danh sách máy in: standby lên đầu, sau đó theo thứ tự ưu tiên"""
        # Định nghĩa thứ tự ưu tiên trạng thái
        priority = {
            'standby': 1,      # Ưu tiên cao nhất
            'ready': 2,
            'complete': 3,
            'completed': 3,
            'paused': 4,
            'printing': 5,
            'error': 6,
            'unknown': 7
        }
        
        # Lấy tất cả items
        items = []
        for i in range(self.printer_list.count()):
            item = self.printer_list.item(i)
            # Parse status từ text "IP - Model - Status"
            parts = item.text().split(' - ')
            status = parts[-1].lower() if len(parts) >= 3 else 'unknown'
            
            # Lấy priority
            item_priority = priority.get(status, 999)
            
            items.append((item_priority, item.text(), item.background(), item.foreground()))
        
        # Sắp xếp theo priority
        items.sort(key=lambda x: x[0])
        
        # Clear và add lại theo thứ tự mới
        self.printer_list.clear()
        for _, text, bg_color, fg_color in items:
            item = QListWidgetItem(text)
            item.setBackground(bg_color)
            item.setForeground(fg_color)
            self.printer_list.addItem(item)

    def get_printer_model(self, ip):
        from printer.api import get_printer_model
        return get_printer_model(ip)

    # Đã loại bỏ update_file_list do không còn sử dụng

    def get_max_printers(self):
        try:
            return max(0, int(self.max_printers_input.text()))
        except ValueError:
            return 0

    # ...existing code...

    def select_and_send_gcode(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn File G-code", "", "G-code Files (*.gcode)")
        if not file_path:
            return
        selected_printers = self.get_selected_printers()
        if not selected_printers:
            self.label.setText("⚠️ Chọn ít nhất một máy in")
            return
        
        # Lưu file_path để dùng sau
        self._pending_upload_file = file_path
        
        # Hiển thị loading
        self.label.setText("⏳ Đang kiểm tra trạng thái máy in...")
        
        # Kiểm tra completed async - không block UI
        self.check_completed_printers_async(selected_printers, self._on_upload_check_completed)
    
    def _on_upload_check_completed(self, completed_printers, valid_printers):
        """Callback sau khi kiểm tra completed xong cho upload"""
        if completed_printers:
            # Hiển thị cảnh báo về các máy bị bỏ qua
            self.show_completed_warning(completed_printers, valid_printers)
            
            # Nếu không còn máy nào hợp lệ, dừng lại
            if not valid_printers:
                self.label.setText("⚠️ Tất cả máy đã hoàn thành - Vui lòng thu sản phẩm!")
                return
        
        # Chỉ thực hiện trên các máy hợp lệ
        selected_printers = valid_printers
        file_path = self._pending_upload_file
        
        # Tạo progress dialog
        total_printers = len(selected_printers)
        self.upload_progress = QProgressDialog(
            f"Đang upload/in tới {total_printers} máy in...",
            "Hủy", 0, total_printers, self
        )
        self.upload_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.upload_progress.setMinimumDuration(0)
        self.upload_progress.show()
        
        # Tạo upload thread duy nhất cho TẤT CẢ máy in
        self.upload_thread = UploadThread(selected_printers, file_path)
        self.upload_thread.update_signal.connect(self.update_label)
        self.upload_thread.progress_signal.connect(self.update_upload_progress)
        self.upload_thread.finished_signal.connect(self.upload_finished)
        self.upload_progress.canceled.connect(self.upload_thread.cancel)
        self.upload_thread.start()

    def update_label(self, message):
        self.label.setText(message)
    
    def update_upload_progress(self, current, total):
        """Cập nhật progress dialog cho upload"""
        if hasattr(self, 'upload_progress'):
            self.upload_progress.setValue(current)
            self.upload_progress.setLabelText(
                f"Đang upload/in... ({current}/{total} máy)"
            )
    
    def upload_finished(self):
        """Xử lý khi hoàn thành upload tất cả máy"""
        if hasattr(self, 'upload_progress'):
            self.upload_progress.close()
        
        # Lấy danh sách máy upload THÀNH CÔNG
        uploaded_ips = self.upload_thread.success_ips
        failed_ips = self.upload_thread.failed_ips
        
        # Kiểm tra nếu không có máy nào upload thành công
        if not uploaded_ips or len(uploaded_ips) == 0:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("❌ Upload Thất Bại")
            
            if failed_ips:
                failed_list = "\n".join([f"  ❌ {ip}" for ip in failed_ips])
                msg.setText(
                    f"Tất cả {len(failed_ips)} máy in đều THẤT BẠI upload!\n\n"
                    f"Các máy thất bại:\n{failed_list}\n\n"
                    f"Vui lòng kiểm tra kết nối và thử lại!"
                )
            else:
                msg.setText("❌ Không có máy in nào được upload!")
            
            msg.exec()
            self.label.setText(f"❌ Upload thất bại!")
            return
        
        # Lấy tên file đã upload
        file_name = os.path.basename(self._pending_upload_file)
        
        # Hiển thị thông tin upload
        if failed_ips:
            self.label.setText(
                f"⚠️ Upload: {len(uploaded_ips)} thành công, {len(failed_ips)} thất bại - Đang verify..."
            )
        else:
            self.label.setText(f"✅ Upload xong {len(uploaded_ips)} máy - Đang verify...")
        
        # Bắt đầu verify trạng thái CHỈ cho các máy upload thành công
        self.verify_progress = QProgressDialog(
            f"Đang kiểm tra trạng thái {len(uploaded_ips)} máy in...",
            None, 0, len(uploaded_ips), self
        )
        self.verify_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.verify_progress.setMinimumDuration(0)
        self.verify_progress.setCancelButton(None)  # Không cho phép hủy verify
        self.verify_progress.show()
        
        # Tạo verify worker
        self.verify_worker = VerifyPrintWorker(uploaded_ips, file_name, wait_time=5)
        self.verify_worker.update_signal.connect(self.update_label)
        self.verify_worker.progress_signal.connect(self.update_verify_progress)
        self.verify_worker.result_signal.connect(self.update_printer_after_verify)
        self.verify_worker.finished_signal.connect(self.verify_finished)
        self.verify_worker.start()
    
    def update_verify_progress(self, current, total):
        """Cập nhật progress dialog cho verify"""
        if hasattr(self, 'verify_progress'):
            self.verify_progress.setValue(current)
            self.verify_progress.setLabelText(
                f"Đang kiểm tra... ({current}/{total} máy)"
            )
    
    def update_printer_after_verify(self, result_dict):
        """Cập nhật trạng thái máy in sau khi verify"""
        for ip, result in result_dict.items():
            # Tìm row tương ứng trong dashboard
            for row in range(self.dashboard.rowCount()):
                if self.dashboard.item(row, 0).text() == ip:
                    # Cập nhật trạng thái và file
                    status = result['status']
                    current_file = result['file']
                    
                    status_item = QTableWidgetItem(str(status))
                    self.dashboard.setItem(row, 2, status_item)
                    self.dashboard.setItem(row, 3, QTableWidgetItem(str(current_file)))
                    
                    # Đổi màu nền theo trạng thái
                    bg_color = self.status_colors.get(status.lower(), self.status_colors["unknown"])
                    text_color = self.status_text_colors.get(status.lower(), self.status_text_colors["unknown"])
                    
                    for col in range(4):
                        item = self.dashboard.item(row, col)
                        item.setBackground(bg_color)
                        item.setForeground(text_color)
                    
                    # Cập nhật printer list
                    for i in range(self.printer_list.count()):
                        list_item = self.printer_list.item(i)
                        if list_item.text().startswith(ip):
                            # Lấy model từ text cũ
                            parts = list_item.text().split(' - ')
                            if len(parts) >= 2:
                                model = parts[1]
                                list_item.setText(f"{ip} - {model} - {status}")
                            break
                    break
    
    def verify_finished(self):
        """Xử lý khi hoàn thành verify"""
        if hasattr(self, 'verify_progress'):
            self.verify_progress.close()
        
        # Lấy summary kết quả
        summary = self.verify_worker.get_summary()
        
        # Kiểm tra nếu không có kết quả
        if summary['total'] == 0:
            self.label.setText("⚠️ Không có máy nào để verify!")
            return
        
        # Ghi statistics
        file_name = os.path.basename(self._pending_upload_file)
        self.app_settings.record_print(
            file_name,
            summary['success_ips'] + summary['failed_ips'],
            summary['success'],
            summary['failed']
        )
        
        # Hiển thị kết quả chi tiết
        msg = QMessageBox(self)
        if summary['success'] == summary['total']:
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("✅ Thành Công")
            msg.setText(
                f"Tất cả {summary['total']} máy in đã nhận lệnh và đang in thành công!"
            )
        elif summary['success'] > 0:
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("⚠️ Một Số Máy Thất Bại")
            
            success_list = "\n".join([f"  ✅ {ip}" for ip in summary['success_ips']]) if summary['success_ips'] else "  (Không có)"
            failed_list = "\n".join([f"  ❌ {ip}" for ip in summary['failed_ips']]) if summary['failed_ips'] else "  (Không có)"
            
            msg.setText(
                f"Kết quả verify:\n\n"
                f"✅ Thành công: {summary['success']}/{summary['total']} máy\n{success_list}\n\n"
                f"❌ Thất bại: {summary['failed']}/{summary['total']} máy\n{failed_list}\n\n"
                f"Vui lòng kiểm tra lại các máy thất bại!"
            )
        else:
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("❌ Thất Bại")
            
            failed_list = "\n".join([f"  ❌ {ip}" for ip in summary['failed_ips']])
            
            msg.setText(
                f"Tất cả {summary['total']} máy in đều THẤT BẠI!\n\n"
                f"Các máy không nhận lệnh:\n{failed_list}\n\n"
                f"Vui lòng kiểm tra kết nối mạng và thử lại!"
            )
        
        msg.setStyleSheet("""
            QMessageBox {
                font-size: 14px;
            }
            QMessageBox QLabel {
                font-size: 14px;
                min-width: 500px;
            }
            QPushButton {
                font-size: 13px;
                padding: 8px 15px;
                min-width: 100px;
            }
        """)
        
        msg.exec()
        
        # Cập nhật label cuối cùng
        self.label.setText(
            f"✅ Hoàn tất! {summary['success']}/{summary['total']} máy đang in thành công"
        )

    def download_selected_files(self):
        pass

    def delete_selected_files(self):
        selected_printers = self.get_selected_printers()
        if not selected_printers:
            self.label.setText("⚠️ Chọn ít nhất một máy in")
            return
        
        # Tạo progress dialog
        total_printers = len(selected_printers)
        self.delete_progress = QProgressDialog(
            f"Đang xóa file trên {total_printers} máy in...",
            "Hủy", 0, total_printers, self
        )
        self.delete_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.delete_progress.setMinimumDuration(0)
        self.delete_progress.show()
        
        # Tạo delete worker thread
        self.delete_worker = DeleteFilesWorker(selected_printers)
        self.delete_worker.update_signal.connect(self.update_label)
        self.delete_worker.progress_signal.connect(self.update_delete_progress)
        self.delete_worker.finished_signal.connect(self.delete_finished)
        self.delete_progress.canceled.connect(self.delete_worker.cancel)
        self.delete_worker.start()
    
    def update_delete_progress(self, current, total):
        """Cập nhật progress dialog cho xóa file"""
        if hasattr(self, 'delete_progress'):
            self.delete_progress.setValue(current)
            self.delete_progress.setLabelText(
                f"Đang xóa file... ({current}/{total} máy)"
            )
    
    def delete_finished(self):
        """Xử lý khi hoàn thành xóa file"""
        if hasattr(self, 'delete_progress'):
            self.delete_progress.close()
        
        # Ghi statistics
        self.app_settings.record_files_deleted(self.delete_worker.total_deleted)
        
        self.label.setText(f"✅ Đã xóa {self.delete_worker.total_deleted} file trên {self.delete_worker.completed_count} máy!")

    def toggle_pause_resume(self):
        pass

    def stop_selected_printers(self):
        pass

    def print_history(self):
        pass
        self.progress.setMinimumDuration(0)
        self.progress.setCancelButton(None)
        self.progress.show()
        self.history_thread = QThread()
    # ...existing code...
        self.history_worker.moveToThread(self.history_thread)
        self.history_thread.started.connect(self.history_worker.run)
        self.history_worker.update_signal.connect(self.update_label)
        self.history_worker.finished_signal.connect(self.progress.close)
        self.history_worker.finished_signal.connect(self.history_thread.quit)
        self.history_thread.start()

    def update_printer_status_colors(self):
        """Cập nhật màu sắc cho tất cả máy in trong danh sách"""
        for i in range(self.printer_list.count()):
            item = self.printer_list.item(i)
            ip = item.text().split(" - ")[0]
            status = get_printer_status(ip)
            status_color = self.status_colors.get(status.lower(), self.status_colors["unknown"])
            item.setForeground(status_color)
    
    def open_batch_settings_dialog(self):
        """Mở dialog để chọn các thao tác cài đặt hàng loạt"""
        selected_printers = self.get_selected_printers()
        if not selected_printers:
            self.label.setText("⚠️ Chọn ít nhất một máy in")
            return
        
        # Hiển thị loading
        self.label.setText("⏳ Đang kiểm tra trạng thái máy in...")
        
        # Kiểm tra completed async - không block UI
        self.check_completed_printers_async(selected_printers, self._on_batch_check_completed)
    
    def _on_batch_check_completed(self, completed_printers, valid_printers):
        """Callback sau khi kiểm tra completed xong cho batch operations"""
        if completed_printers:
            # Hiển thị cảnh báo về các máy bị bỏ qua
            self.show_completed_warning(completed_printers, valid_printers)
            
            # Nếu không còn máy nào hợp lệ, dừng lại
            if not valid_printers:
                self.label.setText("⚠️ Tất cả máy đã hoàn thành - Vui lòng thu sản phẩm!")
                return
        
        # Chỉ thực hiện trên các máy hợp lệ
        selected_printers = valid_printers
        
        dialog = BatchSettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            operations = dialog.get_selected_operations()
            if operations:
                self.execute_batch_operations(selected_printers, operations)
    
    def execute_batch_operations(self, printer_ips, operations):
        """Thực hiện các thao tác hàng loạt trên các máy in đã chọn - gửi song song"""
        # Tạo progress dialog
        total_tasks = len(printer_ips) * len(operations)
        self.batch_progress = QProgressDialog(
            f"Đang thực hiện {len(printer_ips)} ...",
            "Hủy", 0, total_tasks, self
        )
        self.batch_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.batch_progress.setMinimumDuration(0)
        self.batch_progress.show()
        
        # Tạo và khởi chạy worker thread
        self.batch_worker = BatchOperationsWorker(printer_ips, operations)
        self.batch_worker.update_signal.connect(self.update_label)
        self.batch_worker.progress_signal.connect(self.update_batch_progress)
        self.batch_worker.finished_signal.connect(self.batch_operations_finished)
        self.batch_progress.canceled.connect(self.batch_worker.cancel)
        self.batch_worker.start()
    
    def update_batch_progress(self, current, total):
        """Cập nhật progress dialog"""
        if hasattr(self, 'batch_progress'):
            self.batch_progress.setValue(current)
            self.batch_progress.setLabelText(
                f"Đang gửi lệnh... ({current}/{total})"
            )
    
    def batch_operations_finished(self):
        """Xử lý khi hoàn thành gửi tất cả lệnh"""
        if hasattr(self, 'batch_progress'):
            self.batch_progress.close()
        self.label.setText("✅ Thành công!")


class BatchSettingsDialog(QDialog):
    """Dialog để chọn các thao tác cài đặt hàng loạt"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Cài Đặt Hàng Loạt")
        self.setMinimumWidth(480)
        self.setMinimumHeight(380)
        
        # Stylesheet cho dialog
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #e8eef5);
            }
            QLabel {
                color: #2c3e50;
            }
            QCheckBox {
                color: #2c3e50;
                font-size: 14px;
                padding: 10px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
                border-radius: 6px;
                border: 2px solid #667eea;
            }
            QCheckBox::indicator:unchecked {
                background: white;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid #667eea;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #764ba2;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6439a0);
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("⚙️ Cài Đặt Hàng Loạt")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(header_label)
        
        # Label hướng dẫn
        info_label = QLabel("Chọn các thao tác cần thực hiện trên máy in đã chọn:")
        info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #5a6c7d;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(info_label)
        
        # Container cho checkboxes
        checkbox_container = QWidget()
        checkbox_container.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setSpacing(15)
        
        # Checkboxes cho các thao tác
        self.checkboxes = {}
        
        self.leveling_check = QCheckBox("🔧 Leveling (Bed mesh calibration)")
        checkbox_layout.addWidget(self.leveling_check)
        self.checkboxes['leveling'] = self.leveling_check
        
        self.extrude_check = QCheckBox("➡️ Extrude (Load material)")
        checkbox_layout.addWidget(self.extrude_check)
        self.checkboxes['extrude'] = self.extrude_check
        
        self.retract_check = QCheckBox("⬅️ Retract (Unload material)")
        checkbox_layout.addWidget(self.retract_check)
        self.checkboxes['retract'] = self.retract_check
        
        layout.addWidget(checkbox_container)
        layout.addStretch()
        
        # Nút OK và Cancel
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_selected_operations(self):
        """Trả về danh sách các thao tác đã được chọn"""
        operations = []
        operation_names = {
            'leveling': 'leveling',
            'extrude': 'extrude',
            'retract': 'retract'
        }
        
        for key, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                operations.append(operation_names[key])
        
        return operations


class StatisticsDialog(QDialog):
    """Dialog hiển thị thống kê sử dụng"""
    
    def __init__(self, app_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Thống Kê Sử Dụng")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        
        self.app_settings = app_settings
        stats = app_settings.get_statistics()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("📊 Thống Kê Sử Dụng Creality Farm")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(header_label)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                background: white;
            }
            QTabBar::tab {
                background: #f8f9fa;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background: white;
                color: #667eea;
            }
        """)
        
        # Tab 1: Tổng quan
        overview_widget = self._create_overview_tab(stats)
        tabs.addTab(overview_widget, "📈 Tổng Quan")
        
        # Tab 2: Lịch sử
        history_widget = self._create_history_tab(stats)
        tabs.addTab(history_widget, "📜 Lịch Sử")
        
        layout.addWidget(tabs)
        
        # Reset button
        reset_btn = QPushButton("🔄 Reset Thống Kê")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #dc3545;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #c82333;
            }
        """)
        reset_btn.clicked.connect(self.reset_statistics)
        layout.addWidget(reset_btn)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #5a6268;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def _create_overview_tab(self, stats):
        """Tạo tab tổng quan"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Calculate success rate
        total_prints = stats["total_prints"]
        success_rate = 0
        if total_prints > 0:
            success_rate = (stats["successful_prints"] / total_prints) * 100
        
        # Format dates
        try:
            first_use = datetime.fromisoformat(stats["first_use_date"]).strftime("%d/%m/%Y")
            last_use = datetime.fromisoformat(stats["last_use_date"]).strftime("%d/%m/%Y %H:%M")
        except:
            first_use = "N/A"
            last_use = "N/A"
        
        # Stats text
        stats_text = f"""
<div style='font-size: 14px; line-height: 1.8;'>
    <h3 style='color: #667eea;'>📊 Thống Kê Tổng Quan</h3>
    
    <p><b>📅 Ngày bắt đầu sử dụng:</b> {first_use}</p>
    <p><b>🕐 Lần sử dụng cuối:</b> {last_use}</p>
    
    <hr style='border: 1px solid #e9ecef; margin: 15px 0;'>
    
    <h3 style='color: #667eea;'>🖨️ Thống Kê In Ấn</h3>
    
    <p><b>📤 Tổng số lần gửi in:</b> <span style='color: #667eea; font-size: 18px;'>{total_prints}</span></p>
    <p><b>✅ In thành công:</b> <span style='color: #28a745; font-size: 18px;'>{stats["successful_prints"]}</span></p>
    <p><b>❌ In thất bại:</b> <span style='color: #dc3545; font-size: 18px;'>{stats["failed_prints"]}</span></p>
    <p><b>📊 Tỷ lệ thành công:</b> <span style='color: #17a2b8; font-size: 18px;'>{success_rate:.1f}%</span></p>
    
    <hr style='border: 1px solid #e9ecef; margin: 15px 0;'>
    
    <h3 style='color: #667eea;'>📁 Quản Lý File</h3>
    
    <p><b>📤 Tổng file đã upload:</b> <span style='color: #667eea; font-size: 18px;'>{stats["total_files_uploaded"]}</span></p>
    <p><b>🗑️ Tổng file đã xóa:</b> <span style='color: #dc3545; font-size: 18px;'>{stats["total_files_deleted"]}</span></p>
</div>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(stats_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: none;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        layout.addWidget(text_edit)
        
        return widget
    
    def _create_history_tab(self, stats):
        """Tạo tab lịch sử"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        history = stats.get("print_history", [])
        
        if not history:
            no_history_label = QLabel("📭 Chưa có lịch sử in nào")
            no_history_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    color: #6c757d;
                    padding: 50px;
                }
            """)
            no_history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_history_label)
        else:
            # Table
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(["Ngày", "File", "Tổng", "Thành công", "Thất bại"])
            table.setRowCount(len(history))
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.setStyleSheet("""
                QTableWidget {
                    background: #f8f9fa;
                    border: none;
                    gridline-color: #dee2e6;
                    font-size: 13px;
                }
                QHeaderView::section {
                    background: #667eea;
                    color: white;
                    padding: 10px;
                    border: none;
                    font-weight: bold;
                }
            """)
            
            # Populate table
            for row, entry in enumerate(history):
                # Date
                try:
                    date_obj = datetime.fromisoformat(entry["date"])
                    date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = "N/A"
                table.setItem(row, 0, QTableWidgetItem(date_str))
                
                # File name
                table.setItem(row, 1, QTableWidgetItem(entry.get("file", "N/A")))
                
                # Total
                table.setItem(row, 2, QTableWidgetItem(str(entry.get("total_printers", 0))))
                
                # Success
                success_item = QTableWidgetItem(str(entry.get("success", 0)))
                success_item.setForeground(QColor("#28a745"))
                table.setItem(row, 3, success_item)
                
                # Failed
                failed_item = QTableWidgetItem(str(entry.get("failed", 0)))
                failed_item.setForeground(QColor("#dc3545"))
                table.setItem(row, 4, failed_item)
            
            # Resize columns
            table.setColumnWidth(0, 130)
            table.setColumnWidth(1, 250)
            table.setColumnWidth(2, 60)
            table.setColumnWidth(3, 100)
            table.setColumnWidth(4, 100)
            
            layout.addWidget(table)
        
        return widget
    
    def reset_statistics(self):
        """Reset thống kê"""
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc muốn reset tất cả thống kê?\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.app_settings.reset_statistics()
            QMessageBox.information(self, "Thành công", "Đã reset thống kê!")
            self.accept()  # Close dialog