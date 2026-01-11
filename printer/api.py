import requests
import os
from config.settings import session, GCODE_FOLDER

def is_printer(ip):
    try:
        url = f"http://{ip}:7125/printer/info"
        response = session.get(url, timeout=2.5)  # 2.5s - cân bằng tốc độ và độ tin cậy
        return response.status_code == 200
    except:
        return False

def get_printer_status(ip):
    try:
        url = f"http://{ip}:7125/printer/objects/query?print_stats"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("status", {}).get("print_stats", {})
            return data.get("state", "unknown")
    except:
        return "unknown"

def get_printer_model(ip):
    try:
        url = f"http://{ip}:7125/printer/info"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("result", {})
            model = data.get("hostname", "Unknown")
            if "ender" in model.lower():
                return "Ender-3 V3"
            elif "k1" in model.lower():
                return "K1 Max"
            return model
        return "Unknown"
    except:
        return "Unknown"

def get_printer_temperature(ip):
    try:
        url = f"http://{ip}:7125/printer/objects/query?heater_bed&extruder"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("status", {})
            bed_temp = data.get("heater_bed", {}).get("temperature", "N/A")
            extruder_temp = data.get("extruder", {}).get("temperature", "N/A")
            return f"Bed: {bed_temp}°C, Extruder: {extruder_temp}°C"
        return "N/A"
    except:
        return "N/A"

def get_printer_progress(ip):
    try:
        url = f"http://{ip}:7125/printer/objects/query?virtual_sdcard&print_stats"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("status", {})
            virtual_sdcard = data.get("virtual_sdcard", {})
            print_stats = data.get("print_stats", {})
            
            if print_stats.get("state") == "printing":
                file_position = virtual_sdcard.get("file_position", 0)
                file_size = virtual_sdcard.get("file_size", 0)
                if file_size > 0:
                    progress = (file_position / file_size) * 100
                    return round(progress, 1)
            return 0
        return 0
    except:
        return 0

def get_printer_errors(ip):
    try:
        url = f"http://{ip}:7125/printer/objects/query?print_stats"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("status", {}).get("print_stats", {})
            error = data.get("error", None)
            return error if error else "No errors"
        return "Unable to fetch errors"
    except:
        return "Connection error"

def get_current_printing_file(ip):
    try:
        url = f"http://{ip}:7125/printer/objects/query?print_stats"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            data = response.json().get("result", {}).get("status", {}).get("print_stats", {})
            state = data.get("state", "unknown")
            if state == "printing":
                filename = data.get("filename", "None")
                return filename
            return "None"
        return "None"
    except:
        return "None"

def upload_file(ip, filename, file_content):
    try:
        url_upload = f"http://{ip}:7125/server/files/upload"
        response = session.post(url_upload, files={"file": (filename, file_content)}, timeout=300)
        return response.status_code in (200, 201)
    except:
        return False

def upload_and_print(ip, file_path):
    try:
        status = get_printer_status(ip)
        if status == "printing":
            return False, "Máy in đang in - không thể gửi lệnh in."
        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            if not upload_file(ip, filename, f):
                return False, "Lỗi khi upload file."
        url_print = f"http://{ip}:7125/printer/print/start"
        response = session.post(url_print, headers={"Content-Type": "application/json"}, json={"filename": filename}, timeout=10)
        if response.status_code in (200, 201):
            return True, f"Đã upload & bắt đầu in (HTTP {response.status_code})."
        return False, f"Lỗi HTTP {response.status_code} khi gửi lệnh in."
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

def pause_print(ip):
    try:
        url = f"http://{ip}:7125/printer/print/pause"
        response = session.post(url, timeout=10)
        if response.status_code in (200, 201):
            return True, "Đã tạm dừng in."
        return False, f"Lỗi HTTP {response.status_code} khi tạm dừng in."
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

def resume_print(ip):
    try:
        url = f"http://{ip}:7125/printer/print/resume"
        response = session.post(url, timeout=10)
        if response.status_code in (200, 201):
            return True, "Đã tiếp tục in."
        return False, f"Lỗi HTTP {response.status_code} khi tiếp tục in."
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

def stop_print(ip):
    try:
        status = get_printer_status(ip)
        if status != "printing":
            return False, "Máy in không ở trạng thái in, không cần dừng."
        url = f"http://{ip}:7125/printer/print/cancel"
        response = session.post(url, timeout=10)
        if response.status_code in (200, 201):
            return True, "Đã dừng in thành công."
        return False, f"Lỗi HTTP {response.status_code} khi dừng in."
    except Exception as e:
        return False, f"Lỗi: {str(e)}"

def send_gcode_command(ip, gcode, timeout=300):
    """
    Gửi lệnh G-code tới máy in thông qua Moonraker API
    timeout: Thời gian chờ tối đa (mặc định 300 giây cho các lệnh dài như selfcheck)
    """
    try:
        url = f"http://{ip}:7125/printer/gcode/script"
        payload = {"script": gcode}
        response = session.post(url, json=payload, timeout=timeout)
        if response.status_code in (200, 201):
            return True, f"Đã gửi lệnh: {gcode}"
        return False, f"Lỗi HTTP {response.status_code} khi gửi lệnh G-code."
    except Exception as e:
        return False, f"Lỗi khi gửi lệnh G-code: {str(e)}"

def wait_for_printer_ready(ip, max_wait_time=600, check_interval=2):
    """
    Chờ máy in sẵn sàng (không còn lệnh nào đang chạy)
    max_wait_time: Thời gian chờ tối đa (giây)
    check_interval: Khoảng thời gian giữa các lần kiểm tra (giây)
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # Kiểm tra trạng thái máy in
            url = f"http://{ip}:7125/printer/objects/query?print_stats&idle_timeout"
            response = session.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json().get("result", {}).get("status", {})
                print_stats = data.get("print_stats", {})
                state = print_stats.get("state", "unknown")
                
                # Nếu máy in ở trạng thái standby hoặc ready, có thể gửi lệnh tiếp
                if state in ["standby", "complete", "cancelled"]:
                    return True
                
                # Kiểm tra xem có lệnh nào đang chờ không
                url_queue = f"http://{ip}:7125/printer/objects/query?gcode_move"
                response_queue = session.get(url_queue, timeout=5)
                if response_queue.status_code == 200:
                    queue_data = response_queue.json().get("result", {}).get("status", {})
                    gcode_move = queue_data.get("gcode_move", {})
                    # Nếu không có lệnh nào trong queue, máy in sẵn sàng
                    # (Thực tế Moonraker không có queue status trực tiếp, nên ta kiểm tra state)
                    if state not in ["printing", "paused"]:
                        time.sleep(check_interval)
                        return True
        except Exception:
            pass
        
        time.sleep(check_interval)
    
    return False

def run_selfcheck(ip):
    """
    Chạy selfcheck - kiểm tra tự động máy in bao gồm:
    - Home all axes (G28)
    - Input shaping calibration (INPUTSHAPER)
    - Bed leveling (G29)
    - Tắt nhiệt độ
    
    Gửi tất cả các lệnh trong một script để đảm bảo chúng chạy tuần tự
    """
    # Gửi tất cả các lệnh trong một script, Moonraker sẽ thực hiện tuần tự
    script = """G28
M400
INPUTSHAPER
M400
G29
M400
TURN_OFF_HEATERS"""
    
    success, message = send_gcode_command(ip, script, timeout=600)
    if success:
        return True, f"Đã gửi selfcheck (G28 + INPUTSHAPER + G29): {message}"
    else:
        return False, f"Lỗi khi gửi selfcheck: {message}"

def run_leveling(ip):
    """
    Chạy leveling - căn chỉnh giường in (bed mesh calibration)
    Quy trình:
    1. Làm nóng nozzle đến 200 độ để nozzle clean
    2. Thực hiện nozzle clean
    3. Hạ nhiệt độ xuống 160 độ
    4. Cân bàn (bed mesh calibration)
    5. Tắt gia nhiệt
    """
    # Script leveling với quy trình đúng: 200 độ -> nozzle clean -> 160 độ -> cân bàn -> tắt gia nhiệt
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
    
    return send_gcode_command(ip, script, timeout=300)

def run_extrude(ip):
    """
    Chạy extrude - đẩy filament ra (load material)
    Tắt nhiệt độ sau khi hoàn thành
    """
    script = """LOAD_MATERIAL
TURN_OFF_HEATERS"""
    return send_gcode_command(ip, script)

def run_retract(ip):
    """
    Chạy retract - rút filament vào (unload material)
    Tắt nhiệt độ sau khi hoàn thành
    """
    script = """QUIT_MATERIAL
TURN_OFF_HEATERS"""
    return send_gcode_command(ip, script)