import os
import tkinter as tk
from tkinter import filedialog

def format_size(size_in_bytes):
    # Convert to GB for sizes 1GB or more
    if size_in_bytes >= 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"
    # Convert to MB for sizes less than 1GB
    else:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"

def prompt_and_calculate_video_sizes():
    # Set up the tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hides the root window

    input_path = filedialog.askdirectory()  # Allows selection of files and folders

    # Check if a path was selected
    if not input_path:
        print("No file or folder selected.")
        return

    # If a file is selected, use its parent directory; otherwise, the path is already a folder
    if os.path.isfile(input_path):
        input_path = os.path.dirname(input_path)


    extensions = ['.mp4', '.mkv', '.avi', '.mov']
    # videos = [os.path.join(input_path, f) for f in os.listdir(input_path) if not f.startswith('.') and any(f.lower().endswith(ext) for ext in extensions)]
    videos = []

    # Recursively walk through folder and subfolders
    for root, dirs, files in os.walk(input_path):
        for file in files:
            if not file.startswith('.') and any(file.lower().endswith(ext) for ext in extensions):
                videos.append(os.path.join(root, file))


    size_old = 0
    size_compressed = 0
    count_converted = 0

    # Process each video file
    for video in videos:
        if "_OLD" in video:
            # print(video)
            base_name = video.rsplit("_OLD", 1)[0]
            new_version = base_name + ".mp4"
            print(f"new_version: {new_version}")
            if new_version in videos:
                size_old += os.path.getsize(video)
                size_compressed += os.path.getsize(new_version)
                count_converted += 1
    
    try:
        compression_ratio = f'{round((1 - size_compressed / size_old) * 100, 1)}%' if size_old > 0 else "N/A"
        print(f"{count_converted} files: from {format_size(size_old)} to {format_size(size_compressed)}, ({compression_ratio} compression)")
    except ZeroDivisionError:
        print("No converted videos found")

# Call the function
prompt_and_calculate_video_sizes()