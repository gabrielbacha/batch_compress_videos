import subprocess
import datetime
import os

ffmpeg_settings = {
    '4k': {
        '30': {
            'vt_h265': {
                'LQ': '25',
                'HQ': '60'
            },
        },
        '60': {
            'vt_h265': {
                'LQ': '30',
                'HQ': '70'
            },
        },
        '120': {
            'vt_h265': {
                'LQ': '50',  # These are hypothetical values
                'HQ': '100'  # Adjust them as per the actual quality settings required
            },
        },
    },
    '1080p': {
        '30': {
            'vt_h265': {
                'LQ': '8',
                'HQ': '15'
            },
        },
        '60': {
            'vt_h265': {
                'LQ': '10',
                'HQ': '20'
            },
        },
        '120': {
            'vt_h265': {
                'LQ': '20',  # These are hypothetical values
                'HQ': '40'   # Adjust them as per the actual quality settings required
            },
        },
    }
}

def get_video_info(input_path):
    ## FFPROBE INFO
    # ffprobe command to get video codec, dimensions, bitrate, fps, duration, and file size
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,bit_rate,r_frame_rate',
        '-show_entries', 'format=duration,size',  # Including format=size to get the file size
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    print("Pulling video information...")
    print(" ".join(cmd))

    # Execute the ffprobe command
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8').strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        output = ['h264', '1', '1', '1/1', '1', '1', '1']

    # Extracting the information from the output
    video_codec = output[0]
    width = output[1]
    height = output[2]
    bitrate = output[4]
    fps_frac = output[3]
    duration = float(output[5])
    file_size = output[6]  # Corrected file size index

    # Calculating FPS from the fractional representation
    fps = "N/A"
    if fps_frac:
        try:
            numerator, denominator = map(int, fps_frac.split('/'))
            fps = round(float(numerator) / float(denominator), 2)
        except ValueError:
            # Handle the case where the FPS is not a fraction (which is rare)
            fps = float(fps_frac)

    # Formatting dimensions
    dimensions = f"{width}x{height}"

    # Formatting bitrate as Mb/s if bitrate is available
    video_bitrate = "N/A"
    if bitrate and bitrate.isdigit():
        video_bitrate = round(int(bitrate) / 1e6, 1)

    # Formatting file size as MB
    size_mb = round(int(file_size) / 1e6, 1)

    # Formatting duration as HH:MM:SS
    duration_str = str(datetime.timedelta(seconds=duration))

    ##RATING
    # Command to get the rating using exiftool
    rating_cmd = ['exiftool', '-XMP:Rating', input_path]

    # Run the command and capture the output
    completed_process = subprocess.run(rating_cmd, stdout=subprocess.PIPE, text=True)

    # Check if the command was successful
    if completed_process.returncode == 0:
        # Extract the rating from the output
        output = completed_process.stdout.strip()

        # Assume output format: "XMP:Rating                        : <RatingValue>"
        # Split the output and get the last element, which should be the rating
        rating = output.split(':')[-1].strip()

    else:
        # Handle error if exiftool failed
        print("Error: exiftool did not complete successfully.")
        return None

     # Constructing the dictionary with the video information
    video_info = {
        'video_codec': video_codec,
        'dimensions': dimensions,
        'video_bitrate': video_bitrate,
        'fps': fps,
        'duration_str': duration_str,
        'size_mb': size_mb,
        'rating': rating
    }

    # Returning the constructed dictionary
    return video_info

# get_video_info(testfile)

def get_export_bitrate(video_info, force_hq=False):
    # Use the get_video_info function to get video parameters
    print("Getting export settings...")
    dimensions = video_info['dimensions']
    fps = video_info['fps']
    codec = 'vt_h265'
    video_bitrate = video_info['video_bitrate']
    rating_str = video_info['rating']
    # Default quality
    quality = 'LQ'
    # Override quality if HQ is forced
    if force_hq:
        quality = 'HQ'

    # Attempt to convert the rating to an integer if it's numeric
    try:
        rating = int(rating_str)
        if rating >= 5:
            quality = 'HQ'
    except ValueError:
        # If it's not a number, keep the default quality
        pass
    
    # Determine resolution based on dimensions
    width, height = map(int, dimensions.split('x'))
    resolution = None
    if (width >= 3840 and height >= 2160) or (width >= 2160 and height >= 3840):  # Handling both landscape and portrait 4K
        resolution = '4k'
    elif (width >= 1920 and height >= 1080) or (width >= 1080 and height >= 1920):  # Handling both landscape and portrait 1080p
        resolution = '1080p'

    # Round fps to the nearest whole number to match against '30' or '60', 24 & 25 are considered 30
    if float(fps) <= 30:
        frame_rate = '30'
    else:
        frame_rate = str(round(float(fps) / 30) * 30)

    # Use resolution and frame rate to get the correct settings from the dictionary
    try:
        export_settings = {
            "new_bitrate": str(min(float(ffmpeg_settings.get(resolution, {}).get(str(frame_rate), {}).get(codec, {}).get(quality)), float(video_bitrate))),
            "new_codec":list(ffmpeg_settings.get(resolution, {}).get(str(frame_rate)).keys())[0]
            }
    except:
        export_settings = {
            "new_bitrate": "1",
            "new_codec": "vt_h265"
            }

    return export_settings

def bitrate_to_size(duration_str, bitrate_mbps):
    """
    Estimates the file size in MB based on the video duration and bitrate.
    The duration_str is expected to be in HH:MM:SS format.
    The bitrate_mbps is expected to be in Mbps.
    """
    # Convert HH:MM:SS to total seconds
    hours, minutes, seconds = map(float, duration_str.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    
    # Calculate the estimated file size in MB
    if bitrate_mbps != "N/A":
        file_size_mb = (bitrate_mbps * total_seconds * 0.125)
    else:
        file_size_mb = "N/A"
    
    return round(file_size_mb, 2) if file_size_mb != "N/A" else file_size_mb

def estimate_new_file_size(video_info, export_settings):
    print("Estimating new file size...")

    duration_str = video_info['duration_str']
    size_mb = video_info['size_mb']
    new_bitrate = export_settings['new_bitrate']

    # If no matching settings found, return "N/A"
    if not new_bitrate:
        return "N/A"

    # Estimate new file size
    new_file_size_mb = round(bitrate_to_size(duration_str, float(new_bitrate)),1)

    # Calculate compression ratio
    try:
        compression_ratio = 1 - (new_file_size_mb / size_mb)
    except:
        compression_ratio = 0

    converted_file_data = {
        'new_file_size_mb': new_file_size_mb,
        'new_bitrate': new_bitrate,
        'size_mb': size_mb,
        'compression_ratio': f'{round(compression_ratio * 100, 1)}%'
    }

    return converted_file_data

def parse_videos(input_path):
    print("Parsing videos in folder...")
    extensions = ['.mp4', '.mkv', '.avi', '.mov']
    videos = [os.path.join(input_path, f) for f in os.listdir(input_path) if not f.startswith('.') and any(f.lower().endswith(ext) for ext in extensions)]
    return videos

def save_new_filename(input_filedir):
    dir_name = os.path.dirname(input_filedir)
    file_name = os.path.splitext(os.path.basename(input_filedir))[0]
    extension = '.mp4'  # Since we want to convert all files to mp4
    counter = 1

    output_filedir = os.path.join(dir_name, f"{file_name}{extension}")

    while os.path.exists(output_filedir):
        output_filedir = os.path.join(dir_name, f"{file_name} {counter}{extension}")
        counter += 1
    return output_filedir

def convert_video_handbrake(input_file, export_settings):
    print("Converting video...")
    output_file = save_new_filename(input_file)
    # Build the HandbrakeCLI command
    cmd = [
        'HandBrakeCLI',
        '-i', input_file,
        '-o', output_file,
        '-e', export_settings['new_codec'],
        '-b', str(float(export_settings['new_bitrate'])*1000),  # Average bitrate
        '-f', 'mp4',
        '--encopts', 'keyint=60',
        '--optimize',
        '--cfr',  # Constant frame rate
        '--keep-display-aspect',  # Maintain aspect ratio
    ]
    
    ## Build the ffmpeg command
    # cmd = [
    #     'ffmpeg',
    #     '-i', input_file,
    #     '-c:v', "hevc_videotoolbox",
    #     '-b:v', f"{float(export_settings['new_bitrate']) * 1000}k",  # Bitrate in kbps
    #     '-f', 'mp4',
    #     '-g', '60',  # Keyframe interval
    #     '-vsync', 'cfr',  # Constant frame rate
    #     '-map_metadata', '0',
    #     output_file
    # ]


    # Execute the command
    print(" ".join(cmd))
    subprocess.run(cmd)
    # print(f'FAKE PROCESSED {input_file}')
    return output_file

import subprocess

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

    for full_key, simple_key in simplified_keys.items():
        if full_key in exif_data:
            value = exif_data[full_key]
            if isinstance(value, str) and value.strip() == '':
                continue  # Skip empty string values
            # print(f'{full_key}:{value}:{simple_key}')
            command_write = ['exiftool', "-P", "-overwrite_original", f'-{simple_key}={value}', new_file]
            # print(" ".join(command_write)) 
            result = subprocess.run(command_write, capture_output=True, text=True)

            # Split the output into lines and get the first line
            first_line = result.stdout.split('\n')[0]
            if first_line == "    1 image files updated":
                print(f"Successly changed {simple_key} to {value}")
            else:
                print(first_line)

    print("Exif data copied.")
    return exif_data

def update_timestamp(original_file, new_file):
    print(f"Updating timestamp for: {new_file}")

    # Get the original creation time for comparison
    read_create_date = subprocess.run(['stat', '-f', '%SB', original_file], capture_output=True, text=True)
    # print(read_create_date.stdout.strip())
    # Convert the birth time string to a datetime object
    original_timestamp = datetime.datetime.strptime(read_create_date.stdout.strip(), "%b %d %H:%M:%S %Y")
    print(f"Original file timestamp: {original_timestamp}")

    # Try to get 'Create Date' from EXIF data
    command = ['exiftool', '-CreateDate', '-d', '%Y:%m:%d %H:%M:%S', original_file]
    result = subprocess.run(command, capture_output=True, text=True)
    create_date_str = result.stdout.strip().split(': ')[-1]  # Extract the date part

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




def old_file_new_name(input_path):
    file_base, file_extension = os.path.splitext(input_path)
    converted_file_name = f"{file_base}_OLD{file_extension}"
    
    return converted_file_name

def rename_file(input_path, new_name):
    try:
        directory = os.path.dirname(input_path)
        original_extension = os.path.splitext(input_path)[1]
        new_name_without_extension = os.path.splitext(new_name)[0]
        new_file_path = os.path.join(directory, new_name_without_extension + original_extension)
        os.rename(input_path, new_file_path)
        print(f"Renamed {os.path.basename(input_path)} to {os.path.basename(new_file_path)}")
        return True
    except Exception as e:
        print(f"Failed to rename {os.path.basename(input_path)}: {e}")
        return False


def rename_with_rollback(original_file_path, intermediate_file_path, final_file_path):
    # First, rename the original file to the intermediate path
    if rename_file(original_file_path, intermediate_file_path):
        # If the first rename succeeds, try the second rename
        if rename_file(final_file_path, original_file_path):
            return True
        else:
            # If the second rename fails, rollback the first rename
            print("Second renaming operation failed, rolling back the first rename.")
            rename_file(intermediate_file_path, original_file_path)
    else:
        print("First renaming operation failed.")
    return False




from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QPushButton, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
import os
import json
import sys
import os

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        # Obtain the size of the screen
        screen = QtWidgets.QApplication.primaryScreen().geometry()

        # Calculate 80% of the screen width and convert to integer
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.6)  # You can choose to keep the current height or set your own

        # Set the window size with integer width and height
        self.resize(width, height)

        self.tree = QTreeView()
        self.tree.setHeaderHidden(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSortingEnabled(True)  # Enable sorting


        ## Use dialog box to get directory path
        path = self.get_directory_path()  # Use the dialog box to get the directory path
        if path is None:
            # User cancelled the dialog box
            return

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Select', 'Name', 'Size', 'Rating'])

        self.populate_tree(path)

        self.tree.setModel(self.model)
        self.setCentralWidget(self.tree)

        self.tree.sortByColumn(1, Qt.AscendingOrder)

        for column in range(self.model.columnCount()):
            self.tree.resizeColumnToContents(column)

        # Add a button to the window
        self.printButton = QPushButton("Convert selected videos", self)
        self.printButton.clicked.connect(self.convert_video)

        # Add checkboxes for 'Select All'
        self.selectAllCheckBox = QtWidgets.QCheckBox("Select All", self)
        self.selectAllCheckBox.stateChanged.connect(self.selectAllChanged)
        self.forceHQAllCheckBox = QtWidgets.QCheckBox("Force HQ All", self)
        self.forceHQAllCheckBox.stateChanged.connect(self.forceHQAllChanged)

        # Add 'Show in Finder' button
        self.showInFinderButton = QtWidgets.QPushButton("Show in Finder", self)
        self.showInFinderButton.clicked.connect(self.showInFinder)

        # Layout adjustments to include the checkboxes
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.selectAllCheckBox)
        layout.addWidget(self.forceHQAllCheckBox)
        layout.addWidget(self.tree)  # Your existing tree
        layout.addWidget(self.printButton)
        layout.addWidget(self.showInFinderButton)
        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def selectAllChanged(self, state):
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 0)  # 0 is the index for 'Select' column
            item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def forceHQAllChanged(self, state):
        for row in range(self.model.rowCount()):
            item = self.model.item(row, 3)  # 3 is the index for 'Force HQ' column
            item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def showInFinder(self):
        # Logic to open the selected directory in Finder or File Explorer
        directory = self.get_directory_path()  # Assuming this method returns the selected directory path
        if directory:
            if sys.platform == "darwin":
                subprocess.run(["open", directory])
            elif sys.platform == "win32":
                subprocess.run(["explorer", directory])
            else:  # Linux and other OS
                subprocess.run(["xdg-open", directory])

    def show_completion_dialog(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Video conversion completed.")
        msgBox.setInformativeText("Do you want to close the application?")
        msgBox.setStandardButtons(QMessageBox.Close)
        msgBox.buttonClicked.connect(self.close_application)

        returnValue = msgBox.exec()
        if returnValue == QMessageBox.Close:
            self.close_application()

    def close_application(self):
        QtWidgets.QApplication.quit()

    def convert_video(self):
        total_checked = sum(self.model.item(row, 0).checkState() == Qt.Checked for row in range(self.model.rowCount()))
        current_checked = 0

        for row in range(self.model.rowCount()):
            check_item = self.model.item(row, 0)  # 0 is the index for 'Select' column
            if check_item.checkState() == Qt.Checked:
                current_checked += 1
                file_name = self.model.item(row, 1).text()
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print(f"================Processing {file_name} - {current_checked}/{total_checked}================")
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)
                print("=" * 80)

                old_file_path = self.model.item(row, 16).text()
                renamed_old_file_path = self.model.item(row, 15).text()

                video_info = {
                    'video_codec': self.model.item(row, 7).text(),
                    'dimensions': self.model.item(row, 5).text(),
                    'video_bitrate': self.model.item(row, 8).text(),
                    'fps': self.model.item(row, 6).text(),
                    'duration_str': self.model.item(row, 4).text(),
                    'size_mb': self.model.item(row, 9).text(),
                    'rating': self.model.item(row, 2).text(),
                }

                force_hq = self.model.item(row, 3).checkState() == Qt.Checked  # Checking Force HQ checkbox
                export_settings = get_export_bitrate(video_info, force_hq)
                print(export_settings)

                new_file_path = convert_video_handbrake(old_file_path, export_settings)
                copy_exif_data(old_file_path, new_file_path)
                update_timestamp(old_file_path, new_file_path)

                success = rename_with_rollback(old_file_path, renamed_old_file_path, new_file_path)
                if success:
                    print("Both renaming operations completed successfully.")
                else:
                    print("Renaming operations failed or partially failed.")
        # After conversion is done, show a confirmation dialog
        self.show_completion_dialog()

    def get_directory_path(self):
        ##Logic to save the last used directory
        # Get the path to the hidden file
        home_dir = os.path.dirname(__file__)
        hidden_file_path = os.path.join(home_dir, ".compress_vid_last_dir")

        # Try to read the last used directory from the hidden file
        try:
            with open(hidden_file_path, "r") as f:
                last_dir = f.read().strip()
        except FileNotFoundError:
            last_dir = None

        # Open the file dialog and get the selected directory
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        if last_dir:
            dialog.setDirectory(last_dir)
        if dialog.exec_() == QFileDialog.Accepted:
            selected_dir = dialog.selectedFiles()[0]
            # Save the selected directory to the hidden file
            with open(hidden_file_path, "w") as f:
                f.write(selected_dir)
            return selected_dir
        else:
            return None

    def center_on_screen(self):
        # Get the screen resolution of your monitor
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        # Get the window size
        window_size = self.geometry()
        
        # Calculate the center position
        center_position = QtCore.QPoint(
            (resolution.width() - window_size.width()) // 2,
            (resolution.height() - window_size.height()) // 2
        )
        
        # Move the window to the center position
        self.move(center_position)


    
    def populate_tree(self, path):
        # Assuming get_export_bitrate and save_new_filename are defined 
        # and imported along with get_video_info and get_rating
        
        self.model.setHorizontalHeaderLabels([
            'Select', 'Name', 'Rating', 'Force HQ', 'Duration', 'Dimensions', 'FPS',
            'Codec', 'Bit Rate', 'Size (MB)', 'New Codec', 'New Bit Rate',
            'Est. New Size', 'Compression %', 'Converted File Name', 'Renamed Old File Name', 'Full File Path'
        ])

        grey_brush = QBrush(QColor(128, 128, 128))  # Grey color
        videos_list = parse_videos(path)
        rows_to_grey_out = []  # List to keep track of rows to grey out

        for entry in videos_list:
            video_info = get_video_info(entry)
            export_settings = get_export_bitrate(video_info)
            converted_file_data = estimate_new_file_size(video_info, export_settings)
            
            new_file_size = converted_file_data['new_file_size_mb']
            converted_file_name = save_new_filename(entry)
            renamed_old_file_name = old_file_new_name(entry)

            item_select = QStandardItem()
            item_select.setCheckable(True)
            item_select.setCheckState(Qt.Unchecked)

            item_force_hq = QStandardItem()
            item_force_hq.setCheckable(True)
            item_force_hq.setCheckState(Qt.Unchecked)

            # Populate the row with all the necessary items
            row_items = [
                item_select,
                QStandardItem(os.path.basename(entry)), #filename
                QStandardItem(str(video_info['rating'])), #rating
                item_force_hq, #force HQ
                QStandardItem(video_info['duration_str'].split('.')[0]), #duration
                QStandardItem(video_info['dimensions']), #dimensions
                QStandardItem(str(video_info['fps'])), #fps
                QStandardItem(video_info['video_codec']), #current codec
                QStandardItem(str(video_info['video_bitrate'])), #current bitrate
                QStandardItem(f"{video_info['size_mb']} MB"), #current size
                QStandardItem(export_settings['new_codec']), #new codec
                QStandardItem(str(export_settings['new_bitrate'])), #new bitrate
                QStandardItem(str(f'{new_file_size} MB')), #new size
                QStandardItem(converted_file_data['compression_ratio']), #compression ratio
                QStandardItem(converted_file_name), # new file name
                QStandardItem(renamed_old_file_name), #remaining file name
                QStandardItem(entry),# os.path.basename(entry)), #full path
            ]

            self.model.appendRow(row_items)

            base_name = os.path.splitext(os.path.basename(entry))[0]
            old_file_name = f"{base_name}_OLD"

            if any(old_file_name in file for file in videos_list):
                current_row = self.model.rowCount()
                rows_to_grey_out.append((current_row - 1, old_file_name))

        # Grey out the necessary rows
        for row_index, old_file_name in rows_to_grey_out:
            # Grey out the current file
            for col in range(self.model.columnCount()):
                self.model.item(row_index, col).setForeground(grey_brush)

            # Grey out the _OLD file
            for row in range(self.model.rowCount()):
                if self.model.item(row, 1).text().startswith(old_file_name):
                    for col in range(self.model.columnCount()):
                        self.model.item(row, col).setForeground(grey_brush)


    # def resize_columns(self):
    #     for column in range(self.model.columnCount()):
    #         self.tree.resizeColumnToContents(column)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.center_on_screen()  # Center the window on the screen
    window.show()
    app.exec_()