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
        self.initial_scale = 1.0 # 初期の画像スケール
        self.current_scale = 1.0 # 現在の画像スケール

        # 画像を表示する Scene
        self.scene = QGraphicsScene(self)

        # Scene を表示する View
        self.view = ImageView(self.scene)

        # スクロールバーを出さない
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 画像を読み込んで Qt が画面表示できる画像データに変換する
        #self.pixmap = QPixmap("nekochan.webp")
        self.pixmap = QPixmap("test_image_724-2172.png")

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
        image_rect = self.image_item.sceneBoundingRect()

        screen = self.screen()
        available_rect = screen.availableGeometry()

        # 画像の解像度が画面の解像度を超える場合、画面の高さを上限に縮小表示
        if image_rect.height() > available_rect.height():
            self.initial_scale = (
                available_rect.height() / image_rect.height()
            )
        else:
            self.initial_scale = 1.0

        self.current_scale = self.initial_scale

        self.scene.setSceneRect(image_rect)
        self.apply_scale()
        self.resize_window_to_image()

        self.view.centerOn(image_rect.center())
    
    def apply_scale(self):
        self.view.resetTransform()
        self.view.scale(
            self.current_scale,
            self.current_scale,
        )

    # 拡大・縮小・縮尺リセット
    def zoom_in(self):
        self.current_scale += 0.2
        self.apply_scale()
        self.resize_window_to_image()

    def zoom_out(self):
        self.current_scale = max(
            0.1,
            self.current_scale - 0.2,
        )
        self.apply_scale()
        self.resize_window_to_image()
    
    # マウスホイールクリック時に 画像の100%表示 → 初期表示 をトグル
    def toggle_original_scale(self, view_pos):
        # クリックした場所を Scene座標へ変換
        scene_pos = self.view.mapToScene(view_pos)

        # 現在100%表示なら初期表示へ戻す
        if abs(self.current_scale - 1.0) < 0.001:
            self.reset_to_initial_view()
            return

        # 100%表示へ
        self.current_scale = 1.0
        self.apply_scale()

        # ウィンドウ最大化
        self.showMaximized()

        # クリックした画像位置を View中央へ
        self.view.centerOn(scene_pos)
    
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
    
    def mousePressEvent(self, event):
        # マウスホイールクリック: toggle_original_scale()
        if event.button() == Qt.MiddleButton:
            view_pos = event.position().toPoint()

            self.window().toggle_original_scale(view_pos)

            event.accept()
            return

        super().mousePressEvent(event)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
