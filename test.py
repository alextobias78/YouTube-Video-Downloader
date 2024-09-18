from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import logging
import yt_dlp
import time
import subprocess

logging.basicConfig(
    level=logging.DEBUG,
    filename='youtube_downloader.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class FetchInfoThread(QtCore.QThread):
    info_fetched = QtCore.pyqtSignal(dict)
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, url, ydl_opts):
        super().__init__()
        self.url = url
        self.ydl_opts = ydl_opts

    def run(self):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                self.info_fetched.emit(info)
        except Exception as e:
            logging.error(f"Error fetching video info: {str(e)}")
            self.error_occurred.emit(str(e))


class DownloadThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(dict)
    download_finished = QtCore.pyqtSignal()
    download_error = QtCore.pyqtSignal(str)

    def __init__(self, url, ydl_opts):
        super().__init__()
        self.url = url
        self.ydl_opts = ydl_opts

    def run(self):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([self.url])
            self.download_finished.emit()
        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            self.download_error.emit(str(e))


class YouTubeDownloader(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Video Downloader")
        self.setFixedSize(600, 450)
        self.init_ui()
        self.ydl_opts = {
            'progress_hooks': [self.emit_progress],
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',  # Ensure merging into MP4
        }

        # Initialize threads
        self.fetch_thread = None
        self.download_thread = None

        # Initialize progress tracking attributes
        self.last_update_time = 0
        self.progress_history = []

        # Validate FFmpeg Availability
        self.validate_ffmpeg()

    def init_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout()

        # URL Input
        url_label = QtWidgets.QLabel("Enter YouTube Video URL:")
        url_label.setFont(QtGui.QFont("Arial", 14))
        layout.addWidget(url_label)

        self.url_entry = QtWidgets.QLineEdit()
        self.url_entry.setPlaceholderText("https://www.youtube.com/watch?v=example")
        self.url_entry.setFont(QtGui.QFont("Arial", 12))
        layout.addWidget(self.url_entry)

        # Fetch Button
        fetch_button = QtWidgets.QPushButton("Fetch Video Info")
        fetch_button.setStyleSheet("""
            QPushButton {
                background-color: #007BFF; 
                color: white; 
                font-size: 14px; 
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        fetch_button.clicked.connect(self.start_fetch_info)
        layout.addWidget(fetch_button)

        # Resolution Selection
        resolution_label = QtWidgets.QLabel("Select Resolution:")
        resolution_label.setFont(QtGui.QFont("Arial", 14))
        layout.addWidget(resolution_label)

        self.resolution_combo = QtWidgets.QComboBox()
        layout.addWidget(self.resolution_combo)

        # Download Button
        download_button = QtWidgets.QPushButton("Download")
        download_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745; 
                color: white; 
                font-size: 14px; 
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        download_button.clicked.connect(self.start_download)
        layout.addWidget(download_button)

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setFont(QtGui.QFont("Arial", 12))
        layout.addWidget(self.status_label)

        central_widget.setLayout(layout)

    def validate_ffmpeg(self):
        """Check if FFmpeg is installed and accessible."""
        try:
            subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            logging.info("FFmpeg is installed.")
        except subprocess.CalledProcessError:
            logging.error("FFmpeg is not installed or not found in PATH.")
            QtWidgets.QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                "FFmpeg is required to merge audio and video streams.\nPlease install FFmpeg and ensure it's added to your system's PATH.",
            )
            self.set_ui_enabled(False)
        except FileNotFoundError:
            logging.error("FFmpeg is not installed or not found in PATH.")
            QtWidgets.QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                "FFmpeg is required to merge audio and video streams.\nPlease install FFmpeg and ensure it's added to your system's PATH.",
            )
            self.set_ui_enabled(False)

    def start_fetch_info(self):
        url = self.url_entry.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a YouTube video URL.")
            return

        # Disable fetch button to prevent multiple clicks
        self.set_ui_enabled(False)
        self.status_label.setText("Fetching video information...")

        # Initialize and start fetch thread
        self.fetch_thread = FetchInfoThread(url, self.ydl_opts.copy())
        self.fetch_thread.info_fetched.connect(self.on_info_fetched)
        self.fetch_thread.error_occurred.connect(self.on_fetch_error)
        self.fetch_thread.start()

    def on_info_fetched(self, info):
        format_groups = {}
        for f in info.get('formats', []):
            # Include all MP4 formats with a defined height (resolution)
            if f.get('height') and f.get('ext') == 'mp4':
                resolution = f['height']
                # Select the format with the highest bitrate for each resolution
                if (resolution not in format_groups) or (f.get('tbr', 0) > format_groups[resolution].get('tbr', 0)):
                    format_groups[resolution] = f

        if not format_groups:
            self.status_label.setText("No suitable video formats found.")
            QtWidgets.QMessageBox.warning(self, "No Formats", "No MP4 formats with resolution found.")
            self.set_ui_enabled(True)
            return

        sorted_resolutions = sorted(format_groups.keys(), reverse=True)

        self.resolution_combo.clear()
        for resolution in sorted_resolutions:
            format_info = format_groups[resolution]
            resolution_text = f"{resolution}p"
            self.resolution_combo.addItem(resolution_text, format_info['format_id'])

        self.status_label.setText("Video information fetched. Select resolution and click Download.")
        self.set_ui_enabled(True)

    def on_fetch_error(self, error_message):
        self.status_label.setText("Failed to fetch video information.")
        QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.set_ui_enabled(True)

    def start_download(self):
        if self.resolution_combo.count() == 0:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please fetch video information first.")
            return

        format_id = self.resolution_combo.currentData()

        # Modify format to include best audio
        self.ydl_opts['format'] = f"{format_id}+bestaudio"

        # Ensure the output is merged into MP4
        self.ydl_opts['merge_output_format'] = 'mp4'

        url = self.url_entry.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Input Error", "Please enter a YouTube video URL.")
            return

        # Disable UI elements to prevent multiple actions
        self.set_ui_enabled(False)
        self.status_label.setText("Starting download...")

        # Initialize and start download thread
        self.download_thread = DownloadThread(url, self.ydl_opts.copy())
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.download_error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_progress(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            current_time = time.time()
            if current_time - self.last_update_time < 0.1:  # Update every 100ms
                return
            self.last_update_time = current_time

            if total > 0:
                percentage = (downloaded / total) * 100
                smoothed_percentage = self.calculate_moving_average(percentage)
                self.progress_bar.setValue(int(smoothed_percentage))
                self.status_label.setText(f"Downloading: {smoothed_percentage:.1f}% of {self.format_bytes(total)}")
            else:
                self.progress_bar.setValue(0)
                self.status_label.setText(f"Downloading: {self.format_bytes(downloaded)} downloaded")
        elif d['status'] == 'finished':
            self.status_label.setText("Download finished, now merging audio and video...")
            self.progress_bar.setValue(100)

    def emit_progress(self, d):
        # Emit progress from the download thread
        self.download_thread.progress.emit(d)

    def on_download_finished(self):
        self.progress_bar.setValue(100)
        self.status_label.setText("Download and merging completed!")
        QtWidgets.QMessageBox.information(self, "Success", "Download and merging completed successfully!")
        self.set_ui_enabled(True)
        self.download_thread = None

    def on_download_error(self, error_message):
        self.progress_bar.setValue(0)
        self.status_label.setText("Download failed.")
        QtWidgets.QMessageBox.critical(self, "Error", f"An error occurred during download: {error_message}")
        self.set_ui_enabled(True)
        self.download_thread = None

    def set_ui_enabled(self, enabled):
        """
        Enable or disable UI elements to prevent user interaction during operations.
        """
        self.url_entry.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        for button in self.findChildren(QtWidgets.QPushButton):
            button.setEnabled(enabled)

    def format_bytes(self, bytes_num):
        """Helper method to format bytes into a human-readable format"""
        if bytes_num < 1024:
            return f"{bytes_num} B"
        elif bytes_num < 1024 * 1024:
            return f"{bytes_num / 1024:.1f} KB"
        elif bytes_num < 1024 * 1024 * 1024:
            return f"{bytes_num / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_num / (1024 * 1024 * 1024):.1f} GB"

    def calculate_moving_average(self, new_value):
        self.progress_history.append(new_value)
        if len(self.progress_history) > 10:  # Keep last 10 values
            self.progress_history.pop(0)
        return sum(self.progress_history) / len(self.progress_history)


def create_ui():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')  # Optional: Set a modern UI style
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    create_ui()