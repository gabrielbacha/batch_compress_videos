import subprocess
import datetime
import os

ffmpeg_settings = {
    ('4k', '30'): {
        'codec': 'vt_h265',
        'bitrate': '30',
        'profile': 'high',
        'level': '5.1',
        'handbrake_quality': '18'
    },
    ('4k', '60'): {
        'codec': 'vt_h265',
        'bitrate': '35',
        'profile': 'high',
        'level': '5.1',
        'handbrake_quality': '18'
    },
    ('1080p', '30'): {
        'codec': 'vt_h265',
        'bitrate': '10',
        'profile': 'high',
        'level': '5.1',
        'handbrake_quality': '22'
    },
    ('1080p', '60'): {
        'codec': 'vt_h265',
        'bitrate': '12.5',
        'profile': 'high',
        'level': '5.1',
        'handbrake_quality': '22'
    }
}

testfile="./test/DJI_0021.MP4"
testdir="./test"

###############



def get_video_info(input_path):
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

    # Execute the ffprobe command
    output = subprocess.check_output(cmd).decode('utf-8').strip().split('\n')

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
    bitrate_mbps = "N/A"
    if bitrate and bitrate.isdigit():
        bitrate_mbps = round(int(bitrate) / 1e6, 1)

    # Formatting file size as MB
    size_mb = round(int(file_size) / 1e6, 1)

    # Formatting duration as HH:MM:SS
    duration_str = str(datetime.timedelta(seconds=duration))

    # Returning the information as a tuple
    return video_codec, dimensions, bitrate_mbps, fps, duration_str, size_mb

# get_video_info(testfile)


def get_export_settings(input_path):
    # Use the get_video_info function to get video parameters
    video_codec, dimensions, bitrate_mbps, fps, duration_str, size_mb = get_video_info(input_path)
    
    # Determine resolution based on dimensions
    width, height = map(int, dimensions.split('x'))
    resolution = None
    if (width >= 3840 and height >= 2160) or (width >= 2160 and height >= 3840):  # Handling both landscape and portrait 4K
        resolution = '4k'
    elif (width >= 1920 and height >= 1080) or (width >= 1080 and height >= 1920):  # Handling both landscape and portrait 1080p
        resolution = '1080p'

    # Round fps to the nearest whole number to match against '30' or '60'
    frame_rate = str(round(fps / 30) * 30)  # This will convert fps to either '30' or '60'

    # Use resolution and frame rate to get the correct settings from the dictionary
    settings = ffmpeg_settings.get((resolution, frame_rate))

    return settings

# get_export_settings(testfile)

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

# bitrate_to_size("00:01:00", 5.0)

def estimate_new_file_size(input_path):
    global settings
    # Get video information
    video_codec, dimensions, bitrate_mbps, fps, duration_str, size_mb = get_video_info(input_path)

    # Get export settings
    settings = get_export_settings(input_path)

    # If no matching settings found, return "N/A"
    if not settings:
        return "N/A"

    # Get bitrate from settings
    bitrate_mbps = float(settings.get('bitrate'))

    # Estimate new file size
    new_file_size_mb = round(bitrate_to_size(duration_str, bitrate_mbps),1)

    # Calculate compression ratio
    compression_ratio = 1 - (new_file_size_mb / size_mb)

    return new_file_size_mb, bitrate_mbps, size_mb, f'{round(compression_ratio * 100, 1)}%'

# estimate_new_file_size(testfile)


def parse_videos(input_path):
    extensions = ['.mp4', '.mkv', '.avi', 'mov']
    videos = [os.path.join(input_path, f) for f in os.listdir(input_path) if any(f.lower().endswith(ext) for ext in extensions)]
    return videos

# parse_videos(testdir)


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

# save_new_filename(testfile)

def get_rating(file_path):
    # Command to get the rating using exiftool
    rating_cmd = ['exiftool', '-XMP:Rating', file_path]

    # Run the command and capture the output
    completed_process = subprocess.run(rating_cmd, stdout=subprocess.PIPE, text=True)

    # Check if the command was successful
    if completed_process.returncode == 0:
        # Extract the rating from the output
        output = completed_process.stdout.strip()

        # Assume output format: "XMP:Rating                        : <RatingValue>"
        # Split the output and get the last element, which should be the rating
        rating = output.split(':')[-1].strip()

        return rating
    else:
        # Handle error if exiftool failed
        print("Error: exiftool did not complete successfully.")
        return None

def convert_video_handbrake(input_file):
    output_file = save_new_filename(input_file)  ## to change to replace existing file name #TODO
    estimate_new_file_size(input_file)  #TODO check if best way to get settings
    # Build the HandbrakeCLI command
    cmd = [
        'HandBrakeCLI',
        '-i', input_file,
        '-o', output_file,
        '-e', settings['codec'],
        '-b', str(float(settings['bitrate'])*1000),  # Average bitrate
        '-f', 'mp4',
        '--encopts', 'keyint=60',
        '--optimize',
        '--cfr',  # Constant frame rate
        '--keep-display-aspect',  # Maintain aspect ratio
        # '--encoder-profile', settings['profile'],
        # '--encoder-level', settings['level'],
    ]

    # Execute the command
    print(" ".join(cmd))
    # subprocess.run(cmd) #TODO
    print(f'FAKE PROCESSED {input_file}')
    print(get_video_info(input_file))
    # print(get_video_info(output_file))

# convert_video_handbrake(testfile)








from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt
import os

class MainWindow(QMainWindow):
    def __init__(self, path):
        super().__init__()

        self.tree = QTreeView()
        self.tree.setHeaderHidden(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)

        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Select', 'Name', 'Size', 'Rating'])

        self.populate_tree(path)

        self.tree.setModel(self.model)
        self.setCentralWidget(self.tree)

        self.tree.expanded.connect(self.resize_columns)
        self.tree.collapsed.connect(self.resize_columns)

    def populate_tree(self, path):
        for entry in parse_videos(path):
            rating = get_rating(entry)
            size = os.stat(entry).st_size
            if size >= 1024**3:
                size_str = f"{size / 1024**3:.1f} GB"
            elif size >= 1024**2:
                size_str = f"{size / 1024**2:.1f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"

            item_select = QStandardItem()
            item_select.setCheckable(True)
            item_select.setCheckState(Qt.Unchecked)
            
            item_name = QStandardItem(entry)
            item_size = QStandardItem(size_str)
            item_rating = QStandardItem(str(rating))
            
            self.model.appendRow([item_select, item_name, item_size, item_rating])

    def resize_columns(self):
        for column in range(self.model.columnCount()):
            self.tree.resizeColumnToContents(column)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = MainWindow(testdir)  # Replace with the actual path when integrating into the notebook
    window.show()
    sys.exit(app.exec_())
