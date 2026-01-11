"""
Module quản lý settings của ứng dụng
- Window size & position
- Printer profiles
- Statistics
"""
import json
import os
from datetime import datetime
from pathlib import Path

class AppSettings:
    def __init__(self):
        # Thư mục lưu settings - Dễ tìm và backup
        self.app_data_dir = Path("C:/Creality/Data")
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.settings_file = self.app_data_dir / "settings.json"
        self.statistics_file = self.app_data_dir / "statistics.json"
        
        # Load settings
        self.settings = self._load_json(self.settings_file, self._default_settings())
        self.statistics = self._load_json(self.statistics_file, self._default_statistics())
    
    def _default_settings(self):
        """Settings mặc định"""
        return {
            "window": {
                "width": 1200,
                "height": 800,
                "x": None,  # None = center screen
                "y": None,
                "maximized": False
            },
            "last_network_prefix": "192.168.1.",
            "auto_verify": True,
            "verify_wait_time": 5
        }
    
    def _default_statistics(self):
        """Statistics mặc định"""
        return {
            "total_prints": 0,
            "successful_prints": 0,
            "failed_prints": 0,
            "total_files_uploaded": 0,
            "total_files_deleted": 0,
            "print_history": [],  # List of {date, file, printers, status}
            "first_use_date": datetime.now().isoformat(),
            "last_use_date": datetime.now().isoformat()
        }
    
    def _load_json(self, file_path, default_value):
        """Load JSON file"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return default_value
    
    def _save_json(self, file_path, data):
        """Save JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving {file_path}: {e}")
            return False
    
    # ===== WINDOW SETTINGS =====
    
    def save_window_geometry(self, width, height, x, y, maximized=False):
        """Lưu kích thước và vị trí cửa sổ"""
        self.settings["window"] = {
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "maximized": maximized
        }
        self._save_json(self.settings_file, self.settings)
    
    def get_window_geometry(self):
        """Lấy kích thước và vị trí cửa sổ đã lưu"""
        return self.settings["window"]
    
    # ===== STATISTICS =====
    
    def record_print(self, file_name, printer_ips, success_count, failed_count):
        """Ghi nhận một lần in"""
        self.statistics["total_prints"] += len(printer_ips)
        self.statistics["successful_prints"] += success_count
        self.statistics["failed_prints"] += failed_count
        self.statistics["total_files_uploaded"] += success_count
        self.statistics["last_use_date"] = datetime.now().isoformat()
        
        # Thêm vào history (giới hạn 100 records gần nhất)
        history_entry = {
            "date": datetime.now().isoformat(),
            "file": file_name,
            "total_printers": len(printer_ips),
            "success": success_count,
            "failed": failed_count
        }
        self.statistics["print_history"].insert(0, history_entry)
        self.statistics["print_history"] = self.statistics["print_history"][:100]
        
        self._save_json(self.statistics_file, self.statistics)
    
    def record_files_deleted(self, count):
        """Ghi nhận số file đã xóa"""
        self.statistics["total_files_deleted"] += count
        self.statistics["last_use_date"] = datetime.now().isoformat()
        self._save_json(self.statistics_file, self.statistics)
    
    def get_statistics(self):
        """Lấy thống kê"""
        return self.statistics
    
    def get_print_history(self, limit=50):
        """Lấy lịch sử in"""
        return self.statistics["print_history"][:limit]
    
    def reset_statistics(self):
        """Reset thống kê"""
        self.statistics = self._default_statistics()
        self._save_json(self.statistics_file, self.statistics)
        return True
    
    # ===== GENERAL =====
    
    def update_last_use(self):
        """Cập nhật thời gian sử dụng cuối"""
        self.statistics["last_use_date"] = datetime.now().isoformat()
        self._save_json(self.statistics_file, self.statistics)


# Singleton instance
_app_settings_instance = None

def get_app_settings():
    """Get singleton instance of AppSettings"""
    global _app_settings_instance
    if _app_settings_instance is None:
        _app_settings_instance = AppSettings()
    return _app_settings_instance

