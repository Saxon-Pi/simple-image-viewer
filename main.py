import sys

# QApplication がアプリ全体を管理、QMainWindow が実際のウィンドウ本体
from PySide6.QtWidgets import QApplication, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Simple Image Viewer")
        self.resize(800, 600)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
