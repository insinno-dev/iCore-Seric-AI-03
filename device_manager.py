"""Device management and validation"""
import csv
import os
from typing import Optional, Dict, List
from pathlib import Path
from difflib import SequenceMatcher

class DeviceManager:
    """Manages device validation against device database from CSV"""
    
    def __init__(self):
        """Initialize device manager and load devices from CSV."""
        self.devices = self._load_devices_from_csv()
        self.device_index = self._build_index()
    
    def _load_devices_from_csv(self) -> Dict[str, Dict]:
        """Load device list from devices.csv file."""
        devices = {}
        csv_path = Path(__file__).parent / "devices.csv"
        
        if not csv_path.exists():
            print(f"⚠️ Warning: {csv_path} not found. Using empty device list.")
            return devices
        
        try:
            # Try different encodings
            encodings = ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(csv_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    print(f"[OK] CSV opened with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                print(f"[ERROR] Could not read {csv_path} with any encoding")
                return devices
            
            # Parse CSV with custom handling for malformed lines
            import io
            lines = content.strip().split('\n')
            headers = lines[0].split(',')
            
            for line_idx, line in enumerate(lines[1:], 1):
                # Remove outer quotes if the entire line is quoted
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    line = line[1:-1]
                
                # Split by comma but be careful with quoted fields
                # Simple approach: just split by comma
                parts = line.split(',')
                
                if len(parts) >= 2:
                    try:
                        # Clean up each part
                        clean_parts = []
                        for part in parts:
                            p = part.strip().strip('"')
                            clean_parts.append(p)
                        
                        # Map to headers
                        row = {}
                        for i, header in enumerate(headers):
                            row[header.strip()] = clean_parts[i] if i < len(clean_parts) else ''
                        
                        # Extract model (primary key)
                        model = row.get('model', '').strip()
                        if model:
                            key = model.lower()
                            brand = row.get('brand', '').strip()
                            device_type = row.get('type', '').strip()
                            devices[key] = {
                                "brand": brand,
                                "model": model,
                                "type": device_type,
                                "device_type": device_type,
                                "description": row.get('description', '').strip(),
                                "manufacturer_code": row.get('manufacturer-code', '').strip(),
                                "full_name": f"{brand} {device_type} {model}".strip()
                            }
                    except Exception as row_err:
                        # Skip problematic rows
                        continue
            
            print(f"[OK] Loaded {len(devices)} devices from {csv_path}")
            return devices
        except Exception as e:
            print(f"[ERROR] Error loading devices.csv: {e}")
            return devices
    
    def _build_index(self) -> Dict[str, str]:
        """Build fuzzy matching index for device names"""
        index = {}
        for key, device in self.devices.items():
            # Index by model number
            index[device["model"].lower()] = key
            # Index by full name
            index[device["full_name"].lower()] = key
            # Index by brand + model
            brand_model = f"{device['brand']} {device['model']}".lower()
            index[brand_model] = key
            # Index by brand + type
            brand_type = f"{device['brand']} {device['type']}".lower()
            index[brand_type] = key
        return index
    
    def find_device(self, user_input: str) -> Dict:
        """
        Find device in database with fuzzy matching
        Returns: {"is_known": bool, "device_model": str, "device_info": dict}
        """
        normalized = user_input.lower().strip()
        
        # Exact match attempt
        if normalized in self.device_index:
            key = self.device_index[normalized]
            device = self.devices[key]
            return {
                "is_known": True,
                "device_key": key,
                "device_model": device["model"],
                "device_info": device
            }
        
        # Substring match attempt
        for idx_key, db_key in self.device_index.items():
            if normalized in idx_key or idx_key in normalized:
                device = self.devices[db_key]
                return {
                    "is_known": True,
                    "device_key": db_key,
                    "device_model": device["model"],
                    "device_info": device
                }
        
        # Fuzzy matching (find closest match)
        best_match = None
        best_score = 0.6  # Minimum similarity threshold
        
        for device_key, device in self.devices.items():
            score = SequenceMatcher(None, normalized, device_key).ratio()
            if score > best_score:
                best_score = score
                best_match = (device_key, device)
        
        if best_match:
            device_key, device = best_match
            return {
                "is_known": True,
                "device_key": device_key,
                "device_model": device["model"],
                "device_info": device,
                "match_confidence": f"{best_score:.0%}"
            }
        
        # No match found
        return {
            "is_known": False,
            "device_key": None,
            "device_model": None,
            "device_info": None,
            "user_input": user_input
        }
    
    def get_device_list(self) -> List[str]:
        """Return list of known devices for display"""
        return [
            device["full_name"] 
            for device in self.devices.values()
        ]
    
    def validate_device(self, device_key: str) -> bool:
        """Check if device exists"""
        return device_key in self.DEVICE_DATABASE
