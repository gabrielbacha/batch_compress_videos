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

def process_video_server(video_path):
    # Check if the video filename contains "_OLD"
    if '_OLD' in os.path.basename(video_path):
        print(f"Skipping {video_path} as it is marked as an _OLD file.")
        return

    # Check if a corresponding _OLD file exists
    base, ext = os.path.splitext(video_path)
    old_file = base + '_OLD' + ext
    if os.path.exists(old_file):
        print(f"Skipping {video_path} as an _OLD version already exists.")
        return

    # Extract video information
    video_info = get_video_info(video_path)
    if not video_info:
        print(f"Failed to retrieve info for {video_path}. Skipping.")
        return

    # Get export settings
    export_settings = get_export_bitrate(video_info)

    # Estimate new file size and compression ratio
    converted_file_data = estimate_new_file_size(video_info, export_settings)
    if converted_file_data == "N/A":
        print(f"Failed to estimate file size for {video_path}. Skipping.")
        return

    compression_ratio = converted_file_data['compression_ratio'].rstrip('%')
    if compression_ratio and float(compression_ratio) < 10:
        print(f"Skipping {video_path} due to low compression ratio ({compression_ratio}%).")
        return

    # Convert the video
    new_file_path = convert_selected_video(video_path, export_settings, use_ffmpeg=False, use_codec='mac')

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