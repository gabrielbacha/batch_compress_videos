import subprocess
import datetime
import os
from compress_vid import *


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




# def get_video_info(input_path):
#     ## FFPROBE INFO
#     # ffprobe command to get video codec, dimensions, bitrate, fps, duration, and file size
#     cmd = [
#         'ffprobe',
#         '-v', 'error',
#         '-select_streams', 'v:0',
#         '-show_entries', 'stream=codec_name,width,height,bit_rate,r_frame_rate',
#         '-show_entries', 'format=duration,size',  # Including format=size to get the file size
#         '-of', 'default=noprint_wrappers=1:nokey=1',
#         input_path
#     ]
#     print("Pulling video information...")
#     # print(" ".join(cmd))

#     # Execute the ffprobe command
#     try:
#         output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8').strip().split('\n')
#     except subprocess.CalledProcessError as e:
#         print(f"Error: {e.output.decode('utf-8')}")
#         output = ['h264', '1', '1', '1/1', '1', '1', '1']

#     # Extracting the information from the output
#     video_codec = output[0]
#     width = output[1]
#     height = output[2]
#     bitrate = output[4]
#     fps_frac = output[3]
#     duration = float(output[5])
#     file_size = output[6]  # Corrected file size index

#     # Calculating FPS from the fractional representation
#     fps = "N/A"
#     if fps_frac:
#         try:
#             numerator, denominator = map(int, fps_frac.split('/'))
#             fps = round(float(numerator) / float(denominator), 2)
#         except ValueError:
#             # Handle the case where the FPS is not a fraction (which is rare)
#             fps = float(fps_frac)

#     # Formatting dimensions
#     dimensions = f"{width}x{height}"

#     # Formatting bitrate as Mb/s if bitrate is available
#     video_bitrate = "N/A"
#     if bitrate and bitrate.isdigit():
#         video_bitrate = round(int(bitrate) / 1e6, 1)

#     # Formatting file size as MB
#     size_mb = round(int(file_size) / 1e6, 1)

#     # Formatting duration as HH:MM:SS
#     duration_str = str(datetime.timedelta(seconds=duration))

#     ##RATING
#     # Command to get the rating using exiftool
#     rating_cmd = ['exiftool', '-XMP:Rating', input_path]

#     # Run the command and capture the output
#     completed_process = subprocess.run(rating_cmd, stdout=subprocess.PIPE, text=True)

#     # Check if the command was successful
#     if completed_process.returncode == 0:
#         # Extract the rating from the output
#         output = completed_process.stdout.strip()

#         # Assume output format: "XMP:Rating                        : <RatingValue>"
#         # Split the output and get the last element, which should be the rating
#         rating = output.split(':')[-1].strip()

#     else:
#         # Handle error if exiftool failed
#         print("Error: exiftool did not complete successfully.")
#         return None

#      # Constructing the dictionary with the video information
#     video_info = {
#         'video_codec': video_codec,
#         'dimensions': dimensions,
#         'video_bitrate': video_bitrate,
#         'fps': fps,
#         'duration_str': duration_str,
#         'size_mb': size_mb,
#         'rating': rating
#     }

#     # Returning the constructed dictionary
#     return video_info

# # get_video_info(testfile)

# def get_export_bitrate(video_info, force_hq=False):
#     # Use the get_video_info function to get video parameters
#     print("Getting export settings...")
#     try:
#         dimensions = video_info['dimensions']
#         fps = video_info['fps']
#         codec = 'vt_h265'
#         video_bitrate = video_info['video_bitrate']
#         rating_str = video_info['rating']
#         # Default quality
#         quality = 'LQ'
#         # Override quality if HQ is forced
#         if force_hq:
#             quality = 'HQ'
#     except:
#         pass

#     # Attempt to convert the rating to an integer if it's numeric
#     try:
#         rating = int(rating_str)
#         if rating >= 5:
#             quality = 'HQ'
#     except ValueError:
#         # If it's not a number, keep the default quality
#         pass
    
#     # Determine resolution based on dimensions
#     width, height = map(int, dimensions.split('x'))
#     resolution = None
#     if (width >= 3840 and height >= 2160) or (width >= 2160 and height >= 3840):  # Handling both landscape and portrait 4K
#         resolution = '4k'
#     elif (width >= 1920 and height >= 1080) or (width >= 1080 and height >= 1920):  # Handling both landscape and portrait 1080p
#         resolution = '1080p'

#     # Round fps to the nearest whole number to match against '30' or '60', 24 & 25 are considered 30
#     if float(fps) <= 30:
#         frame_rate = '30'
#     else:
#         frame_rate = str(round(float(fps) / 30) * 30)

#     # Use resolution and frame rate to get the correct settings from the dictionary
#     try:
#         export_settings = {
#             "new_bitrate": str(min(float(ffmpeg_settings.get(resolution, {}).get(str(frame_rate), {}).get(codec, {}).get(quality)), float(video_bitrate))),
#             "new_codec":list(ffmpeg_settings.get(resolution, {}).get(str(frame_rate)).keys())[0]
#             }
#     except:
#         export_settings = {
#             "new_bitrate": "1",
#             "new_codec": "vt_h265"
#             }

#     return export_settings

# def parse_videos(input_path):
#     print("Parsing videos in folder...")
#     extensions = ['.mp4', '.mkv', '.avi', '.mov']
#     videos = []
#     for root, dirs, files in os.walk(input_path):
#         for f in files:
#             if not f.startswith('.') and any(f.lower().endswith(ext) for ext in extensions):
#                 videos.append(os.path.join(root, f))
#     return videos

# def save_new_filename(input_filedir):
#     dir_name = os.path.dirname(input_filedir)
#     file_name = os.path.splitext(os.path.basename(input_filedir))[0]
#     extension = '.mp4'  # Since we want to convert all files to mp4
#     counter = 1

#     output_filedir = os.path.join(dir_name, f"{file_name}{extension}")

#     while os.path.exists(output_filedir):
#         output_filedir = os.path.join(dir_name, f"{file_name} {counter}{extension}")
#         counter += 1
#     return output_filedir

# def convert_video_handbrake(input_file, export_settings):
#     print("Converting video...")
#     output_file = save_new_filename(input_file)
#     # Build the HandbrakeCLI command
#     cmd = [
#         'HandBrakeCLI',
#         '-i', input_file,
#         '-o', output_file,
#         '-e', export_settings['new_codec'],
#         '-b', str(float(export_settings['new_bitrate'])*1000),  # Average bitrate
#         '-f', 'mp4',
#         '--encopts', 'keyint=60',
#         '--optimize',
#         '--cfr',  # Constant frame rate
#         '--keep-display-aspect',  # Maintain aspect ratio
#     ]
    
#     ## Build the ffmpeg command
#     # cmd = [
#     #     'ffmpeg',
#     #     '-i', input_file,
#     #     '-c:v', "hevc_videotoolbox",
#     #     '-b:v', f"{float(export_settings['new_bitrate']) * 1000}k",  # Bitrate in kbps
#     #     '-f', 'mp4',
#     #     '-g', '60',  # Keyframe interval
#     #     '-vsync', 'cfr',  # Constant frame rate
#     #     '-map_metadata', '0',
#     #     output_file
#     # ]


#     # Execute the command
#     print(" ".join(cmd))
#     subprocess.run(cmd)
#     # print(f'FAKE PROCESSED {input_file}')
#     return output_file

# import subprocess

# def copy_exif_data(original_file, new_file):
#     # Keys to copy
#     keys = {
#         'XMP:Rating': 'Rating',
#         'XML:DeviceManufacturer': 'Make',
#         'XML:DeviceModelName': 'Model',
#         'XML:DeviceSerialNo': 'SerialNumber',
#         'QuickTime:CameraLensModel': 'LensModel',
#         'QuickTime:CameraFocalLength35mmEquivalent': 'FocalLengthIn35mmFilm',
#         'QuickTime:Make': 'Make',
#         'QuickTime:Model': 'Model',
#         'QuickTime:Software': 'Software',
#         'QuickTime:CreateDate': 'DateTimeOriginal',
#         'Composite:GPSAltitude': 'GPSAltitude',
#         'Composite:GPSAltitudeRef': 'GPSAltitudeRef',
#         'Composite:GPSLatitude': 'GPSLatitude',
#         'Composite:GPSLongitude': 'GPSLongitude',
#         'Composite:Rotation': 'Rotation'    
#     }

#     simplified_keys = {key.split(':')[1]: value for key, value in keys.items()}

#     # Read EXIF data from the original file
#     command_read = ['exiftool', '-json', original_file]
#     result = subprocess.run(command_read, capture_output=True, text=True)
#     exif_data = json.loads(result.stdout)[0]

#     print("Copying exif data...")

#     updated_keys_values = []
    
#     command_write = ['exiftool', '-P', '-overwrite_original']

#     for full_key, simple_key in simplified_keys.items():
#         if full_key in exif_data:
#             value = exif_data[full_key]
#             if isinstance(value, str) and value.strip() == '':
#                 continue  # Skip empty string values
#             # print(f'{full_key}:{value}:{simple_key}')
#             command_write.append(f'-{simple_key}={value}')
#             updated_keys_values.append((simple_key, value))


#     command_write.append(new_file)
#     # print(" ".join(command_write)) 
#     result = subprocess.run(command_write, capture_output=True, text=True)

#     # Check the first line of the output to determine if the file was updated
#     first_line = result.stdout.split('\n')[0] if result.stdout else ''
#     if "1 image files updated" in first_line:
#         print("The following keys and values have been updated:")
#         for key, value in updated_keys_values:
#             print(f'Updated {key} to {value}')
#     else:
#         print("No updates were made.")
#         if result.stderr:
#             print("Error:", result.stderr)

#     print("Exif data copied.")
#     return exif_data

# def update_timestamp(original_file, new_file):
#     print(f"Updating timestamp for: {os.path.basename(new_file)}")

#     # Get the original creation time for comparison
#     read_create_date = subprocess.run(['stat', '-f', '%SB', original_file], capture_output=True, text=True)
#     # print(read_create_date.stdout.strip())
#     # Convert the birth time string to a datetime object
#     original_timestamp = datetime.datetime.strptime(read_create_date.stdout.strip(), "%b %d %H:%M:%S %Y")
#     print(f"Original (_OLD) file timestamp: {original_timestamp}")

#     # Try to get 'Create Date' from EXIF data
#     command = ['exiftool', '-CreateDate', '-d', '%Y:%m:%d %H:%M:%S', original_file]
#     result = subprocess.run(command, capture_output=True, text=True)
#     create_date_str = result.stdout.strip().split(': ')[-1]  # Extract the date part
#     print(f"{os.path.basename(original_file)} create date is {create_date_str}")

#     if create_date_str:
#         # Parse the 'Create Date' string into a datetime object
#         try:
#             create_date = datetime.datetime.strptime(create_date_str, '%Y:%m:%d %H:%M:%S')
#             # Update the creation date using SetFile
#             formatted_date = create_date.strftime("%m/%d/%Y %H:%M:%S")
#             setfile_command = ['SetFile', '-d', formatted_date, new_file]
#             subprocess.run(setfile_command, check=True)
#             print(f"'Create Date' set to: {formatted_date} based on EXIF DATA")
#         except ValueError:
#             print("Invalid EXIF 'Create Date'. Using fallback method.")
#             # Fallback method using touch -r
#             touch_command = ['touch', '-r', original_file, new_file]
#             subprocess.run(touch_command, check=True)
#             print(f"'Create Date' updated using touch -r from {original_file}")
#     else:
#         # Fallback to the original file's creation time using touch -r
#         touch_command = ['touch', '-r', original_file, new_file]
#         subprocess.run(touch_command, check=True)
#         print(f"EXIF data not found. 'Create Date' updated using touch -r from {original_file}")

# def old_file_new_name(input_path):
#     file_base, file_extension = os.path.splitext(input_path)
#     counter = 1
#     converted_file_name = f"{file_base}_OLD{file_extension}"
#     # Check if the file exists and increment the counter until an unused name is found
#     while os.path.exists(converted_file_name):
#         converted_file_name = f"{file_base}_OLD {counter}{file_extension}"
#         counter += 1
    
#     return converted_file_name

# def rename_file(input_path, new_name):
#     try:
#         directory = os.path.dirname(input_path)
#         original_extension = os.path.splitext(input_path)[1]
#         new_name_without_extension = os.path.splitext(new_name)[0]
#         new_file_path = os.path.join(directory, new_name_without_extension + original_extension)
#         os.rename(input_path, new_file_path)
#         print(f"Renamed {os.path.basename(input_path)} to {os.path.basename(new_file_path)}")
#         return True
#     except Exception as e:
#         print(f"Failed to rename {os.path.basename(input_path)}: {e}")
#         return False

# def rename_with_rollback(original_file_path, intermediate_file_path, final_file_path):
#     # First, rename the original file to the intermediate path
#     if rename_file(original_file_path, intermediate_file_path):
#         # If the first rename succeeds, try the second rename
#         if rename_file(final_file_path, original_file_path):
#             return True
#         else:
#             # If the second rename fails, rollback the first rename
#             print("Second renaming operation failed, rolling back the first rename.")
#             rename_file(intermediate_file_path, original_file_path)
#     else:
#         print("First renaming operation failed.")
#     return False




###


def main():
    input_folder = input("Enter the path to the folder containing videos: ")
    if not os.path.exists(input_folder):
        print("The specified folder does not exist.")
        return

    videos = parse_videos(input_folder)
    if not videos:
        print("No video files found in the specified folder.")
        return

    for video in videos:
        process_video_server(video)

def process_video_server(video_path, force_hq=False):
    # Extract video information
    video_info = get_video_info(video_path)
    if not video_info:
        print(f"Failed to retrieve info for {video_path}. Skipping.")
        return

    # Get export settings
    export_settings = get_export_bitrate(video_info, force_hq=force_hq)

    # Convert the video
    new_file_path = convert_video_handbrake(video_path, export_settings)

    # Copy EXIF data to the new file
    copy_exif_data(video_path, new_file_path)

    # Update the timestamp of the new file
    update_timestamp(video_path, new_file_path)

    # Rename the original file with a backup name
    renamed_old_file_path = old_file_new_name(video_path)

    # Rename files with rollback on failure
    if rename_with_rollback(video_path, renamed_old_file_path, new_file_path):
        print(f"Successfully processed and renamed {video_path}")
    else:
        print(f"Failed to process {video_path}")



if __name__ == "__main__":
    main()