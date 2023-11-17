import subprocess
import datetime
import os
import json
import tkinter as tk
from tkinter import filedialog
from compress_vid import copy_exif_data, update_timestamp



def parse_videos_old(input_path):
    print("Parsing videos in folder...")
    extensions = ['.mp4', '.mkv', '.avi', '.mov']
    videos_dict = {}

    for root, dirs, files in os.walk(input_path):
        for f in files:
            if not f.startswith('.') and any(f.lower().endswith(ext) for ext in extensions):
                video_path = os.path.join(root, f)
                base_name, ext = os.path.splitext(f)

                # Check if a video with "_OLD" exists without considering the extension
                old_base_name = base_name + "_OLD"
                for file in os.listdir(root):
                    if file.startswith(old_base_name):
                        old_version = os.path.join(root, file)
                        videos_dict[video_path] = old_version
                        break

    return videos_dict



def prompt_and_copy_exif():
    # Set up the tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hides the root window

    home_dir = os.path.dirname(__file__)
    
    try:
        hidden_file_path = os.path.join(home_dir, ".compress_vid_last_dir")
        with open(hidden_file_path, 'r') as file:
            initial_dir = file.read().strip()
    except FileNotFoundError:
        # Handle the case when the file doesn't exist or is empty
        initial_dir = None

    # Use the initial directory as a default if it exists, otherwise use the current directory
    if initial_dir:
        input_path = filedialog.askdirectory(initialdir=initial_dir)
    else:
        input_path = filedialog.askdirectory()

    with open(hidden_file_path, "w") as f:
        f.write(input_path)

    # Check if a path was selected
    if not input_path:
        print("No file or folder selected.")
        return

    # If a file is selected, use its parent directory; otherwise, the path is already a folder
    if os.path.isfile(input_path):
        input_path = os.path.dirname(input_path)

    videos_dict = parse_videos_old(input_path)

    counter = 0
    for new, old in videos_dict.items():
        counter += 1
        print(f"=====({counter}/{len(videos_dict)})===== Updating {os.path.basename(new)} using {os.path.basename(old)}")
        copy_exif_data(old, new)
        update_timestamp(old, new)

prompt_and_copy_exif()

# copy_exif_data("old", "new")
# update_timestamp("old", "new")