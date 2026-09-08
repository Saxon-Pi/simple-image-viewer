"""
QPixmap: 画像データそのもの

QGraphicsScene: 画像などのオブジェクトが存在する仮想的な空間
        ↓ その中に
QGraphicsPixmapItem: Scene 上に存在する画像オブジェクト
        ↓ その Scene を覗く
QGraphicsView: ユーザーが実際に見る、Scene の一部分を画面に表示する窓
"""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
# QApplication がアプリ全体を管理、QMainWindow が実際のウィンドウ本体
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Simple Image Viewer")
        self.resize(800, 600)

        self.rotation_angle = 0 # 現在の表示上の回転角度
        self.is_fit_mode = True # Fitモード（画像全体をView内に収めて表示）のフラグ
        self.zoom_factor = 1.0  # 画像の縮尺

        # 画像を表示する Scene
        self.scene = QGraphicsScene(self)

        # Scene を表示する View
        self.view = ImageView(self.scene)

        # スクロールバーを出さない
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 画像を読み込んで Qt が画面表示できる画像データに変換する
        self.pixmap = QPixmap("nekochan.webp")
        #self.pixmap = QPixmap("test_image_724-2172.png")

        # Pixmap を Scene 上に配置する Item に変換
        self.image_item = QGraphicsPixmapItem(self.pixmap)

        # 画像の中心を回転軸にする
        self.image_item.setTransformOriginPoint(
            self.image_item.boundingRect().center()
        )

        # Scene に画像を追加
        self.scene.addItem(self.image_item)

        # QMainWindow の中央コンテンツを QGraphicsView にする
        self.setCentralWidget(self.view)

        # 画像の初期表示
        self.reset_to_initial_view()
    
    # 画像の縮尺変更 (画像自体のサイズは変更せず、View側の倍率を変更する)
    def fit_to_window(self):
        self.is_fit_mode = True
        self.zoom_factor = 1.0

        # Zoom すると QGraphicsView 内部に「1.2倍」のような Transform が残るため
        # View の倍率を一度リセットする
        self.view.resetTransform()

        # 回転後の画像がScene上で占める領域を取得
        image_rect = self.image_item.sceneBoundingRect()

        # Sceneの範囲を回転後の画像に合わせる
        self.scene.setSceneRect(image_rect)

        # Scene全体がView内に収まるようにする
        self.view.fitInView(
            image_rect,
            Qt.KeepAspectRatio,
        )
    
    # 左右に90度回転
    def rotate_right(self):
        # 0 -> 90 -> 180 -> 270 -> 0
        self.rotation_angle = (self.rotation_angle + 90) % 360
        # 画像は元のまま、QGraphicsPixmapItem を回転表示する
        self.image_item.setRotation(self.rotation_angle)
        # 回転後の Item全体が View に収まるよう再Fit
        self.fit_to_window()

    def rotate_left(self):
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.image_item.setRotation(self.rotation_angle)
        self.fit_to_window()

    # Zoom に合わせてウィンドウも伸縮
    def resize_window_to_image(self):
        # Scene上の画像サイズを取得
        image_rect = self.image_item.sceneBoundingRect()

        # 現在の View の Transform を考慮して、
        # 画像が画面上で何px になるかを取得
        display_rect = self.view.transform().mapRect(image_rect)

        image_width = int(display_rect.width())
        image_height = int(display_rect.height())

        # QMainWindow全体と、実際にSceneを表示しているviewportとの差分
        extra_width = self.width() - self.view.viewport().width()
        extra_height = self.height() - self.view.viewport().height()

        self.resize(
            image_width + extra_width,
            image_height + extra_height,
        )
    
    # 画像の初期表示 (高解像度なら画面高さを上限に縮小表示)
    def reset_to_initial_view(self):
        self.zoom_factor = 1.0
        self.view.resetTransform()

        image_rect = self.image_item.sceneBoundingRect()

        # Viewerが現在表示されているモニタを取得
        screen = self.screen()
        available_rect = screen.availableGeometry()

        # debug
        print("screen:", screen.name())
        print(
            "available:",
            available_rect.width(),
            available_rect.height(),
        )

        print(
            "window:",
            self.width(),
            self.height(),
        )

        print(
            "viewport:",
            self.view.viewport().width(),
            self.view.viewport().height(),
        )

        transform = self.view.transform()

        print("scale X:", transform.m11())
        print("scale Y:", transform.m22())
        print("---")

        image_height = image_rect.height()
        max_height = available_rect.height()

        if image_height > max_height:
            scale_factor = max_height / image_height

            self.view.scale(
                scale_factor,
                scale_factor,
            )

        self.scene.setSceneRect(image_rect)
        self.resize_window_to_image()

    # 拡大・縮小・縮尺リセット
    def zoom_in(self):
        self.is_fit_mode = False
        self.zoom_factor += 0.2
        self.apply_zoom()
        self.resize_window_to_image()

    def zoom_out(self):
        self.is_fit_mode = False
        self.zoom_factor = max(0.1, self.zoom_factor - 0.2)
        self.apply_zoom()
        self.resize_window_to_image()
    
    def apply_zoom(self):
        # 現在の Fit表示を 100% の基準とする
        self.view.resetTransform()

        image_rect = self.image_item.sceneBoundingRect()
        self.view.fitInView(
            image_rect,
            Qt.KeepAspectRatio,
        )

        # Fit表示を基準に Zoom倍率を掛ける
        self.view.scale(
            self.zoom_factor,
            self.zoom_factor,
        )
    
    # 画像を元の縮尺に戻す
    def reset_to_original_size(self):
        self.is_fit_mode = False
        self.zoom_factor = 1.0

        # View の Transform をリセット
        self.view.resetTransform()

        # 画像の表示領域を更新
        image_rect = self.image_item.sceneBoundingRect()
        self.scene.setSceneRect(image_rect)

        # オリジナルサイズに合わせて Window も変更
        self.resize_window_to_image()
        
    # # ウィンドウサイズが変更されたときに Qt から自動的に呼ばれるメソッド
    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    
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
        # "0": reset_to_original_size()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key_0:
            self.reset_to_initial_view()
        else:
            super().keyPressEvent(event)
    

class ImageView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

    # ウィンドウリサイズ時、現在の View中央が指している Scene上の位置を維持する    
    def resizeEvent(self, event):
        old_size = event.oldSize()

        # 初回など oldSize が無効な場合は通常処理
        if old_size.isValid():
            # リサイズ前の View中央
            old_center_view = old_size.width() / 2, old_size.height() / 2

            # リサイズ前の中央が指していた Scene座標を保存
            old_center_scene = self.mapToScene(
                int(old_center_view[0]),
                int(old_center_view[1]),
            )

        else:
            old_center_scene = None

        # 通常の QGraphicsView リサイズ処理
        super().resizeEvent(event)

        # リサイズ後も同じ Scene座標を中央にする
        if old_center_scene is not None:
            self.centerOn(old_center_scene)

    def wheelEvent(self, event):
        # マウスホイール操作は Zoom専用にする
        # 上方向にスクロール: zoom_in()
        # 下方向にスクロール: zoom_out()
        if event.angleDelta().y() > 0:
            self.window().zoom_in()
        elif event.angleDelta().y() < 0:
            self.window().zoom_out()

        # QGraphicsView 標準のスクロール処理には渡さない
        event.accept()


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
