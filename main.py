import sys
import traceback
from ui.theme import apply_theme, ThemeMode
from utils.logger import app_logger, log_startup


def run_application():
    log_startup()
    app_logger.info(f'Python: {sys.version}')
    try:
        apply_theme(ThemeMode.DARK)
        from ui.main_window import MainWindow
        app = MainWindow()
        app.protocol('WM_DELETE_WINDOW', app.on_close)
        app.mainloop()
    except Exception as e:
        app_logger.critical(f'Fatal error: {e}')
        app_logger.critical(traceback.format_exc())
        raise


if __name__ == '__main__':
    run_application()
