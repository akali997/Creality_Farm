from PyQt6.QtCore import QThread, pyqtSignal
from printer.api import send_gcode_command
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class BatchOperationsWorker(QThread):
    """Worker thread để gửi lệnh hàng loạt song song tới nhiều máy in"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    progress_signal = pyqtSignal(int, int)  # (current, total)

    def __init__(self, ip_list, operations):
        super().__init__()
        self.ip_list = ip_list
        self.operations = operations  # List các thao tác: ['leveling', 'extrude', 'retract']
        self.cancel_flag = False
        self.lock = threading.Lock()
        self.completed_count = 0

    def _send_operation(self, ip, operation):
        """Gửi một lệnh tới một máy in (timeout ngắn, chỉ đủ để gửi lệnh)"""
        if self.cancel_flag:
            return
        
        try:
            # Tạo script G-code tương ứng với thao tác
            if operation == 'leveling':
                script = """SET_FILAMENT_SENSOR SENSOR=filament_sensor ENABLE=0
SET_TEMPERATURE_FAN_TARGET temperature_fan=soc_fan target=5
M109 S200
G28
BED_MESH_CLEAR
NOZZLE_CLEAR HOT_MIN_TEMP=200 HOT_MAX_TEMP=200 BED_MAX_TEMP=60
M400
M104 S160
M109 S160
M400
M204 S5000
SET_VELOCITY_LIMIT ACCEL_TO_DECEL=5000
BED_MESH_CALIBRATE
BED_MESH_OUTPUT
G1 Z50 F3600
CXSAVE_CONFIG
TURN_OFF_HEATERS
SET_TEMPERATURE_FAN_TARGET temperature_fan=soc_fan target=45
SET_FILAMENT_SENSOR SENSOR=filament_sensor ENABLE=1"""
                timeout = 10  # Timeout ngắn, chỉ đủ để gửi lệnh
            elif operation == 'extrude':
                script = """LOAD_MATERIAL
TURN_OFF_HEATERS"""
                timeout = 10
            elif operation == 'retract':
                script = """QUIT_MATERIAL
TURN_OFF_HEATERS"""
                timeout = 10
            else:
                return
            
            # Gửi lệnh với timeout ngắn (chỉ đủ để gửi, không đợi thực thi)
            success, message = send_gcode_command(ip, script, timeout=timeout)
            
            # Cập nhật progress
            with self.lock:
                self.completed_count += 1
                total_tasks = len(self.ip_list) * len(self.operations)
                self.progress_signal.emit(self.completed_count, total_tasks)
            
            # Gửi thông báo kết quả
            operation_names = {
                'leveling': 'Leveling',
                'extrude': 'Extrude',
                'retract': 'Retract'
            }
            op_name = operation_names.get(operation, operation)
            
            if success:
                self.update_signal.emit(f"✅ {ip}: {op_name} - Đã gửi lệnh thành công")
            else:
                self.update_signal.emit(f"❌ {ip}: {op_name} - {message}")
                
        except Exception as e:
            with self.lock:
                self.completed_count += 1
                total_tasks = len(self.ip_list) * len(self.operations)
                self.progress_signal.emit(self.completed_count, total_tasks)
            self.update_signal.emit(f"❌ {ip}: {operation} - Lỗi: {str(e)}")

    def run(self):
        """Gửi tất cả lệnh song song tới tất cả máy in"""
        total_tasks = len(self.ip_list) * len(self.operations)
        
        # Sử dụng ThreadPoolExecutor để gửi song song
        max_workers = min(50, len(self.ip_list) * len(self.operations))  # Tối đa 50 thread
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Tạo futures cho tất cả các tác vụ
            futures = []
            for ip in self.ip_list:
                if self.cancel_flag:
                    break
                for operation in self.operations:
                    if self.cancel_flag:
                        break
                    future = executor.submit(self._send_operation, ip, operation)
                    futures.append(future)
            
            # Đợi tất cả các lệnh được gửi xong
            for future in as_completed(futures):
                if self.cancel_flag:
                    break
                try:
                    future.result()  # Đợi và xử lý exception nếu có
                except Exception as e:
                    pass  # Exception đã được xử lý trong _send_operation
        
        self.finished_signal.emit()

    def cancel(self):
        """Hủy bỏ các thao tác đang thực hiện"""
        self.cancel_flag = True

