import sys
import pyautogui
import pytesseract
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QTime

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ============================================================
#   ★ 時刻取得用の赤枠オーバーレイ（リサイズなし）
# ============================================================
class TimeCaptureOverlay(QWidget):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 初期位置とサイズ（固定）
        self.x, self.y = 300, 200
        self.w, self.h = 70, 30

        # 設置ボタン
#        self.capture_button = QPushButton("設置", self)
#        self.capture_button.setStyleSheet("background-color: white;")
#        self.capture_button.clicked.connect(self.capture_time)
#        self.capture_button.resize(60, 25)

        self.dragging = False

        self.setGeometry(self.x, self.y, self.w, self.h)
#        self.update_button_position()
        self.show()

#    def update_button_position(self):
#        self.capture_button.move(self.w // 2 - 30, -30)
#        self.setGeometry(self.x, self.y, self.w, self.h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 0, 0), 3))
        painter.drawRect(0, 0, self.w - 1, self.h - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            dx = event.x() - self.drag_start.x()
            dy = event.y() - self.drag_start.y()
            self.x += dx
            self.y += dy
            self.setGeometry(self.x, self.y, self.w, self.h)
#            self.update_button_position()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def capture_time(self):
        screenshot = pyautogui.screenshot(region=(self.x, self.y, self.w, self.h))
        text = pytesseract.image_to_string(screenshot, lang="eng")
        print("抽出されたテキスト:", text.strip())

        import re
        match = re.search(r"\b\d{1,2}:\d{2}:\d{2}\b", text)

        if match:
            time_str = match.group()
            # ★ 直近クリック点の時刻セルに入力
            if self.parent_window.last_clicked_time_input is not None:
                self.parent_window.last_clicked_time_input.setText(time_str)
            else:
                # 直近点が無い場合は推定欄へ
                self.parent_window.estimate_input.setText(time_str)

#        self.close()


# ============================================================
#   ★ 元の PyQt5 アプリ（軌道推定 GUI）
# ============================================================
class TimeStampedFitWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("時刻付き点と近似直線＋推定位置＋右クリック削除")
        self.setGeometry(100, 100, 900, 650)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        self.setWindowOpacity(0.7)

        self.points = []
        self.time_inputs = []
        self.estimate_point = None

        # ★ 直近クリック点の時刻セル
        self.last_clicked_time_input = None

        # リセット
        self.reset_button = QPushButton("リセット", self)
        self.reset_button.move(10, 10)
        self.reset_button.clicked.connect(self.reset_all)
        self.reset_button.setStyleSheet("background-color: white;")

        # 推定時刻入力
        self.estimate_input = QLineEdit(self)
        self.estimate_input.setPlaceholderText("hh:mm:ss")
        self.estimate_input.setFixedWidth(100)
        self.estimate_input.move(120, 10)

        # 推定ボタン
        self.estimate_button = QPushButton("推定", self)
        self.estimate_button.move(230, 10)
        self.estimate_button.clicked.connect(self.estimate_position)
        self.estimate_button.setStyleSheet("background-color: white;")

        # ★ 時刻取得ボタン
        self.capture_button = QPushButton("時刻取得", self)
        self.capture_button.move(320, 10)
        self.capture_button.clicked.connect(self.open_time_capture)
        self.capture_button.setStyleSheet("background-color: white;")

        self.show()

        # ★ 起動時に赤枠を表示
        self.overlay = TimeCaptureOverlay(self)

    # --------------------------------------------------------
    #   ★ 赤枠オーバーレイを起動
    # --------------------------------------------------------
    def open_time_capture(self):
    # ★ 赤枠がまだ無ければ作る（位置リセットしない）
#         if not hasattr(self, "overlay"):
#             self.overlay = TimeCaptureOverlay(self)
#     
#         # ★ 設置ボタンの代わりにここで OCR を実行
#         self.overlay.capture_time()

    # ★ すでに赤枠が存在するなら再利用（位置リセットしない）
        if hasattr(self, "overlay") and self.overlay is not None:
            self.overlay.capture_time()
            return

    # 初回だけ赤枠を作成
        self.overlay = TimeCaptureOverlay(self)
        self.overlay.capture_time()

    # --------------------------------------------------------
    #   左クリックで点追加（直近点を記録）
    # --------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x, y = event.x(), event.y()
            self.points.append((x, y))

            time_input = QLineEdit(self)
            time_input.setFixedWidth(80)
            time_input.move(100 + 90 * (len(self.time_inputs) % 7),
                            50 + 30 * (len(self.time_inputs) // 7))
            time_input.setPlaceholderText("hh:mm:ss")
            time_input.show()
            self.time_inputs.append(time_input)

            # ★ 直近クリック点を記録
            self.last_clicked_time_input = time_input

            self.update()

        elif event.button() == Qt.RightButton:
            if not self.points:
                return
            click_x, click_y = event.x(), event.y()

            min_index = None
            min_dist_sq = float('inf')
            for i, (x, y) in enumerate(self.points):
                dist_sq = (x - click_x) ** 2 + (y - click_y) ** 2
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    min_index = i

            if min_index is not None:
                for input_box in self.time_inputs[min_index:]:
                    input_box.deleteLater()
                self.points = self.points[:min_index]
                self.time_inputs = self.time_inputs[:min_index]
                self.estimate_point = None
                self.update()

    def reset_all(self):
        self.points.clear()
        self.estimate_point = None
        for input_box in self.time_inputs:
            input_box.deleteLater()
        self.time_inputs.clear()
        self.estimate_input.clear()
        self.last_clicked_time_input = None
        self.update()

    def estimate_position(self):
        if len(self.points) < 2:
            return

        time_values = []
        for input_box in self.time_inputs:
            t = QTime.fromString(input_box.text(), "hh:mm:ss")
            if not t.isValid():
                return
            time_values.append(t.msecsSinceStartOfDay() / 1000.0)

        t_est = QTime.fromString(self.estimate_input.text(), "hh:mm:ss")
        if not t_est.isValid():
            return
        t_query = t_est.msecsSinceStartOfDay() / 1000.0

        def linear_fit(t_list, v_list):
            n = len(t_list)
            sum_t = sum(t_list)
            sum_v = sum(v_list)
            sum_tt = sum(t * t for t in t_list)
            sum_tv = sum(t * v for t, v in zip(t_list, v_list))
            denom = n * sum_tt - sum_t ** 2
            if denom == 0:
                return None, None
            a = (n * sum_tv - sum_t * sum_v) / denom
            b = (sum_v - a * sum_t) / n
            return a, b

        xs, ys = zip(*self.points)
        ax, bx = linear_fit(time_values, xs)
        ay, by = linear_fit(time_values, ys)
        if None in (ax, ay):
            return

        x_est = ax * t_query + bx
        y_est = ay * t_query + by
        self.estimate_point = (x_est, y_est)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        for i, (x, y) in enumerate(self.points):
            painter.setPen(QPen(QColor(255, 0, 0, 255), 6))
            painter.drawPoint(x, y)
            if i < len(self.time_inputs):
                time_text = self.time_inputs[i].text()
                if time_text:
                    painter.setPen(QPen(QColor(0, 0, 0, 255)))
                    painter.setFont(QFont("Arial", 8))
                    painter.drawText(x + 5, y - 5, time_text)

        if len(self.points) >= 2:
            xs, ys = zip(*self.points)
            n = len(xs)
            sum_x = sum(xs)
            sum_y = sum(ys)
            sum_xx = sum(x * x for x in xs)
            sum_xy = sum(x * y for x, y in zip(xs, ys))
            denom = n * sum_xx - sum_x ** 2
            if denom != 0:
                m = (n * sum_xy - sum_x * sum_y) / denom
                b = (sum_y - m * sum_x) / n
                w = self.width()
                y_left = m * 0 + b
                y_right = m * w + b
                painter.setPen(QPen(QColor(0, 255, 0, 255), 2))
                painter.drawLine(0, int(y_left), w, int(y_right))

        if self.estimate_point:
            x, y = self.estimate_point
            painter.setPen(QPen(QColor(0, 0, 255, 255), 8))
            painter.drawPoint(int(x), int(y))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeStampedFitWindow()
    sys.exit(app.exec_())
