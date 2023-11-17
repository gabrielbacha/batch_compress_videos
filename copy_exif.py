import subprocess
import datetime
import os
import json
import tkinter as tk
from tkinter import filedialog

def copy_exif_data(original_file, new_file):
    # Keys to copy
    keys = {
        'XMP:Rating': 'Rating',
        'XML:DeviceManufacturer': 'Make',
        'XML:DeviceModelName': 'Model',
        'XML:DeviceSerialNo': 'SerialNumber',
        'QuickTime:CameraLensModel': 'LensModel',
        'QuickTime:CameraFocalLength35mmEquivalent': 'FocalLengthIn35mmFilm',
        'QuickTime:Make': 'Make',
        'QuickTime:Model': 'Model',
        'QuickTime:Software': 'Software',
        'QuickTime:CreateDate': 'DateTimeOriginal',
        'Composite:GPSAltitude': 'GPSAltitude',
        'Composite:GPSAltitudeRef': 'GPSAltitudeRef',
        'Composite:GPSLatitude': 'GPSLatitude',
        'Composite:GPSLongitude': 'GPSLongitude',
        'Composite:Rotation': 'Rotation'    
    }

    simplified_keys = {key.split(':')[1]: value for key, value in keys.items()}

    # Read EXIF data from the original file
    command_read = ['exiftool', '-json', original_file]
    result = subprocess.run(command_read, capture_output=True, text=True)
    exif_data = json.loads(result.stdout)[0]

    print("Copying exif data...")

    updated_keys_values = []
    
    command_write = ['exiftool', '-P', '-overwrite_original']

    for full_key, simple_key in simplified_keys.items():
        if full_key in exif_data:
            value = exif_data[full_key]
            if isinstance(value, str) and value.strip() == '':
                continue  # Skip empty string values
            # print(f'{full_key}:{value}:{simple_key}')
            command_write.append(f'-{simple_key}={value}')
            updated_keys_values.append((simple_key, value))


    command_write.append(new_file)
    # print(" ".join(command_write)) 
    result = subprocess.run(command_write, capture_output=True, text=True)

    # Check the first line of the output to determine if the file was updated
    first_line = result.stdout.split('\n')[0] if result.stdout else ''
    if "1 image files updated" in first_line:
        print("The following keys and values have been updated:")
        for key, value in updated_keys_values:
            print(f'Updated {key} to {value}')
    else:
        print("No updates were made.")
        if result.stderr:
            print("Error:", result.stderr)

    print("Exif data copied.")
    return exif_data

def update_timestamp(original_file, new_file):
    print(f"Updating timestamp for: {new_file}")

    # Get the original creation time for comparison
    read_create_date = subprocess.run(['stat', '-f', '%SB', original_file], capture_output=True, text=True)
    # print(read_create_date.stdout.strip())
    # Convert the birth time string to a datetime object
    original_timestamp = datetime.datetime.strptime(read_create_date.stdout.strip(), "%b %d %H:%M:%S %Y")
    print(f"Original (_OLD) file timestamp: {original_timestamp}")

    # Try to get 'Create Date' from EXIF data
    command = ['exiftool', '-CreateDate', '-d', '%Y:%m:%d %H:%M:%S', original_file]
    result = subprocess.run(command, capture_output=True, text=True)
    create_date_str = result.stdout.strip().split(': ')[-1]  # Extract the date part
    print(f"======={os.path.basename(original_file)} create date is {create_date_str}")

    if create_date_str:
        # Parse the 'Create Date' string into a datetime object
        try:
            create_date = datetime.datetime.strptime(create_date_str, '%Y:%m:%d %H:%M:%S')
            # Update the creation date using SetFile
            formatted_date = create_date.strftime("%m/%d/%Y %H:%M:%S")
            setfile_command = ['SetFile', '-d', formatted_date, new_file]
            subprocess.run(setfile_command, check=True)
            print(f"EXIF 'Create Date' set to: {formatted_date}")
        except ValueError:
            print("Invalid EXIF 'Create Date'. Using fallback method.")
            # Fallback method using touch -r
            touch_command = ['touch', '-r', original_file, new_file]
            subprocess.run(touch_command, check=True)
            print(f"Timestamp updated using touch -r from {original_file}")
    else:
        # Fallback to the original file's creation time using touch -r
        touch_command = ['touch', '-r', original_file, new_file]
        subprocess.run(touch_command, check=True)
        print(f"EXIF 'Create Date' not found. Timestamp updated using touch -r from {original_file}")


def parse_videos(input_path):
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

    print(input_path)

    videos_dict = parse_videos(input_path)
    for new, old in videos_dict.items():
        print(f"{os.path.basename(new)} > {os.path.basename(old)}")

    for new, old in videos_dict.items():
        print(f"Updating {os.path.basename(new)} using {os.path.basename(old)}")
        copy_exif_data(old, new)
        update_timestamp(old, new)

prompt_and_copy_exif()

