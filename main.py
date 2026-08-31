import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
# QApplication がアプリ全体を管理、QMainWindow が実際のウィンドウ本体
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QSizePolicy,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Simple Image Viewer")
        self.resize(800, 600)

        self.image_label = QLabel()

        # 画像サイズがウィンドウサイズを制約しないようにする
        self.image_label.setMinimumSize(1, 1)
        self.image_label.setSizePolicy(
            QSizePolicy.Ignored,
            QSizePolicy.Ignored,
        )

        # 画像が表示領域より小さい場合、ウィンドウ中央に配置する
        self.image_label.setAlignment(Qt.AlignCenter)

        # webp を読み込んで Qt が画面表示できる画像データに変換する
        self.pixmap = QPixmap("nekochan.webp")

        # QMainWindow の中央コンテンツを image_label にする
        self.setCentralWidget(self.image_label)

        self.update_image()
    
    def update_image(self):
        # 元画像のアスペクト比を維持しながらウィンドウ内に収める
        scaled_pixmap = self.pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        # QLabel による画像表示
        self.image_label.setPixmap(scaled_pixmap)

    # ウィンドウサイズが変更されたときに Qt から自動的に呼ばれるメソッド
    def resizeEvent(self, event):
        self.update_image()
        super().resizeEvent(event)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
