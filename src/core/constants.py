import os
import sys

# Company Info
COMPANY_NAME = "GOT KEY'D REALTY"
COMPANY_ADDRESS = "22260 Garrison St, Dearborn, MI 48124"
COMPANY_PHONE = "(313) 228-5710"

# PDF colors as RGB tuples (used by pdf_generator.py — NOT UI colors)
NAVY_RGB = (27, 58, 92)
BLUE_RGB = (46, 117, 182)
DARK_TEXT_RGB = (45, 45, 45)
GRAY_TEXT_RGB = (102, 102, 102)
LIGHT_BG_RGB = (244, 247, 250)
ROW_ALT_RGB = (232, 238, 228)
WHITE_RGB = (255, 255, 255)

# App info
APP_NAME = "Got Key'd Commission Tracker"
APP_VERSION = "1.0.0"


def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Go up from src/core/ to project root
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def get_data_dir() -> str:
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.path.join(os.path.expanduser('~'), '.local', 'share')
    data_dir = os.path.join(base, 'GotKeydRealty')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_output_dir() -> str:
    """User-visible output directory for invoices and 1099s (Documents folder)."""
    docs = os.path.join(os.path.expanduser('~'), 'Documents')
    out_dir = os.path.join(docs, 'GotKeyd Realty')
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


DB_PATH = os.path.join(get_data_dir(), 'commission_tracker.db')
LOGO_PATH = get_resource_path(os.path.join('assets', 'logo.png'))
