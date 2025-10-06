"""
Moduł preferences.py - Zarządzanie preferencjami aplikacji.

Zawiera klasę PreferencesManager do obsługi zapisywania i wczytywania
ustawień użytkownika oraz dialogów konfiguracyjnych.
"""

import os
import json


if hasattr(os.sys, 'frozen') and os.sys.frozen:
    BASE_DIR = os.path.dirname(os.sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class PreferencesManager:
    """Zarządza preferencjami programu i dialogów, zapisuje/odczytuje z pliku preferences.txt"""
    
    def __init__(self, filepath="preferences.txt"):
        self.filepath = os.path.join(BASE_DIR, filepath)
        self.preferences = {}
        self.defaults = {
            # Preferencje globalne
            'default_save_path': '',
            'default_read_path': '',
            'last_open_path': '',
            'last_save_path': '',
            'thumbnail_quality': 'Średnia',
            'confirm_delete': 'False',
            'export_image_dpi': '300',
            
            # PageCropResizeDialog
            'PageCropResizeDialog.crop_mode': 'nocrop',
            'PageCropResizeDialog.margin_top': '10',
            'PageCropResizeDialog.margin_bottom': '10',
            'PageCropResizeDialog.margin_left': '10',
            'PageCropResizeDialog.margin_right': '10',
            'PageCropResizeDialog.resize_mode': 'noresize',
            'PageCropResizeDialog.target_format': 'A4',
            'PageCropResizeDialog.custom_width': '',
            'PageCropResizeDialog.custom_height': '',
            'PageCropResizeDialog.position_mode': 'center',
            'PageCropResizeDialog.offset_x': '0',
            'PageCropResizeDialog.offset_y': '0',
            
            # PageNumberingDialog
            'PageNumberingDialog.margin_left': '35',
            'PageNumberingDialog.margin_right': '25',
            'PageNumberingDialog.margin_vertical_mm': '15',
            'PageNumberingDialog.vertical_pos': 'dol',
            'PageNumberingDialog.alignment': 'prawa',
            'PageNumberingDialog.mode': 'normalna',
            'PageNumberingDialog.start_page': '1',
            'PageNumberingDialog.start_number': '1',
            'PageNumberingDialog.font_name': 'Times-Roman',
            'PageNumberingDialog.font_size': '12',
            'PageNumberingDialog.mirror_margins': 'False',
            'PageNumberingDialog.format_type': 'simple',
            
            # ShiftContentDialog
            'ShiftContentDialog.x_direction': 'P',
            'ShiftContentDialog.y_direction': 'G',
            'ShiftContentDialog.x_value': '0',
            'ShiftContentDialog.y_value': '0',
            
            # PageNumberMarginDialog
            'PageNumberMarginDialog.top_margin': '20',
            'PageNumberMarginDialog.bottom_margin': '20',
            
            # MergePageGridDialog
            'MergePageGridDialog.sheet_format': 'A4',
            'MergePageGridDialog.orientation': 'Pionowa',
            'MergePageGridDialog.margin_top_mm': '5',
            'MergePageGridDialog.margin_bottom_mm': '5',
            'MergePageGridDialog.margin_left_mm': '5',
            'MergePageGridDialog.margin_right_mm': '5',
            'MergePageGridDialog.spacing_x_mm': '10',
            'MergePageGridDialog.spacing_y_mm': '10',
            'MergePageGridDialog.dpi_var': '300',
            
            # EnhancedPageRangeDialog
            'EnhancedPageRangeDialog.last_range': '',
            
            # ImageImportSettingsDialog
            'ImageImportSettingsDialog.target_format': 'A4',
            'ImageImportSettingsDialog.orientation': 'auto',
            'ImageImportSettingsDialog.margin_mm': '10',
            'ImageImportSettingsDialog.scaling_mode': 'DOPASUJ',
            'ImageImportSettingsDialog.alignment_mode': 'SRODEK',
            'ImageImportSettingsDialog.scale_factor': '100.0',
            'ImageImportSettingsDialog.page_orientation': 'PIONOWO',
            'ImageImportSettingsDialog.custom_width': '',
            'ImageImportSettingsDialog.custom_height': '',
            'ImageImportSettingsDialog.keep_ratio': 'True',
        }
        self.load_preferences()
    
    def load_preferences(self):
        """Wczytuje preferencje z pliku"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line:
                            key, value = line.split('=', 1)
                            self.preferences[key.strip()] = value.strip()
            except Exception as e:
                print(f"Błąd wczytywania preferencji: {e}")
    
    def save_preferences(self):
        """Zapisuje preferencje do pliku"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                for key, value in sorted(self.preferences.items()):
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"Błąd zapisywania preferencji: {e}")
    
    def get(self, key, default=None):
        """Pobiera wartość preferencji lub wartość domyślną"""
        if key in self.preferences:
            return self.preferences[key]
        elif key in self.defaults:
            return self.defaults[key]
        else:
            return default
    
    def set(self, key, value):
        """Ustawia wartość preferencji"""
        self.preferences[key] = str(value)
        self.save_preferences()
    
    def get_profile(self, profile_key):
        """Pobiera profil (JSON) z preferencji"""
        profile_str = self.get(profile_key, '{}')
        try:
            return json.loads(profile_str)
        except json.JSONDecodeError:
            return {}
    
    def set_profile(self, profile_key, profile_dict):
        """Zapisuje profil (JSON) do preferencji"""
        profile_str = json.dumps(profile_dict)
        self.set(profile_key, profile_str)
    
    def get_profiles(self, prefix):
        """Pobiera wszystkie profile z danym prefiksem"""
        profiles = {}
        for key, value in self.preferences.items():
            if key.startswith(prefix + '.'):
                profile_name = key[len(prefix) + 1:]
                try:
                    profiles[profile_name] = json.loads(value)
                except json.JSONDecodeError:
                    pass
        return profiles
    
    def delete_profile(self, profile_key):
        """Usuwa profil z preferencji"""
        if profile_key in self.preferences:
            del self.preferences[profile_key]
            self.save_preferences()
