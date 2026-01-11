from PyQt6.QtCore import QThread, pyqtSignal
from printer.api import upload_and_print
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class UploadThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, int)  # (current, total)

    def __init__(self, ip_list, file_path):
        super().__init__()
        self.ip_list = ip_list
        self.file_path = file_path
        self.cancel_flag = False
        self.lock = threading.Lock()
        self.completed_count = 0
        self.success_ips = []  # Danh sách máy upload thành công
        self.failed_ips = []   # Danh sách máy upload thất bại

    def _upload_single(self, ip):
        """Upload và in cho một máy in"""
        if self.cancel_flag:
            return
        
        try:
            success, message = upload_and_print(ip, self.file_path)
            
            # Cập nhật progress
            with self.lock:
                self.completed_count += 1
                self.progress_signal.emit(self.completed_count, len(self.ip_list))
                
                # Lưu kết quả
                if success:
                    self.success_ips.append(ip)
                else:
                    self.failed_ips.append(ip)
            
            # Gửi thông báo kết quả
            if success:
                self.update_signal.emit(f"✅ {ip}: {message}")
            else:
                self.update_signal.emit(f"❌ {ip}: {message}")
                
        except Exception as e:
            with self.lock:
                self.completed_count += 1
                self.failed_ips.append(ip)
                self.progress_signal.emit(self.completed_count, len(self.ip_list))
            self.update_signal.emit(f"❌ {ip}: Lỗi - {str(e)}")

    def run(self):
        """Upload song song tới tất cả máy in"""
        # Sử dụng ThreadPoolExecutor để upload song song
        max_workers = min(20, len(self.ip_list))  # Tối đa 20 thread đồng thời
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Tạo futures cho tất cả các tác vụ upload
            futures = []
            for ip in self.ip_list:
                if self.cancel_flag:
                    break
                future = executor.submit(self._upload_single, ip)
                futures.append(future)
            
            # Đợi tất cả upload xong
            for future in as_completed(futures):
                if self.cancel_flag:
                    break
                try:
                    future.result()  # Đợi và xử lý exception nếu có
                except Exception as e:
                    pass  # Exception đã được xử lý trong _upload_single
        
        self.finished_signal.emit()
    
    def cancel(self):
        """Hủy bỏ các upload đang thực hiện"""
        self.cancel_flag = True