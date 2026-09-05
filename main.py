import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
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

        # 現在の表示上の回転角度
        self.rotation_angle = 0

        # QMainWindow の中央コンテンツを image_label にする
        self.setCentralWidget(self.image_label)

        # Fitモード (画像の元サイズで表示) のフラグ
        self.is_fit_mode = True
        # 画像の縮尺
        self.zoom_factor = 1.0

        self.update_image()
    
    def update_image(self):
        # QTransformで回転
        transform = QTransform()
        transform.rotate(self.rotation_angle)

        # 回転後の画像
        rotated_pixmap = self.pixmap.transformed(
            transform,
            Qt.SmoothTransformation,
        )

        # 元画像のアスペクト比を維持しながらウィンドウ内に収める
        scaled_pixmap = rotated_pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        # Zoomモードなら、このFitサイズを基準に倍率を掛ける
        if self.is_fit_mode:
            display_pixmap = scaled_pixmap
        else:
            zoom_width = int(scaled_pixmap.width() * self.zoom_factor)
            zoom_height = int(scaled_pixmap.height() * self.zoom_factor)

            display_pixmap = rotated_pixmap.scaled(
                zoom_width,
                zoom_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

        # QLabel による画像表示
        self.image_label.setPixmap(display_pixmap)

    # ウィンドウサイズが変更されたときに Qt から自動的に呼ばれるメソッド
    def resizeEvent(self, event):
        self.update_image()
        super().resizeEvent(event)
    
    # 左右に90度回転
    def rotate_right(self):
        # 0 -> 90 -> 180 -> 270 -> 0
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.update_image()

    def rotate_left(self):
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.update_image()

    # 拡大・縮小・縮尺リセット
    def zoom_in(self):
        self.is_fit_mode = False
        self.zoom_factor += 0.2
        self.update_image()

    def zoom_out(self):
        self.is_fit_mode = False
        self.zoom_factor = max(0.1, self.zoom_factor - 0.2)
        self.update_image()

    def fit_to_window(self):
        self.is_fit_mode = True
        self.zoom_factor = 1.0
        self.update_image()

    # キー入力
    def keyPressEvent(self, event):
        # "R": rotate_right()
        # "Shift + R": rotate_left()
        if event.key() == Qt.Key_R:
            if event.modifiers() & Qt.ShiftModifier:
                self.rotate_left()
            else:
                self.rotate_right()
        # "+" or "=": zoom_in()
        # "-": zoom_out()
        # "0": fit_to_window()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key_0:
            self.fit_to_window()
        else:
            super().keyPressEvent(event)
    
    # マウスホイール操作
    def wheelEvent(self, event):
        # 上方向にスクロール: zoom_in()
        # 下方向にスクロール: zoom_out()
        if event.angleDelta().y() > 0:
            self.zoom_in()
        elif event.angleDelta().y() < 0:
            self.zoom_out()


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
