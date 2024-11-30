import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer


class VideoPlayerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('OpenCV Video Player')
        self.setGeometry(100, 100, 800, 600)

        # Layout
        layout = QVBoxLayout()

        # Video display label
        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        # Play button
        self.play_button = QPushButton('Open Video')
        self.play_button.clicked.connect(self.open_video)
        layout.addWidget(self.play_button)

        self.setLayout(layout)

        # Timer for updating video frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.cap = None
        self.current_frame = None

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

                # Convert to QImage for displaying in PyQt
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

                # Set the QImage as a pixmap on the label
                self.video_label.setPixmap(QPixmap.fromImage(qimg))
            else:
                self.cap.release()
                self.timer.stop()  # Stop the timer when video ends


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayerApp()
    window.show()
    sys.exit(app.exec_())
