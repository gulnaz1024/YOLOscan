import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class VideoPlayerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Process Images and Videos with YOLO')
        self.setGeometry(100, 100, 800, 600)

        # Layout for the buttons at the top
        top_layout = QHBoxLayout()

        # Button to choose a video
        self.play_button = QPushButton('Choose Video')
        self.play_button.clicked.connect(self.open_video)
        top_layout.addWidget(self.play_button)

        # Button to choose an image
        self.image_button = QPushButton('Choose Image')
        self.image_button.clicked.connect(self.open_image)
        top_layout.addWidget(self.image_button)

        # Toggle size button
        self.toggle_size_button = QPushButton('Toggle Size (Half Size)')
        self.toggle_size_button.clicked.connect(self.toggle_size)
        top_layout.addWidget(self.toggle_size_button)

        # Play/Pause button
        self.pause_play_button = QPushButton('Play/Pause')
        self.pause_play_button.clicked.connect(self.toggle_pause_play)
        top_layout.addWidget(self.pause_play_button)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(top_layout)

        # Video/Image display label
        self.media_label = QLabel(self)
        layout.addWidget(self.media_label)

        self.setLayout(layout)

        # Timer for updating video frames
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.cap = None
        self.current_frame = None
        self.is_paused = False  # Flag to track if the video is paused
        self.is_half_size = False  # Track whether the video or image is in half size or full size
        self.is_video = False  # Track if the media is a video or an image
        self.image = None  # Store the loaded image
        self.original_image = None  # Store the original unmodified image for reset

    def open_video(self):
        # Open file dialog to select a video
        video_file, _ = QFileDialog.getOpenFileName(self, "Choose Video", "", "Video Files (*.mp4 *.avi *.mov)")

        if video_file:
            self.play_video(video_file)

    def open_image(self):
        # Stop video playback if it's running
        if self.is_video:
            self.stop_video()

        # Open file dialog to select an image
        image_file, _ = QFileDialog.getOpenFileName(self, "Choose Image", "", "Images (*.png *.jpg *.bmp *.jpeg)")

        if image_file:
            self.display_image(image_file)

    def stop_video(self):
        # Stop the video playback
        self.timer.stop()  # Stop the timer updating frames
        self.cap.release()  # Release the video capture object
        self.is_video = False  # Mark as not a video
        self.media_label.clear()  # Clear the media label

    def play_video(self, video_path):
        # Open the video file using OpenCV
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            print("Error: Could not open video.")
            return

        # Mark that the current media is a video
        self.is_video = True

        # Start the timer to read and display frames
        self.timer.start(30)  # 30 ms per frame (~33 FPS)

        # Update button text to "Pause" when video starts playing
        self.pause_play_button.setText('Pause')

    def update_frame(self):
        if self.cap is not None and not self.is_paused:
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
                self.media_label.setPixmap(QPixmap.fromImage(qimg))

                # Resize the window based on video size
                self.resize(w, h)
            else:
                # Video has ended, reset it to the beginning
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video to the first frame
                self.update_frame()  # Start playing from the beginning

    def display_image(self, image_path):
        # Open the image using OpenCV
        self.image = cv2.imread(image_path)
        if self.image is None:
            print("Error: Could not open image.")
            return

        # Store the original image for future resizing
        self.original_image = self.image.copy()

        # Mark that the current media is an image
        self.is_video = False

        # Resize the image if in half size mode
        if self.is_half_size:
            self.image = cv2.resize(self.image, (self.image.shape[1] // 2, self.image.shape[0] // 2))

        # Convert the image to RGB (OpenCV uses BGR)
        rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        # Convert to QImage for displaying in PyQt
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qimg = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Set the QImage as a pixmap on the label
        self.media_label.setPixmap(QPixmap.fromImage(qimg))

        # Resize the window based on image size
        self.resize(w, h)  # Resize window to fit the image

        # Manually update the layout after resizing
        self.adjustSize()  # Ensure the window resizes properly

    def toggle_size(self):
        # Toggle the size of the media (video or image) between full size and half size
        self.is_half_size = not self.is_half_size

        if self.is_half_size:
            self.toggle_size_button.setText('Toggle Size (Full Size)')
        else:
            self.toggle_size_button.setText('Toggle Size (Half Size)')

        # If it's a video, adjust the video size
        if self.is_video and self.cap is not None:
            self.update_frame()  # Refresh video display
        # If it's an image, adjust the image size
        elif not self.is_video and self.image is not None:
            # Resize the image
            if self.is_half_size:
                self.image = cv2.resize(self.original_image, (self.original_image.shape[1] // 2, self.original_image.shape[0] // 2))
            else:
                # Reset the image to full size
                self.image = self.original_image.copy()

            # Convert to RGB (OpenCV uses BGR)
            rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

            # Convert to QImage for displaying in PyQt
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Set the QImage as a pixmap on the label
            self.media_label.setPixmap(QPixmap.fromImage(qimg))

            # Resize the window to match the new image size
            self.resize(w, h)  # Resize window based on current image size

            # Manually update the layout after resizing
            self.adjustSize()  # Ensure the window resizes properly

    def toggle_pause_play(self):
        # Toggle the play/pause state (only for video)
        if self.is_video:
            self.is_paused = not self.is_paused

            if self.is_paused:
                self.timer.stop()  # Stop the video when paused
                self.pause_play_button.setText('Play')  # Change button text to 'Play'
            else:
                self.timer.start(30)  # Resume video playback
                self.pause_play_button.setText('Pause')  # Change button text to 'Pause'

            # If the video has ended and we click Play/Pause, restart from the beginning
            if self.cap and not self.cap.isOpened() and self.is_paused:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video to the first frame
                self.update_frame()  # Start playing from the beginning
                self.is_paused = False  # Ensure video starts playing immediately after reset

        else:
            # If it's an image, toggle play/pause doesn't apply, so just reset to default behavior
            self.pause_play_button.setText('Play/Pause')  # Just reset the button text


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayerApp()
    window.show()
    sys.exit(app.exec_())
