import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer


class VideoPlayerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('OpenCV Video Player')
        self.setGeometry(100, 100, 800, 600)

        # Layout for the buttons at the top
        top_layout = QHBoxLayout()

        # Play button
        self.play_button = QPushButton('Open Video')
        self.play_button.clicked.connect(self.open_video)
        top_layout.addWidget(self.play_button)

        # Toggle size button
        self.toggle_size_button = QPushButton('Toggle Size (Half Size)')
        self.toggle_size_button.clicked.connect(self.toggle_size)
        top_layout.addWidget(self.toggle_size_button)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(top_layout)

        # Video display label
        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        self.setLayout(layout)

        # Timer for updating video frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.cap = None
        self.current_frame = None
        self.is_half_size = False  # Track whether the video is in half size or full size

    def open_video(self):
        # Open file dialog to select a video
        video_file, _ = QFileDialog.getOpenFileName(self, "Open Video", "", "Video Files (*.mp4 *.avi *.mov)")

        if video_file:
            self.play_video(video_file)

    def play_video(self, video_path):
        # Open the video file using OpenCV
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            print("Error: Could not open video.")
            return

        # Start the timer to read and display frames
        self.timer.start(30)  # 30 ms per frame (~33 FPS)

    def update_frame(self):
        if self.cap is not None:
            ret, frame = self.cap.read()
            if ret:
                # Convert frame to RGB (OpenCV uses BGR)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Resize frame if in half size mode
                if self.is_half_size:
                    rgb_frame = cv2.resize(rgb_frame, (rgb_frame.shape[1] // 2, rgb_frame.shape[0] // 2))

                # Convert to QImage for displaying in PyQt
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Set the QImage as a pixmap on the label
                self.video_label.setPixmap(QPixmap.fromImage(qimg))

                # Resize the window based on video size
                self.resize(w, h)
            else:
                self.cap.release()
                self.timer.stop()  # Stop the timer when video ends

    def toggle_size(self):
        # Toggle the size of the video between full size and half size
        self.is_half_size = not self.is_half_size

        if self.is_half_size:
            self.toggle_size_button.setText('Toggle Size (Full Size)')
        else:
            self.toggle_size_button.setText('Toggle Size (Half Size)')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayerApp()
    window.show()
    sys.exit(app.exec_())
