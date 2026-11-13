"""Launch GUI. Does not connect to a camera or serial device automatically."""
import sys

if __name__ == '__main__':
    try:
        from emg_app.gui import main
        main(smoke='--smoke-test' in sys.argv)
    except ImportError as exc:
        print(f'Missing dependency: {exc}\nRun setup.ps1, then launch.ps1. See README.md.')
        raise SystemExit(1)
