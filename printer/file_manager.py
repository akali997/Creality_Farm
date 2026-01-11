import requests
import os
from config.settings import session, GCODE_FOLDER

def get_file_list(ip):
    try:
        url = f"http://{ip}:7125/server/files/list?folder={GCODE_FOLDER}"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            files = response.json().get("result", [])
            return [file["path"] for file in files if isinstance(file, dict) and "path" in file and file["path"].endswith(".gcode")]
        return []
    except:
        return []

def download_file(ip, filename, save_path):
    try:
        url_download = f"http://{ip}:7125/server/files/gcodes/{filename}"
        response = session.get(url_download, timeout=10)
        if response.status_code == 200:
            file_path = os.path.join(save_path, f"{ip}_{filename}")
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True, f"Đã tải {filename} từ {ip} về {file_path}."
        return False, f"Lỗi HTTP {response.status_code} khi tải {filename} từ {ip}."
    except Exception as e:
        return False, f"Lỗi: {str(e)} khi tải {filename} từ {ip}."

def delete_file(ip, filename):
    try:
        url = f"http://{ip}:7125/server/files/gcodes/{filename}"
        response = session.delete(url, timeout=10)
        if response.status_code in (200, 204):
            return True, f"Đã xóa file {filename} trên máy {ip}."
        return False, f"Lỗi HTTP {response.status_code} khi xóa file {filename} trên máy {ip}."
    except Exception as e:
        return False, f"Lỗi: {str(e)} khi xóa file {filename} trên máy {ip}."

def get_last_printed_file(ip):
    try:
        url = f"http://{ip}:7125/server/files/list?folder={GCODE_FOLDER}"
        response = session.get(url, timeout=2)
        if response.status_code == 200:
            files = response.json().get("result", [])
            gcode_files = [file for file in files if isinstance(file, dict) and "path" in file and file["path"].endswith(".gcode")]
            if not gcode_files:
                return None
            latest_file = max(gcode_files, key=lambda x: x.get("modified", 0))
            return latest_file["path"]
        return None
    except Exception as e:
        return None