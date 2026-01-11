from PyQt6.QtCore import QThread, pyqtSignal
from printer.file_manager import get_file_list, delete_file
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class DeleteFilesWorker(QThread):
    """Worker thread để xóa file song song trên nhiều máy in"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, int)  # (current, total)

    def __init__(self, ip_list):
        super().__init__()
        self.ip_list = ip_list
        self.cancel_flag = False
        self.lock = threading.Lock()
        self.completed_count = 0
        self.total_deleted = 0

    def _delete_files_for_printer(self, ip):
        """Xóa tất cả file cho một máy in"""
        if self.cancel_flag:
            return
        
        try:
            files = get_file_list(ip)
            if not files:
                self.update_signal.emit(f"⚠️ {ip}: Không tìm thấy file")
            else:
                deleted_count = 0
                for filename in files:
                    if self.cancel_flag:
                        break
                    success, message = delete_file(ip, filename)
                    if success:
                        deleted_count += 1
                        with self.lock:
                            self.total_deleted += 1
                
                if deleted_count > 0:
                    self.update_signal.emit(f"✅ {ip}: Đã xóa {deleted_count} file")
                else:
                    self.update_signal.emit(f"❌ {ip}: Không xóa được file nào")
            
            # Cập nhật progress
            with self.lock:
                self.completed_count += 1
                self.progress_signal.emit(self.completed_count, len(self.ip_list))
                
        except Exception as e:
            with self.lock:
                self.completed_count += 1
                self.progress_signal.emit(self.completed_count, len(self.ip_list))
            self.update_signal.emit(f"❌ {ip}: Lỗi - {str(e)}")

    def run(self):
        """Xóa file song song trên tất cả máy in"""
        # Sử dụng ThreadPoolExecutor để xóa song song
        max_workers = min(20, len(self.ip_list))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Tạo futures cho tất cả các tác vụ xóa
            futures = []
            for ip in self.ip_list:
                if self.cancel_flag:
                    break
                future = executor.submit(self._delete_files_for_printer, ip)
                futures.append(future)
            
            # Đợi tất cả xóa xong
            for future in as_completed(futures):
                if self.cancel_flag:
                    break
                try:
                    future.result()
                except Exception as e:
                    pass  # Exception đã được xử lý trong _delete_files_for_printer
        
        self.finished_signal.emit()
    
    def cancel(self):
        """Hủy bỏ các xóa file đang thực hiện"""
        self.cancel_flag = True

