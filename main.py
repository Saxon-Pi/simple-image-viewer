"""
QPixmap: 画像データそのもの

QGraphicsScene: 画像などのオブジェクトが存在する仮想的な空間
        ↓ その中に
QGraphicsPixmapItem: Scene 上に存在する画像オブジェクト
        ↓ その Scene を覗く
QGraphicsView: ユーザーが実際に見る、Scene の一部分を画面に表示する窓
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
# QApplication がアプリ全体を管理、QMainWindow が実際のウィンドウ本体
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
)

# モニタとウィンドウのマージン
SCREEN_MARGIN_LEFT = 12
SCREEN_MARGIN_RIGHT = 12
SCREEN_MARGIN_BOTTOM = 36
SCREEN_MARGIN_TOP = 0

# 対応する画像拡張子
SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".gif",
}

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
        initial_image_path = Path(
            "test_image_724-2172.png"
        )
        self.pixmap = QPixmap(
            str(initial_image_path)
        )

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
    
    # 同一ディレクトリの画像一覧を取得する
    def load_image_list(self, image_path):
        image_path = Path(image_path)

        self.image_paths = sorted(
            [
                path
                for path in image_path.parent.iterdir()
                if path.is_file()
                and path.suffix.lower() in SUPPORTED_EXTENSIONS
            ]
        )

        self.current_index = self.image_paths.index(
            image_path
        )
    
    #  初期表示 & 切り替え時に画像を読み込む
    def load_image(self, image_path):
        self.current_image_path = Path(image_path)

        self.pixmap = QPixmap(
            str(self.current_image_path)
        )

        # QGraphicsPixmapItem 自体は作り直さず、中身の Pixmap だけ入れ替える
        self.image_item.setPixmap(
            self.pixmap
        )

        # 新しい画像の中心を回転軸にする
        self.image_item.setTransformOriginPoint(
            self.image_item.boundingRect().center()
        )

        # 画像切り替え時は回転をリセット
        self.rotation_angle = 0
        self.image_item.setRotation(0)

        # 初期表示状態へ戻す
        self.reset_to_initial_view()
    
    # 画像を切り替える (←→ で前後移動、ループなし)
    def show_next_image(self):
        if self.current_index >= len(self.image_paths) - 1:
            return

        self.current_index += 1

        self.load_image(
            self.image_paths[self.current_index]
        )

    def show_previous_image(self):
        if self.current_index <= 0:
            return

        self.current_index -= 1

        self.load_image(
            self.image_paths[self.current_index]
        )
        
    # このアプリが使える最大 Window領域を返す
    def get_available_window_rect(self):
        screen = self.screen()
        rect = screen.availableGeometry()

        return rect.adjusted(
            SCREEN_MARGIN_LEFT,
            SCREEN_MARGIN_TOP,
            -SCREEN_MARGIN_RIGHT,
            -SCREEN_MARGIN_BOTTOM,
        )

    # スクリーンの中央にウィンドウを表示
    def center_window_on_screen(self):
        screen = self.screen()
        available_rect = screen.availableGeometry()

        frame = self.frameGeometry()
        frame.moveCenter(available_rect.center())

        self.move(frame.topLeft())
    
    # マージン有りの最大ウィンドウ（モニタ解像度からマージンを差し引く）
    def expand_window_for_original_view(self):
        screen = self.screen()
        available_rect = screen.availableGeometry()

        margin_left = 12
        margin_right = 12
        margin_bottom = 36

        target_width = (
            available_rect.width()
            - margin_left
            - margin_right
        )

        target_height = (
            available_rect.height()
            - margin_bottom
        )

        # 現在のWindow位置を保存
        current_pos = self.pos()

        # 最大サイズ制限を一旦解除
        self.setMaximumSize(
            16777215,
            16777215,
        )

        # 位置を変えずサイズだけ拡大
        self.resize(
            target_width,
            target_height,
        )

        # 画面外にはみ出した場合だけ位置を補正
        new_x = min(
            current_pos.x(),
            available_rect.right() - target_width,
        )

        new_y = min(
            current_pos.y(),
            available_rect.bottom() - target_height,
        )

        new_x = max(new_x, available_rect.left() + margin_left)
        new_y = max(new_y, available_rect.top())

        self.move(new_x, new_y)
    
    # 現在の画像表示サイズをウィンドウの最大サイズにする（余白をなくす）
    def update_window_size_limits(self):
        image_rect = self.image_item.sceneBoundingRect()

        display_rect = self.view.transform().mapRect(
            image_rect
        )

        image_width = int(display_rect.width())
        image_height = int(display_rect.height())

        extra_width = (
            self.width()
            - self.view.viewport().width()
        )

        extra_height = (
            self.height()
            - self.view.viewport().height()
        )

        # 共通のウィンドウ利用可能領域
        allowed_rect = (
            self.get_available_window_rect()
        )

        max_width = min(
            image_width + extra_width,
            allowed_rect.width(),
        )

        max_height = min(
            image_height + extra_height,
            allowed_rect.height(),
        )

        self.setMaximumSize(
            max_width,
            max_height,
        )
    
    # 左右に90度回転
    def rotate_right(self):
        # 0 -> 90 -> 180 -> 270 -> 0
        self.rotation_angle = (self.rotation_angle + 90) % 360

        # 画像は元のまま、QGraphicsPixmapItem を回転表示する
        self.image_item.setRotation(self.rotation_angle)

        # 回転後の Item全体が View に収まるよう再Fit
        self.update_after_rotation()

    def rotate_left(self):
        self.rotation_angle = (self.rotation_angle - 90) % 360

        self.image_item.setRotation(self.rotation_angle)

        self.update_after_rotation()
    
    # 回転後の画像の理想倍率を計算
    # (横幅・高さの両方について、モニタの利用可能領域に収まる倍率を計算する)
    def calculate_scale_to_screen(self, image_rect):
        allowed_rect = self.get_available_window_rect()

        width_scale = (
            allowed_rect.width() / image_rect.width()
        )

        height_scale = (
            allowed_rect.height() / image_rect.height()
        )

        # 縦横どちらもモニタ内に収まる最大倍率
        return min(
            width_scale,
            height_scale,
            1.0,
        )
    
    def update_after_rotation(self):
        image_rect = self.image_item.sceneBoundingRect()

        # 回転後の画像領域へSceneを更新
        self.scene.setSceneRect(image_rect)

        # 回転後の画像がモニタ内に最大で収まる倍率を計算
        self.current_scale = self.calculate_scale_to_screen(
            image_rect
        )

        # 現在の倍率をそのまま適用
        self.apply_scale()
        # 回転後の画像サイズへWindowを追従
        self.resize_window_to_image()

        # ウィンドウ自体をモニタ中央へ
        QTimer.singleShot(
            0,
            self.center_window_on_screen,
        )

        # 回転前に見ていた位置を回転後のView中央にする
        QTimer.singleShot(
            0,
            lambda: self.view.centerOn(image_rect.center()),
        )

    # Zoom に合わせてウィンドウも伸縮
    def resize_window_to_image(self):
        # 以前のmaximumSizeを解除
        self.setMaximumSize(
            16777215,
            16777215,
        )

        # Scene上の画像サイズを取得
        image_rect = self.image_item.sceneBoundingRect()

        # 現在の View の Transform を考慮して、
        # 画像が画面上で何px になるかを取得
        display_rect = self.view.transform().mapRect(image_rect)

        extra_width = (
            self.width()
            - self.view.viewport().width()
        )

        extra_height = (
            self.height()
            - self.view.viewport().height()
        )

        desired_width = int(
            display_rect.width()
            + extra_width
        )

        desired_height = int(
            display_rect.height()
            + extra_height
        )

        allowed_rect = self.get_available_window_rect()

        target_width = min(
            desired_width,
            allowed_rect.width(),
        )

        target_height = min(
            desired_height,
            allowed_rect.height(),
        )

        # 現在のウィンドウ中心
        current_center = self.frameGeometry().center()

        # まずは現在中心から左右均等に広げる
        new_x = int(
            current_center.x()
            - target_width / 2
        )

        new_y = int(
            current_center.y()
            - target_height / 2
        )

        # 左右が画面外にはみ出さないよう補正
        min_x = allowed_rect.left()
        max_x = (
            allowed_rect.right()
            - target_width
            + 1
        )

        new_x = max(
            min_x,
            min(new_x, max_x),
        )

        # 上下も同様に補正
        min_y = allowed_rect.top()
        max_y = (
            allowed_rect.bottom()
            - target_height
            + 1
        )

        new_y = max(
            min_y,
            min(new_y, max_y),
        )

        # サイズと位置を同時に変更
        self.setGeometry(
            new_x,
            new_y,
            target_width,
            target_height,
        )

        # resize後のWindow状態を基準に制限を設定
        self.update_window_size_limits()
    
    # 画像の初期表示 (高解像度なら画面高さを上限に縮小表示)
    def reset_to_initial_view(self):
        image_rect = self.image_item.sceneBoundingRect()

        # モニタ端のマージンを考慮した利用可能領域
        available_rect = self.get_available_window_rect()

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

        QTimer.singleShot(
            0,
            lambda: self.view.centerOn(image_rect.center()),
        )

        QTimer.singleShot(
            0,
            self.center_window_on_screen,
        )
    
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
        self.resize_window_to_image()

        QTimer.singleShot(
            0,
            # クリックした画像位置を View中央へ
            lambda: self.view.centerOn(scene_pos),
        )
    
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
        # "→" : show_next_image()
        # "←" : show_previous_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()
        elif event.key() == Qt.Key_Left:
            self.show_previous_image()
        else:
            super().keyPressEvent(event)
    

class ImageView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        self.is_panning = False
        self.last_mouse_pos = None
    
    def restore_zoom_anchor(self, scene_pos_before, global_pos):
        # ウィンドウサイズ変更後のマウスポインタ位置を View座標へ変換
        view_pos_after = self.viewport().mapFromGlobal(global_pos)

        # 現在その位置が指している Scene座標
        scene_pos_after = self.mapToScene(view_pos_after)

        # Zoom 前後で生じた Scene座標のズレ
        delta = scene_pos_before - scene_pos_after

        # 現在の View中央
        current_center = self.mapToScene(
            self.viewport().rect().center()
        )

        # ズレた分だけ View中央を補正
        self.centerOn(
            current_center + delta
        )

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

        # Zoom前に、マウスポインタが指している Scene座標を保存
        view_pos = event.position().toPoint()
        scene_pos_before = self.mapToScene(view_pos)

        # ウィンドウリサイズ後も同じ画面上のマウス位置を取得できるようにする
        global_pos = event.globalPosition().toPoint()

        if event.angleDelta().y() > 0:
            self.window().zoom_in()
        elif event.angleDelta().y() < 0:
            self.window().zoom_out()

        # resize処理完了後にポインタ位置を補正
        QTimer.singleShot(
            0,
            lambda: self.restore_zoom_anchor(
                scene_pos_before,
                global_pos,
            ),
        )

        # QGraphicsView 標準のスクロール処理には渡さない
        event.accept()

    def mousePressEvent(self, event):
        # マウスホイールクリック: toggle_original_scale()
        if event.button() == Qt.MiddleButton:
            view_pos = event.position().toPoint()

            self.window().toggle_original_scale(view_pos)

            event.accept()
            return

        # 右クリック開始時にパンモードに移行
        if event.button() == Qt.RightButton:
            self.is_panning = True
            self.last_mouse_pos = event.position().toPoint()

            event.accept()
            return

        super().mousePressEvent(event)
    
    # 右クリック押下 + マウス移動中に Scene の表示位置をずらす
    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_mouse_pos is not None:
            current_pos = event.position().toPoint()

            delta = current_pos - self.last_mouse_pos

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )

            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )

            self.last_mouse_pos = current_pos

            event.accept()
            return

        super().mouseMoveEvent(event)
    
    # 右クリックを離すとパンモード終了
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.is_panning = False
            self.last_mouse_pos = None

            event.accept()
            return

        super().mouseReleaseEvent(event)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # Window表示後に初期画像サイズを計算する
    QTimer.singleShot(
        0,
        window.reset_to_initial_view,
    )

    # app.exec() でウィンドウを開いたままユーザー操作を待ち続けるイベントループを開始する
    # -> app.exec()でイベントループ開始 → ウィンドウを閉じる → app.exec()が終了 → sys.exit()でPythonプログラムを終了
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
