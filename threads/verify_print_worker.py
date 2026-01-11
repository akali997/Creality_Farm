from PyQt6.QtCore import QThread, pyqtSignal
from printer.api import get_printer_status, get_current_printing_file
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class VerifyPrintWorker(QThread):
    """Worker thread để verify trạng thái máy in sau khi upload"""
    update_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)  # {ip: {'status': str, 'file': str, 'success': bool}}
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, int)  # (current, total)
    
    def __init__(self, ip_list, expected_file_name, wait_time=3):
        super().__init__()
        self.ip_list = ip_list
        self.expected_file_name = expected_file_name
        self.wait_time = wait_time  # Thời gian đợi trước khi verify (giây)
        self.results = {}
        
    def _verify_single_printer(self, ip):
        """Verify một máy in có nhận lệnh thành công không"""
        try:
            # Lấy trạng thái hiện tại
            status = get_printer_status(ip)
            current_file = get_current_printing_file(ip)
            
            # Kiểm tra xem máy có đang in hoặc đã nhận file đúng không
            success = False
            status_lower = status.lower()
            
            if status_lower == "printing":
                # Đang in - kiểm tra tên file (so sánh không phân biệt hoa thường)
                if current_file and self.expected_file_name.lower() in current_file.lower():
                    success = True
                else:
                    success = False  # Đang in nhưng file khác
            elif status_lower in ["standby", "ready"]:
                # Standby - có thể vừa nhận lệnh, chưa bắt đầu in
                # Nếu có tên file đúng trong current_file thì coi như thành công
                if current_file and self.expected_file_name.lower() in current_file.lower():
                    success = True
                else:
                    success = False  # Chưa nhận lệnh
            elif status_lower in ["complete", "completed"]:
                # Có thể đã in xong rất nhanh (file nhỏ)
                # Kiểm tra file name, nếu đúng thì cũng coi như thành công
                if current_file and self.expected_file_name.lower() in current_file.lower():
                    success = True
                else:
                    success = False
            else:
                # Error hoặc unknown
                success = False
            
            return {
                'status': status,
                'file': current_file,
                'success': success
            }
        except Exception as e:
            return {
                'status': 'error',
                'file': '',
                'success': False,
                'error': str(e)
            }
    
    def run(self):
        """Verify song song tất cả máy in"""
        # Kiểm tra nếu không có máy in nào
        if not self.ip_list or len(self.ip_list) == 0:
            self.update_signal.emit("⚠️ Không có máy in nào để verify!")
            self.finished_signal.emit()
            return
        
        # Đợi một chút để máy in xử lý lệnh
        self.update_signal.emit(f"⏳ Đang đợi {self.wait_time}s để máy in xử lý lệnh...")
        time.sleep(self.wait_time)
        
        self.update_signal.emit(f"🔍 Đang kiểm tra trạng thái {len(self.ip_list)} máy in...")
        
        # Verify song song
        max_workers = min(20, len(self.ip_list))
        completed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self._verify_single_printer, ip): ip 
                      for ip in self.ip_list}
            
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    result = future.result()
                    self.results[ip] = result
                    
                    # Cập nhật progress
                    completed += 1
                    self.progress_signal.emit(completed, len(self.ip_list))
                    
                    # Emit result cho từng máy
                    self.result_signal.emit({ip: result})
                    
                except Exception as e:
                    self.results[ip] = {
                        'status': 'error',
                        'file': '',
                        'success': False,
                        'error': str(e)
                    }
                    completed += 1
                    self.progress_signal.emit(completed, len(self.ip_list))
        
        self.finished_signal.emit()
    
    def get_results(self):
        """Trả về kết quả verify"""
        return self.results
    
    def get_summary(self):
        """Trả về tóm tắt kết quả"""
        if not self.results:
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'success_ips': [],
                'failed_ips': []
            }
        
        success_count = sum(1 for r in self.results.values() if r['success'])
        failed_count = len(self.results) - success_count
        
        success_ips = [ip for ip, r in self.results.items() if r['success']]
        failed_ips = [ip for ip, r in self.results.items() if not r['success']]
        
        return {
            'total': len(self.results),
            'success': success_count,
            'failed': failed_count,
            'success_ips': success_ips,
            'failed_ips': failed_ips
        }

