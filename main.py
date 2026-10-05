"""
QPixmap: 画像データそのもの

QGraphicsScene: 画像などのオブジェクトが存在する仮想的な空間
        ↓ その中に
QGraphicsPixmapItem: Scene 上に存在する画像オブジェクト
        ↓ その Scene を覗く
QGraphicsView: ユーザーが実際に見る、Scene の一部分を画面に表示する窓
"""

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QIcon, QPainter, QPixmap
# QApplication がアプリ全体を管理、QMainWindow が実際のウィンドウ本体
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QMenu,
    QToolBar,
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

# ツールバーのアイコン画像のパス
BASE_DIR = Path(__file__).resolve().parent
ICON_DIR = BASE_DIR / "assets" / "icons"

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

        # ============= 画像操作用のツールバーを作成 =============

        self.toolbar = QToolBar("Image Toolbar", self)
        self.addToolBar(self.toolbar)

        self.toolbar.setIconSize(
            QSize(20, 20)
        )

        # 画像を開くアクション
        self.open_action = QAction("Open", self)
        self.open_action.setToolTip("Open Image")

        self.open_action.setIcon(
            QIcon(str(ICON_DIR / "open.svg"))
        )
        
        self.open_action.triggered.connect(
            self.open_image_file
        )

        self.toolbar.addAction(
            self.open_action
        )

        self.toolbar.addSeparator()

        # 表示中の画像のフォルダを開くアクション
        self.open_folder_action = QAction("Open Folder", self)
        self.open_folder_action.setToolTip("Open Current Folder")

        self.open_folder_action.setIcon(
            QIcon(str(ICON_DIR / "open-folder.svg"))
        )

        self.open_folder_action.triggered.connect(
            self.open_current_folder
        )

        self.toolbar.addAction(
            self.open_folder_action
        )

        # 左回転
        self.rotate_left_action = QAction(
            "Rotate Left",
            self,
        )

        self.rotate_left_action.setIcon(
            QIcon(
                str(ICON_DIR / "rotate-left.svg")
            )
        )

        self.rotate_left_action.setToolTip(
            "Rotate Left (Shift + R)"
        )
        
        self.rotate_left_action.triggered.connect(
            self.rotate_left
        )

        self.toolbar.addAction(
            self.rotate_left_action
        )

        # 右回転
        self.rotate_right_action = QAction(
            "Rotate Right",
            self,
        )

        self.rotate_right_action.setIcon(
            QIcon(
                str(ICON_DIR / "rotate-right.svg")
            )
        )

        self.rotate_right_action.setToolTip(
            "Rotate Right (R)"
        )

        self.rotate_right_action.triggered.connect(
            self.rotate_right
        )

        self.toolbar.addAction(
            self.rotate_right_action
        )

        self.toolbar.addSeparator()

        # 最初の画像
        self.first_action = QAction("First", self)
        self.first_action.setToolTip("First Image (Home)")

        self.first_action.setIcon(
            QIcon(str(ICON_DIR / "first.svg"))
        )

        self.first_action.triggered.connect(
            self.show_first_image
        )

        self.toolbar.addAction(
            self.first_action
        )

        # 前の画像
        self.previous_action = QAction("Previous", self)
        self.previous_action.setToolTip("Previous Image (←)")

        self.previous_action.setIcon(
            QIcon(str(ICON_DIR / "previous.svg"))
        )
        
        self.previous_action.triggered.connect(
            self.show_previous_image
        )

        self.toolbar.addAction(
            self.previous_action
        )

        # 次の画像
        self.next_action = QAction("Next", self)
        self.next_action.setToolTip("Next Image (→)")

        self.next_action.setIcon(
            QIcon(str(ICON_DIR / "next.svg"))
        )

        self.next_action.triggered.connect(
            self.show_next_image
        )

        self.toolbar.addAction(
            self.next_action
        )

        # 最後の画像
        self.last_action = QAction("Last", self)
        self.last_action.setToolTip("Last Image (End)")

        self.last_action.setIcon(
            QIcon(str(ICON_DIR / "last.svg"))
        )
        
        self.last_action.triggered.connect(
            self.show_last_image
        )

        self.toolbar.addAction(
            self.last_action
        )

        # =====================================================

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

    # 右クリックメニューを表示（内容はツールバーと同様）
    def show_context_menu(self, global_pos):
        menu = QMenu(self)

        menu.addAction(self.open_action)
        menu.addAction(self.open_folder_action)

        menu.addSeparator()

        menu.addAction(self.rotate_left_action)
        menu.addAction(self.rotate_right_action)

        menu.addSeparator()

        menu.addAction(self.first_action)
        menu.addAction(self.previous_action)
        menu.addAction(self.next_action)
        menu.addAction(self.last_action)

        menu.exec(global_pos)
    
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
    
    # 最初の画像を表示
    def show_first_image(self):
        if not self.image_paths:
            return

        self.current_index = 0

        self.load_image(
            self.image_paths[self.current_index]
        )


    # 最後の画像を表示
    def show_last_image(self):
        if not self.image_paths:
            return

        self.current_index = len(self.image_paths) - 1

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

        # 回転後のFit表示位置へWindowを配置
        QTimer.singleShot(
            0,
            self.position_window_for_fit_view,
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

        # resize後のWindow状態を基準に制限を設定
        self.update_window_size_limits()

    # ウィンドウを画面上端・水平方向中央へ配置
    def position_window_for_fit_view(self):
        allowed_rect = self.get_available_window_rect()
        frame = self.frameGeometry()

        new_x = int(
            allowed_rect.center().x()
            - frame.width() / 2
        )

        # 左右の利用可能領域からはみ出さないようにする
        min_x = allowed_rect.left()
        max_x = (
            allowed_rect.right()
            - frame.width()
            + 1
        )

        new_x = max(
            min_x,
            min(new_x, max_x),
        )

        # タイトルバーを画面上端へ合わせる
        new_y = allowed_rect.top()

        self.move(
            new_x,
            new_y,
        )
    
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
            self.position_window_for_fit_view,
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

    # 画像ファイルを開くためのエクスプローラを表示
    def open_image_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.gif)",
        )

        # キャンセルされた場合
        if not file_path:
            return

        image_path = Path(file_path)

        # 選択した画像のフォルダを対象にする
        self.load_image_list(image_path)

        # 選択した画像を表示
        self.load_image(image_path)

    # 表示中の画像のフォルダを開く
    def open_current_folder(self):
        folder_path = self.current_image_path.parent

        if sys.platform == "win32":
            os.startfile(folder_path)

        elif sys.platform == "darwin":
            subprocess.run(
                ["open", str(folder_path)],
                check=False,
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
        # "Home": show_first_image()
        # "←"   : show_previous_image()
        # "→"   : show_next_image()
        # "End" : show_last_image()
        elif event.key() == Qt.Key_Home:
            self.show_first_image()
        elif event.key() == Qt.Key_Left:
            self.show_previous_image()
        elif event.key() == Qt.Key_Right:
            self.show_next_image()
        elif event.key() == Qt.Key_End:
            self.show_last_image()
        else:
            super().keyPressEvent(event)
    

class ImageView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        self.is_panning = False
        self.last_mouse_pos = None
        self.right_press_pos = None
        self.right_dragged = False
        self.left_press_global_pos = None
        self.window_start_pos = None

    # パンできる状態か確認する
    def can_pan(self):
        horizontal_scrollable = (
            self.horizontalScrollBar().maximum()
            > self.horizontalScrollBar().minimum()
        )

        vertical_scrollable = (
            self.verticalScrollBar().maximum()
            > self.verticalScrollBar().minimum()
        )

        return horizontal_scrollable or vertical_scrollable
    
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

        # 右クリック開始時：パンの準備
        if event.button() == Qt.RightButton:
            self.right_press_pos = event.position().toPoint()
            self.last_mouse_pos = self.right_press_pos

            self.right_dragged = False
            self.is_panning = False

            event.accept()
            return
        
        # 左クリック開始時：ウィンドウ移動の準備
        if event.button() == Qt.LeftButton:
            self.left_press_global_pos = (
                event.globalPosition().toPoint()
            )

            self.window_start_pos = (
                self.window().pos()
            )

            event.accept()
            return

        super().mousePressEvent(event)
    
    # 右クリック押下 + マウス移動中に Scene の表示位置をずらす
    def mouseMoveEvent(self, event):
        # 左ドラッグ中はウィンドウ自体を移動
        if (
            self.left_press_global_pos is not None
            and event.buttons() & Qt.LeftButton
        ):
            current_global_pos = (
                event.globalPosition().toPoint()
            )

            delta = (
                current_global_pos
                - self.left_press_global_pos
            )

            self.window().move(
                self.window_start_pos + delta
            )

            event.accept()
            return

        if (
            self.right_press_pos is not None
            and event.buttons() & Qt.RightButton
        ):
            current_pos = event.position().toPoint()

            # まだドラッグ判定されていない場合
            if not self.right_dragged:
                drag_distance = (
                    current_pos - self.right_press_pos
                ).manhattanLength()

                drag_threshold = (
                    QApplication.styleHints().startDragDistance()
                )

                if drag_distance >= drag_threshold:
                    self.right_dragged = True

                    if self.can_pan():
                        self.is_panning = True

            # パン中なら画像を移動
            if self.is_panning:
                delta = current_pos - self.last_mouse_pos

                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value()
                    - delta.x()
                )

                self.verticalScrollBar().setValue(
                    self.verticalScrollBar().value()
                    - delta.y()
                )

            self.last_mouse_pos = current_pos

            event.accept()
            return

        super().mouseMoveEvent(event)
    
    
    def mouseReleaseEvent(self, event):
        # 左クリックを離すとウィンドウ移動終了
        if event.button() == Qt.LeftButton:
            self.left_press_global_pos = None
            self.window_start_pos = None

            event.accept()
            return
        
        # 右クリックを離すとパンモード終了
        if event.button() == Qt.RightButton:
            # ドラッグされていなければ通常の右クリック
            show_menu = not self.right_dragged

            self.is_panning = False
            self.last_mouse_pos = None
            self.right_press_pos = None
            self.right_dragged = False

            if show_menu:
                self.window().show_context_menu(
                    event.globalPosition().toPoint()
                )

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
