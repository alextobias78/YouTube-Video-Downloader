# YouTube Video Downloader

This project is a simple YouTube video downloader application built with Python and PyQt5. It allows you to enter a YouTube video URL, fetch video information, select a resolution, and download the video with its audio merged into an MP4 file. The application uses the [yt-dlp](https://github.com/yt-dlp/yt-dlp) library for downloading and [FFmpeg](https://ffmpeg.org/) for merging audio and video streams.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python 3.6+**: Make sure Python is installed on your system. You can download it from [python.org](https://www.python.org/downloads/).
- **FFmpeg**: This application requires FFmpeg to merge audio and video streams. Follow the installation instructions for your operating system on the [FFmpeg website](https://ffmpeg.org/download.html).
- **PyQt5**: Install PyQt5 for the graphical user interface.
- **yt-dlp**: This is a command-line program to download videos from YouTube and other sites.

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/alextobias78/YouTube-Video-Downloader.git
    cd YouTube-Video-Downloader
    ```

2. **Install dependencies:**

    ```sh
    pip install pyqt5 yt-dlp
    ```

3. **Ensure FFmpeg is installed** and added to your system's PATH.

## Usage

1. **Run the application:**

    ```sh
    python YT_DOWNLOADER.py
    ```

2. **Enter the YouTube video URL** in the input field.

3. **Click on 'Fetch Video Info'** to retrieve available video formats.

4. **Select the desired resolution** from the dropdown menu.

5. **Click on 'Download'** to start downloading the video. The progress will be shown in the progress bar.

6. **Wait for the download and merging process to complete.** A success message will appear once finished.

## Logging

Logs will be saved in the `youtube_downloader.log` file for troubleshooting and debugging.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
