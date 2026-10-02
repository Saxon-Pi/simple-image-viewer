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
from PySide6.QtGui import QPainter, QPixmap
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
    def __init__(self, initial_image_path):
        super().__init__()

        # 入力チェック
        if not initial_image_path.exists():
            print(f"File not found: {initial_image_path}")
            sys.exit(1)

        if initial_image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"Unsupported image format: {initial_image_path.suffix}")
            sys.exit(1)

        self.setWindowTitle("Simple Image Viewer")
        self.resize(800, 600)

        self.rotation_angle = 0 # 現在の表示上の回転角度
        self.initial_scale = 1.0 # 初期の画像スケール
        self.current_scale = 1.0 # 現在の画像スケール

        # 画像を表示する Scene
        self.scene = QGraphicsScene(self)

        # Scene を表示する View
        self.view = ImageView(self.scene)

        # 画像の拡大・縮小時に高品質な補間を使用
        self.view.setRenderHint(
            QPainter.SmoothPixmapTransform,
            True,
        )

        # キーボード入力は MainWindow 側で処理する
        self.view.setFocusPolicy(Qt.NoFocus)

        # スクロールバーを出さない
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 画像を読み込んで Qt が画面表示できる画像データに変換する
        self.pixmap = QPixmap(
            str(initial_image_path)
        )
        self.current_image_path = initial_image_path

        # Pixmap を Scene 上に配置する Item に変換
        self.image_item = QGraphicsPixmapItem(self.pixmap)

        # 拡大・縮小時に高品質な補間を使用
        self.image_item.setTransformationMode(
            Qt.SmoothTransformation
        )

        # 画像の中心を回転軸にする
        self.image_item.setTransformOriginPoint(
            self.image_item.boundingRect().center()
        )

        # Scene に画像を追加
        self.scene.addItem(self.image_item)

        # QMainWindow の中央コンテンツを QGraphicsView にする
        self.setCentralWidget(self.view)

        # 同一ディレクトリの画像一覧を取得
        self.load_image_list(initial_image_path)
    
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

        print(self.image_paths)

        self.current_index = self.image_paths.index(
            image_path
        )
    
    #  キー操作での切り替え時の画像読み込み
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
    def calculate_scale_to_screen(self):
        allowed_rect = self.get_available_window_rect()

        # 元画像のサイズ
        original_width = self.pixmap.width()
        original_height = self.pixmap.height()

        # 90度 / 270度回転時は縦横が入れ替わる
        if self.rotation_angle % 180 == 90:
            rotated_width = original_height
            rotated_height = original_width
        else:
            rotated_width = original_width
            rotated_height = original_height

        width_scale = (
            allowed_rect.width() / rotated_width
        )

        height_scale = (
            allowed_rect.height() / rotated_height
        )

        # モニタ内に収まる最大倍率
        # 小さい画像は100%以上には拡大しない
        return min(
            width_scale,
            height_scale,
            1.0,
        )
    
    def update_after_rotation(self):
        # 回転後の元画像サイズを基準に
        # モニタ内へ最大限収まる倍率を計算
        self.initial_scale = self.calculate_scale_to_screen()
        self.current_scale = self.initial_scale

        # 高品質な縮小Pixmapを生成
        self.apply_scale()

        # apply_scale後の実際の表示領域
        image_rect = self.image_item.sceneBoundingRect()

        # 回転後の画像サイズへWindowを追従
        self.resize_window_to_image()

        # Windowをモニタ中央へ
        QTimer.singleShot(
            0,
            self.center_window_on_screen,
        )

        # 画像中央をView中央へ
        QTimer.singleShot(
            0,
            lambda: self.view.centerOn(
                image_rect.center()
            ),
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

        # geometry() はタイトルバーなどのWindow frameを含まない
        # frameGeometry() はタイトルバーを含む実際のWindow全体
        geometry = self.geometry()
        frame = self.frameGeometry()

        # Window frame が geometry よりどれだけ大きいか
        frame_extra_width = (
            frame.width()
            - geometry.width()
        )

        frame_extra_height = (
            frame.height()
            - geometry.height()
        )

        # geometry の左上と frameGeometry の左上の差
        frame_left_offset = (
            geometry.left()
            - frame.left()
        )

        frame_top_offset = (
            geometry.top()
            - frame.top()
        )

        # frame全体がモニタ内に収まるよう、
        # geometry側で使える最大サイズを求める
        max_window_width = max(
            1,
            allowed_rect.width() - frame_extra_width,
        )

        max_window_height = max(
            1,
            allowed_rect.height() - frame_extra_height,
        )

        target_width = min(
            desired_width,
            max_window_width,
        )

        target_height = min(
            desired_height,
            max_window_height,
        )

        # 実際のWindow frameサイズ
        target_frame_width = (
            target_width
            + frame_extra_width
        )

        target_frame_height = (
            target_height
            + frame_extra_height
        )

        # 現在のWindow frame中心
        current_center = frame.center()

        # frameを中心から均等に拡大
        new_frame_x = int(
            current_center.x()
            - target_frame_width / 2
        )

        new_frame_y = int(
            current_center.y()
            - target_frame_height / 2
        )

        # frame全体がallowed_rectから出ないように補正
        min_frame_x = allowed_rect.left()

        max_frame_x = (
            allowed_rect.right()
            - target_frame_width
            + 1
        )

        min_frame_y = allowed_rect.top()

        max_frame_y = (
            allowed_rect.bottom()
            - target_frame_height
            + 1
        )

        new_frame_x = max(
            min_frame_x,
            min(new_frame_x, max_frame_x),
        )

        new_frame_y = max(
            min_frame_y,
            min(new_frame_y, max_frame_y),
        )

        # setGeometry() は frame ではなく geometry を設定するため、
        # frameとの差分を戻して指定する
        self.setGeometry(
            new_frame_x + frame_left_offset,
            new_frame_y + frame_top_offset,
            target_width,
            target_height,
        )

        print("--- window geometry debug ---")
        print("geometry     :", self.geometry())
        print("frameGeometry:", self.frameGeometry())
        print("allowed_rect :", allowed_rect)
        print("pos          :", self.pos())
        print("-----------------------------")

        # resize後のWindow状態を基準に制限を設定
        self.update_window_size_limits()
    
    # 画像の初期表示 (高解像度なら画面高さを上限に縮小表示)
    def reset_to_initial_view(self):
        # 現在の回転状態を考慮して Fit 倍率を計算
        self.initial_scale = self.calculate_scale_to_screen()
        self.current_scale = self.initial_scale

        # ここで縮小 Pixmap を生成
        self.apply_scale()

        # apply_scale 後の画像サイズを取得
        image_rect = self.image_item.sceneBoundingRect()

        self.resize_window_to_image()

        QTimer.singleShot(
            0,
            lambda: self.view.centerOn(
                image_rect.center()
            ),
        )

        QTimer.singleShot(
            0,
            self.center_window_on_screen,
        )
    
    def apply_scale(self):
        self.view.resetTransform()

        # 縮小時は HiDPI を考慮した高解像度 Pixmap を事前生成する
        # View 側だけで縮小すると細線や文字がぼやけるため、
        # 物理解像度(DPR)分の画素数を確保してから表示する
        if self.current_scale < 1.0:
            logical_width = max(
                1,
                round(self.pixmap.width() * self.current_scale),
            )

            logical_height = max(
                1,
                round(self.pixmap.height() * self.current_scale),
            )

            # Retina / Windows DPI scaling を考慮
            dpr = self.devicePixelRatioF()

            physical_width = max(
                1,
                round(logical_width * dpr),
            )

            physical_height = max(
                1,
                round(logical_height * dpr),
            )

            scaled_pixmap = self.pixmap.scaled(
                physical_width,
                physical_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            # Pixmapの物理解像度と論理サイズを対応させる
            scaled_pixmap.setDevicePixelRatio(dpr)

            self.image_item.setPixmap(
                scaled_pixmap
            )

            self.image_item.setTransformOriginPoint(
                self.image_item.boundingRect().center()
            )

            self.view.scale(
                1.0,
                1.0,
            )

        else:
            # 100%以上では元画像を使用
            self.image_item.setPixmap(
                self.pixmap
            )

            self.image_item.setTransformOriginPoint(
                self.image_item.boundingRect().center()
            )

            self.view.scale(
                self.current_scale,
                self.current_scale,
            )

        # Pixmap 変更後の実際の画像領域に Scene を合わせる
        image_rect = self.image_item.sceneBoundingRect()

        self.scene.setSceneRect(
            image_rect
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
        print("MainWindow key:", event.key())
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

    if len(sys.argv) < 2:
        print("Usage: python main.py <image_path>")
        sys.exit(1)

    initial_image_path = Path(sys.argv[1])

    window = MainWindow(initial_image_path)
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
