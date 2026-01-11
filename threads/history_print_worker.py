from PyQt6.QtCore import QObject, pyqtSignal
from printer.api import get_printer_status
from printer.file_manager import get_last_printed_file
from config.settings import session

class HistoryPrintWorker(QObject):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, ip_list):
        super().__init__()
        self.ip_list = ip_list

    def run(self):
        for ip in self.ip_list:
            filename = get_last_printed_file(ip)
            if not filename:
                self.update_signal.emit(f"{ip}: Không tìm thấy file lịch sử!")
                continue
            status = get_printer_status(ip)
            if status == "printing":
                self.update_signal.emit(f"{ip}: Máy đang in - không thể in lịch sử!")
                continue
            try:
                url_print = f"http://{ip}:7125/printer/print/start"
                response = session.post(url_print, headers={"Content-Type": "application/json"}, json={"filename": filename}, timeout=10)
                if response.status_code in (200, 201):
                    self.update_signal.emit(f"{ip}: Đã bắt đầu in file lịch sử {filename}")
                else:
                    self.update_signal.emit(f"{ip}: Lỗi HTTP {response.status_code} khi in lịch sử")
            except Exception as e:
                self.update_signal.emit(f"{ip}: Lỗi khi in lịch sử: {str(e)}")
        self.finished_signal.emit()