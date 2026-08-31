import sys

from PySide6.QtGui import QPixmap
# QApplication がアプリ全体を管理、QMainWindow が実際のウィンドウ本体
from PySide6.QtWidgets import QApplication, QMainWindow,  QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Simple Image Viewer")
        self.resize(800, 600)

        image_label = QLabel()

        # webp を読み込んで Qt が画面表示できる画像データに変換する
        pixmap = QPixmap("nekochan.webp")
        # QLabel による画像表示
        image_label.setPixmap(pixmap)

        # QMainWindow の中央コンテンツを image_label にする
        self.setCentralWidget(image_label)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
