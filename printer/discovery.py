from concurrent.futures import ThreadPoolExecutor, as_completed
from printer.api import is_printer
import math

def discover_printers(network_prefix, start_ip, end_ip, callback, progress_callback=None):
    discovered = []
    try:
        start = int(start_ip)
        end = int(end_ip)
        if not (0 <= start <= 255 and 0 <= end <= 255 and start <= end):
            raise ValueError("Phạm vi IP không hợp lệ!")
        if not network_prefix.endswith("."):
            network_prefix += "."
            
        total_ips = end - start + 1
        ips = [f"{network_prefix}{i}" for i in range(start, end + 1)]
        
        # Tối ưu: 40 workers - cân bằng giữa tốc độ và độ tin cậy
        max_workers = min(40, max(10, math.ceil(total_ips / 10)))
        
        scanned_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(is_printer, ip): ip for ip in ips}
            for future in as_completed(futures):
                scanned_count += 1
                if progress_callback:
                    progress = (scanned_count / total_ips) * 100
                    progress_callback(progress, scanned_count, total_ips)
                
                ip = futures[future]
                try:
                    if future.result():
                        discovered.append(ip)
                except:
                    pass
                    
    except ValueError as e:
        callback([], str(e))
        return
        
    callback(discovered)