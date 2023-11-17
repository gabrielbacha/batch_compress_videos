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
    # print(" ".join(cmd))

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
    try:
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
    except:
        pass

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
    videos = []
    for root, dirs, files in os.walk(input_path):
        for f in files:
            if not f.startswith('.') and any(f.lower().endswith(ext) for ext in extensions):
                videos.append(os.path.join(root, f))
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
    counter = 1
    converted_file_name = f"{file_base}_OLD{file_extension}"
    # Check if the file exists and increment the counter until an unused name is found
    while os.path.exists(converted_file_name):
        converted_file_name = f"{file_base}_OLD {counter}{file_extension}"
        counter += 1
    
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
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QPushButton, QFileDialog, QMessageBox, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox 
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QFont
import os
import json
import sys
import subprocess

def resize_window(window):
    # Obtain the size of the screen
    screen = QtWidgets.QApplication.primaryScreen().geometry()

    # Calculate 80% of the screen width and convert to integer
    width = int(screen.width() * 0.8)
    height = int(screen.height() * 0.6)  # You can choose to keep the current height or set your own

    # Set the window size with integer width and height
    window.resize(width, height)

def centerWindowOnScreen(window):
    # Centers the window on the screen
    centerPoint = QtWidgets.QApplication.desktop().availableGeometry().center()
    frameGm = window.frameGeometry()
    frameGm.moveCenter(centerPoint)
    window.move(frameGm.topLeft())

class SubfolderSelectionDialog(QDialog):
    def __init__(self, root_folder, parent=None):
        super().__init__(parent)
        self.setup_window()
        self.setup_tree_view()
        self.populate_tree_with_root_and_subfolders(root_folder)
        self.setup_layout()

    def setup_window(self):
        self.setWindowTitle("Select Subfolders")
        resize_window(self)
        centerWindowOnScreen(self)

    def setup_tree_view(self):
        self.treeView = QTreeView(self)
        self.treeView.setHeaderHidden(False)
        self.treeView.setAlternatingRowColors(True)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Select", "Folder Name", "Full Path"])
        self.treeView.setModel(self.model)

    def populate_tree_with_root_and_subfolders(self, root_folder):
        self.add_folder_item(root_folder, checked=True)
        subfolders = self.get_subfolders(root_folder)
        for folder in subfolders:
            self.add_folder_item(folder)

    def get_subfolders(self, root_folder):
        return [os.path.join(root_folder, name) for name in os.listdir(root_folder)
                if os.path.isdir(os.path.join(root_folder, name))]

    def add_folder_item(self, folder_path, checked=False):
        select_item = QStandardItem()
        select_item.setCheckable(True)
        select_item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

        folder_name_item = QStandardItem(os.path.basename(folder_path))
        full_path_item = QStandardItem(folder_path)

        self.model.appendRow([select_item, folder_name_item, full_path_item])

    def setup_layout(self):
        self.treeView.expandAll()
        self.treeView.resizeColumnToContents(0)
        self.treeView.resizeColumnToContents(1)
        self.treeView.resizeColumnToContents(2)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.treeView)
        layout.addWidget(buttonBox)

    def selected_folders(self):
        selected_folders = []
        for row in range(self.model.rowCount()):
            if self.model.item(row, 0).checkState() == Qt.Checked:
                selected_folders.append(self.model.item(row, 2).text())
        return selected_folders


class MainWindow(QtWidgets.QMainWindow):
    COL_NAME = 0
    COL_SELECT = 1
    COL_FORCE_HQ = 2
    COL_RATING = 3
    COL_DURATION = 4
    COL_DIMENSIONS = 5
    COL_FPS = 6
    COL_CODEC = 7
    COL_BIT_RATE = 8
    COL_SIZE_MB = 9
    COL_NEW_CODEC = 10
    COL_NEW_BIT_RATE = 11
    COL_EST_NEW_SIZE = 12
    COL_COMPRESSION_PERCENT = 13
    COL_CONVERTED_FILE_NAME = 14
    COL_RENAMED_OLD_FILE_NAME = 15
    COL_FULL_FILE_PATH = 16

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.initTree()
        self.initButtonsAndCheckBoxes()
        self.setupLayout()
        resize_window(self)
        centerWindowOnScreen(self)

    def initTree(self):
        self.tree = QTreeView()
        self.tree.setHeaderHidden(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSortingEnabled(True)

        self.model = QStandardItemModel()
        self.model.itemChanged.connect(self.onItemChanged)
        self.tree.setModel(self.model)

        path = self.get_directory_path()
        if path:
            if not self.has_subfolders(path):
                self.populate_tree(path)
            else:
                selected_folders = self.get_subfolder_selection(path)
                for folder in selected_folders:
                    self.populate_tree(folder)  # Assuming populate_tree can handle individual folders
        
        # Auto-size columns
        self.tree.resizeColumnToContents(self.COL_NAME)  
        self.tree.resizeColumnToContents(self.COL_CONVERTED_FILE_NAME)  
        self.tree.resizeColumnToContents(self.COL_RENAMED_OLD_FILE_NAME)  
        self.tree.resizeColumnToContents(self.COL_FULL_FILE_PATH)  
        
        #Sort by column
        self.tree.sortByColumn(self.COL_NAME, Qt.AscendingOrder)

    def initButtonsAndCheckBoxes(self):
        self.printButton = QPushButton("Convert selected videos", self)
        self.printButton.clicked.connect(self.convert_video)

        self.selectAllCheckBox = QtWidgets.QCheckBox("Select All", self)
        self.selectAllCheckBox.stateChanged.connect(self.selectAllChanged)

        self.forceHQAllCheckBox = QtWidgets.QCheckBox("Force HQ All", self)
        self.forceHQAllCheckBox.stateChanged.connect(self.forceHQAllChanged)

        self.deleteConvertedVideosCheckBox = QtWidgets.QCheckBox("Delete Converted Videos", self)
        self.deleteConvertedVideosCheckBox.stateChanged.connect(self.deleteConvertedVideosChanged)
        self.delete_converted_videos = False

        self.showInFinderButton = QtWidgets.QPushButton("Show in Finder", self)
        self.showInFinderButton.clicked.connect(self.showInFinder)

    def setupLayout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.selectAllCheckBox)
        layout.addWidget(self.forceHQAllCheckBox)
        layout.addWidget(self.deleteConvertedVideosCheckBox)
        layout.addWidget(self.tree)
        layout.addWidget(self.printButton)
        layout.addWidget(self.showInFinderButton)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def has_subfolders(self, path):
        return any(os.path.isdir(os.path.join(path, name)) for name in os.listdir(path))

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
        
    def get_subfolder_selection(self, root_folder):
        dialog = SubfolderSelectionDialog(root_folder, self)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selected_folders()
        else:
            return []

    
    def selectAllChanged(self, state):
        for row in range(self.model.rowCount()):
            folder_item = self.model.item(row)
            for child_row in range(folder_item.rowCount()):
                item = folder_item.child(child_row, self.COL_SELECT)
                if item is not None and item.isCheckable():
                    item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def forceHQAllChanged(self, state):
        for row in range(self.model.rowCount()):
            folder_item = self.model.item(row)
            for child_row in range(folder_item.rowCount()):
                item = folder_item.child(child_row, self.COL_FORCE_HQ)  # 3 is the index for 'Force HQ' column
                if item is not None and item.isCheckable():
                    item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def deleteConvertedVideosChanged(self, state):
        self.delete_converted_videos = state == Qt.Checked

    def select_all_for_folder(self, folder_item, state):
        for row in range(folder_item.rowCount()):
            item = folder_item.child(row, self.COL_SELECT)
            if item is not None and item.isCheckable():
                item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def force_hq_all_for_folder(self, folder_item, state):
        for row in range(folder_item.rowCount()):
            item = folder_item.child(row, self.COL_FORCE_HQ)
            if item is not None and item.isCheckable():
                item.setCheckState(Qt.Checked if state == Qt.Checked else Qt.Unchecked)

    def onItemChanged(self, item):
    # Check if the changed item is a folder-level checkbox
        if item.column() in [self.COL_SELECT, self.COL_FORCE_HQ]:
            folder_item = item.data(Qt.UserRole)
            if folder_item:
                if item.column() == self.COL_SELECT:
                    self.select_all_for_folder(folder_item, item.checkState())
                elif item.column() == self.COL_FORCE_HQ:
                    self.force_hq_all_for_folder(folder_item, item.checkState())
    
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

    def get_total_checked_videos(self):
        total_checked = 0
        for folder_row in range(self.model.rowCount()):
            folder_item = self.model.item(folder_row)
            for video_row in range(folder_item.rowCount()):
                if self.is_video_selected(folder_item, video_row):
                    total_checked += 1
        return total_checked

    def convert_video(self):
        total_checked = self.get_total_checked_videos()
        if total_checked == 0:
            QMessageBox.information(self, "No Videos Selected", "Please select videos to convert.")
            return

        current_checked = 0
        for folder_row in range(self.model.rowCount()):
            folder_item = self.model.item(folder_row)
            for video_row in range(folder_item.rowCount()):
                if self.is_video_selected(folder_item, video_row):  # Adjusted to check within folder
                    current_checked += 1
                    file_name = self.get_item_text(folder_item, video_row, self.COL_NAME)
                    self.print_conversion_header(file_name, current_checked, total_checked)

                    try:
                        self.process_video(folder_item, video_row)  # Adjusted to process within folder
                    except Exception as e:
                        print(f"Error processing {file_name}: {e}")
                        continue

        self.show_completion_dialog()

    def is_video_selected(self, folder_item, row):
        check_item = folder_item.child(row, self.COL_SELECT)
        return check_item and check_item.checkState() == Qt.Checked

    def get_item_text(self, folder_item, row, column):
        item = folder_item.child(row, column)
        return item.text() if item else ""

    def print_conversion_header(self, file_name, current, total):
        header_line = "=" * 100 + "\n"
        print(f"{header_line *10}{'=' * 29} Processing {file_name} - {current}/{total} {'=' * 29}\n{header_line *10}")

    def process_video(self, folder_item, row):
        # Retrieve the full file path from the folder item and row index
        old_file_path = self.get_item_text(folder_item, row, self.COL_FULL_FILE_PATH)
        renamed_old_file_path = self.get_item_text(folder_item, row, self.COL_RENAMED_OLD_FILE_NAME)
        video_info = self.extract_video_info(folder_item, row)
        force_hq = folder_item.child(row, self.COL_FORCE_HQ).checkState() == Qt.Checked


        export_settings = get_export_bitrate(video_info, force_hq)
        print(export_settings)

        new_file_path = convert_video_handbrake(old_file_path, export_settings)
        copy_exif_data(old_file_path, new_file_path)
        update_timestamp(old_file_path, new_file_path)

        success = rename_with_rollback(old_file_path, renamed_old_file_path, new_file_path)
        print("Renaming operations completed successfully." if success else "Renaming operations failed or partially failed.")

        if self.delete_converted_videos:
            self.delete_original_file(renamed_old_file_path)
            print(f"Deleted original file: {renamed_old_file_path}")

    def delete_original_file(self, file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e.strerror}")
    
    def extract_video_info(self, folder_item, row):
        return {
            'video_codec': self.get_item_text(folder_item, row, self.COL_CODEC),
            'dimensions': self.get_item_text(folder_item, row, self.COL_DIMENSIONS),
            'video_bitrate': self.get_item_text(folder_item, row, self.COL_BIT_RATE),
            'fps': self.get_item_text(folder_item, row, self.COL_FPS),
            'duration_str': self.get_item_text(folder_item, row, self.COL_DURATION),
            'size_mb': self.get_item_text(folder_item, row, self.COL_SIZE_MB),
            'rating': self.get_item_text(folder_item, row, self.COL_RATING),
        }

    def populate_tree(self, path):
        self.setup_tree_headers()
        folder_structure = self.build_folder_structure(path)
        self.populate_folders(folder_structure)
        # Grey out old versions
        self.update_row_styles()

    def setup_tree_headers(self):
        headers = [
            'Name', 'Select', 'Force HQ', 'Rating',  'Duration', 'Dimensions', 'FPS',
            'Codec', 'Bit Rate', 'Size (MB)', 'New Codec', 'New Bit Rate',
            'Est. New Size', 'Compression %', 'Converted File Name', 
            'Renamed Old File Name', 'Full File Path'
        ]
        self.model.setHorizontalHeaderLabels(headers)

    def build_folder_structure(self, path):
        folder_structure = {}
        videos_list = parse_videos(path)
        for video_path in videos_list:
            folder_path = os.path.dirname(video_path)
            folder_structure.setdefault(folder_path, []).append(video_path)
        return folder_structure

    def populate_folders(self, folder_structure):
        for folder, videos in folder_structure.items():
            folder_item = QStandardItem(os.path.basename(folder))

            # Folder-level 'Select All' checkbox
            select_all_item = QStandardItem()
            select_all_item.setCheckable(True)
            select_all_item.setCheckState(Qt.Unchecked)

            # Folder-level 'Force HQ All' checkbox
            force_hq_all_item = QStandardItem()
            force_hq_all_item.setCheckable(True)
            force_hq_all_item.setCheckState(Qt.Unchecked)

            folder_row_items = [
                folder_item,  # Folder name
                select_all_item,  # Select All checkbox
                force_hq_all_item  # Force HQ All checkbox
            ]
            
            # Store the folder item in the checkbox items for later reference
            select_all_item.setData(folder_item, Qt.UserRole)
            force_hq_all_item.setData(folder_item, Qt.UserRole)
            
            self.model.appendRow(folder_row_items)
            folder_index = self.model.indexFromItem(folder_item)
            self.tree.expand(folder_index)  # Expands the folder row

            for video in videos:
                video_row_items = self.create_video_row_items(video)
                folder_item.appendRow(video_row_items)
    
    def format_columns(self, video_row_items):
        for col, item in enumerate(video_row_items):
            # Apply bold font to certain columns
            if col in [self.COL_RATING, self.COL_NEW_BIT_RATE, self.COL_EST_NEW_SIZE, self.COL_COMPRESSION_PERCENT, self.COL_BIT_RATE, self.COL_SIZE_MB]:
                self.apply_bold_font(item)

            # Apply color to certain columns
            if col in [self.COL_NEW_BIT_RATE, self.COL_EST_NEW_SIZE, self.COL_COMPRESSION_PERCENT]:
                item.setForeground(QBrush(QColor('green')))
            elif col in [self.COL_BIT_RATE, self.COL_SIZE_MB]:
                item.setForeground(QBrush(QColor('red')))

            # Grey out certain columns
            if col in [self.COL_DURATION, self.COL_DIMENSIONS, self.COL_FPS, self.COL_CODEC, self.COL_NEW_CODEC]:
                item.setForeground(QBrush(QColor('grey')))

    def apply_bold_font(self, item):
        font = QFont()
        font.setBold(True)
        item.setFont(font)

    def update_row_styles(self):
        grey_brush = QBrush(QColor('grey'))
        font = QFont()
        font = QFont()
        font.setStrikeOut(True)

        for folder_row in range(self.model.rowCount()):
            folder_item = self.model.item(folder_row)
            for video_row in range(folder_item.rowCount()):
                video_item = folder_item.child(video_row, self.COL_NAME)
                base_name, _ = os.path.splitext(video_item.text())
                old_file_name = f"{base_name}_OLD"

                compression_ratio_item = folder_item.child(video_row, self.COL_COMPRESSION_PERCENT)
                compression_ratio = self.parse_compression_ratio(compression_ratio_item.text()) if compression_ratio_item else 100.0

                if self.check_old_file_exists(folder_item, old_file_name):
                    self.update_row_style(folder_item, video_row, grey_brush, font)
                    if old_file_name:
                        self.update_row_style_for_old_file(folder_item, old_file_name, grey_brush, font)
                elif compression_ratio < 10.0:
                    self.update_row_style(folder_item, video_row, grey_brush, font)

    def check_old_file_exists(self, folder_item, old_file_name):
        for row in range(folder_item.rowCount()):
            item = folder_item.child(row, self.COL_NAME)
            if item and old_file_name in item.text():
                return True
        return False

    def parse_compression_ratio(self, ratio_str):
        try:
            return float(ratio_str.rstrip('%'))
        except ValueError:
            return 100.0

    def update_row_style(self, folder_item, row, brush, font):
        for col in range(self.model.columnCount()):
            item = folder_item.child(row, col)
            if item:
                item.setForeground(brush)
                item.setFont(font)

    def update_row_style_for_old_file(self, folder_item, old_file_name, brush, font):
        for row in range(folder_item.rowCount()):
            item = folder_item.child(row, self.COL_NAME)
            if item and old_file_name in item.text():
                self.update_row_style(folder_item, row, brush, font)

    def create_video_row_items(self, video):
        video_info = get_video_info(video)
        export_settings = get_export_bitrate(video_info)
        converted_file_data = estimate_new_file_size(video_info, export_settings)
        new_file_size = converted_file_data['new_file_size_mb']
        converted_file_name = save_new_filename(video)
        renamed_old_file_name = old_file_new_name(video)

        item_select = QStandardItem()
        item_select.setCheckable(True)
        item_select.setCheckState(Qt.Unchecked)

        item_force_hq = QStandardItem()
        item_force_hq.setCheckable(True)
        item_force_hq.setCheckState(Qt.Unchecked)

        # Populate the row with all the necessary items
        video_row_items = [
                        
            QStandardItem(os.path.basename(video)), #filename
            item_select,
            item_force_hq, #force HQ
            QStandardItem(str(video_info['rating'])), #rating
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
            QStandardItem(video),# os.path.basename(video)), #full path
        ]
        
        # Apply formatting to the row items
        self.format_columns(video_row_items)
        
        return video_row_items

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()