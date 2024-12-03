import os
import cv2
import sys
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from ultralytics import YOLO
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QLabel, QMessageBox, QSlider)


class VideoPlayerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Process Images and Videos with YOLO')
        self.setGeometry(100, 100, 800, 600)

        # Main layout for the window (it will hold the video/image and buttons)
        main_layout = QVBoxLayout()

        # Layout for the buttons at the top
        top_layout = QHBoxLayout()

        # Button to choose a video
        self.play_button = QPushButton('Choose Video')
        self.play_button.clicked.connect(self.open_video)
        self.play_button.setToolTip('Select a video file to open') # Tooltip for the "Choose Video" button
        top_layout.addWidget(self.play_button)

        # Button to choose an image
        self.image_button = QPushButton('Choose Image')
        self.image_button.clicked.connect(self.open_image)
        self.image_button.setToolTip('Select an image file to open') # Tooltip for the "Choose Image" button
        top_layout.addWidget(self.image_button)

        # Button to choose YOLO model
        self.choose_model_button = QPushButton('Choose Model')
        self.choose_model_button.clicked.connect(self.choose_model)
        self.choose_model_button.setToolTip('Choose YOLO model for processing')
        top_layout.addWidget(self.choose_model_button)

        # Button to process image/video
        self.process_button = QPushButton('Process')
        self.process_button.clicked.connect(self.process_media)
        self.process_button.setToolTip('Process the selected media with YOLO model')
        top_layout.addWidget(self.process_button)

        # Toggle size button
        self.toggle_size_button = QPushButton('Change Size')
        self.toggle_size_button.clicked.connect(self.toggle_size)
        self.toggle_size_button.setToolTip('Toggle between full size and half size of the media') # Tooltip for the "Change Size" button
        top_layout.addWidget(self.toggle_size_button)

        # Add the top layout containing buttons to the main layout
        main_layout.addLayout(top_layout)

        # Media display area (video or image)
        self.media_label = QLabel(self)
        main_layout.addWidget(self.media_label) # The video/image will be displayed here

        # Create a horizontal layout for the slider at the bottom
        slider_layout = QHBoxLayout()

        # Play/Pause button (moved to the bottom left side)
        self.pause_play_button = QPushButton('Play/Pause')
        self.pause_play_button.clicked.connect(self.toggle_pause_play)
        self.pause_play_button.setToolTip('Play or pause the video playback') # Tooltip for the "Play/Pause" button
        slider_layout.addWidget(self.pause_play_button)

        # Video position slider
        self.video_slider = QSlider(Qt.Horizontal)
        self.video_slider.setMinimum(0)
        self.video_slider.setValue(0)
        self.video_slider.sliderMoved.connect(self.on_slider_move)
        slider_layout.addWidget(self.video_slider)

        # Add slider layout to the main layout (this will place the slider at the bottom)
        main_layout.addLayout(slider_layout)

        self.setLayout(main_layout)

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
        self.model = None  # YOLO model
        self.processed_media = None  # Processed media for display

    def open_video(self):
        # Open file dialog to select a video
        video_file, _ = QFileDialog.getOpenFileName(self, "Choose Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.webm)")

        if video_file:
            self.play_video(video_file)

        # Reset "Change Size" button text after a video is loaded
        self.toggle_size_button.setText('Change Size')

        # Show Play/Pause button and slider
        self.pause_play_button.setVisible(True)
        self.video_slider.setVisible(True)

    def open_image(self):
        # Stop video playback if it's running
        if self.is_video:
            self.stop_video()

        # Open file dialog to select an image
        image_file, _ = QFileDialog.getOpenFileName(self, "Choose Image", "", "Images (*.png *.jpg *.bmp *.jpeg *.tiff *.gif *.webp)")

        if image_file:
            self.display_image(image_file)

        # Reset "Change Size" button text after an image is loaded
        self.toggle_size_button.setText('Change Size')

        # Hide Play/Pause button and slider
        self.pause_play_button.setVisible(False)
        self.video_slider.setVisible(False)

    def stop_video(self):
        # Stop the video playback
        self.timer.stop()  # Stop the timer updating frames
        self.cap.release()  # Release the video capture object
        self.is_video = False  # Mark as not a video
        self.media_label.clear()  # Clear the media label

        # Hide Play/Pause button and slider after stopping the video
        self.pause_play_button.setVisible(False)
        self.video_slider.setVisible(False)

    def play_video(self, video_path):
        # Open the video file using OpenCV
        self.cap = cv2.VideoCapture(video_path)

        # Check if video was opened successfully
        if not self.cap.isOpened():
            # Log to console (for debugging purposes)
            print("Error: Could not open video.")

            # Show error message box to the user
            QMessageBox.critical(self, "Error", "Unsupported video format or file.")
            return

        # Mark that the current media is a video
        self.is_video = True

        # Start the timer to read and display frames
        self.timer.start(30)  # 30 ms per frame (~33 FPS)

        # Update button text to "Pause" when video starts playing
        self.pause_play_button.setText('Pause')

        # Update slider maximum to the number of frames in the video
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_slider.setMaximum(total_frames)

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

                # Set alignment of the label to center the video
                self.media_label.setAlignment(Qt.AlignCenter)  # Center the video horizontally and vertically

                # Resize the window based on video size
                self.resize(w, h)

                # Update slider position
                current_frame_position = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.video_slider.setValue(current_frame_position)
            else:
                # Video has ended, reset it to the beginning
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video to the first frame
                self.update_frame()  # Start playing from the beginning

    def on_slider_move(self, value):
        # Set the video position based on slider value
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)

    def display_image(self, image_path):
        # Open the image using OpenCV
        self.image = cv2.imread(image_path)

        # Check if image is None, indicating an error
        if self.image is None:
            # Log to console (for debugging purposes)
            print("Error: Could not open image.")

            # Show error message box to the user
            QMessageBox.critical(self, "Error", "Unsupported image format or file.")
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

        # Set alignment of the label to center the image
        self.media_label.setAlignment(Qt.AlignCenter)  # Center the image horizontally and vertically

        # Resize the window based on image size
        self.resize(w, h)  # Resize window to fit the image

        # Manually update the layout after resizing
        self.adjustSize()  # Ensure the window resizes properly

    def toggle_size(self):
        # Toggle between half size and full size for the image/video
        self.is_half_size = not self.is_half_size

        if self.is_half_size:
            self.toggle_size_button.setText('Full Size')
        else:
            self.toggle_size_button.setText('Half Size')

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

            # Change button text based on the current state
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


    def process_media(self):
        if not self.model:
            QMessageBox.warning(self, "Model Not Chosen", "Please choose a YOLO model first.")
            return

        if self.is_video:
            self.process_video()
        elif self.image is not None:
            self.process_image()

    def choose_model(self):
        # Let the user select the YOLO model file (e.g., .pt file)
        model_file, _ = QFileDialog.getOpenFileName(self, "Choose YOLO Model", "", "Model Files (*.pt *.weights)")

        if model_file:
            try:
                # Load the model using YOLO class from the Ultralytics package
                self.model = YOLO(model_file)  # Load the model

                # Display the path of the model that was chosen
                QMessageBox.information(self, "Model Loaded", f"YOLO model loaded from:\n{model_file}")

            except Exception as e:
                # If loading the model fails, show the error in a dialog box
                QMessageBox.critical(self, "Model Load Error", f"Failed to load model: {str(e)}")

    def process_image(self):
        # Perform inference using YOLO model on the original image
        results = self.model(self.original_image)

        # Assuming `results[0]` is the processed image with bounding boxes
        processed_image = results[0].plot()  # This will give us the image with boxes

        # Define the folder where processed images will be saved
        save_folder = "Processed media"

        # Create the directory if it doesn't exist
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Create the full file path for saving
        processed_image_path = os.path.join(save_folder, "processed_image.jpg")

        # Save the processed image to the specified path
        cv2.imwrite(processed_image_path, processed_image)

        # Display the processed image (after saving)
        self.display_image(processed_image_path)

    def process_video(self):
        # Define the folder to save the processed video
        save_folder = "Processed media"

        # Create the folder if it doesn't exist
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Check if the video capture object is already opened
        if not self.cap.isOpened():
            print("Error: Video file not opened.")
            return

        # Get the video properties (width, height, FPS)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)

        # Define the output video file path
        output_video_path = os.path.join(save_folder, "processed_video.mp4")

        # Set up the VideoWriter object to save the processed video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec for .mp4
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break  # Exit if there are no more frames

            # Process the frame with YOLO model
            results = self.model(frame)

            # Get the processed frame with bounding boxes (plotting the boxes)
            processed_frame = results[0].plot()  # This is the processed frame

            # Write the processed frame to the output video
            out.write(processed_frame)

        # Release the video writer and capture objects
        out.release()
        self.cap.release()

        # After processing, display the processed video
        self.play_video(output_video_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayerApp()
    window.show()
    sys.exit(app.exec_())
