import sys
import os

# Ensure the src directory is on the path
_base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_base, 'src'))

from app import App


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == '__main__':
    main()
