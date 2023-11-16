import subprocess

def copy_exif_data(original_file, new_file):
    try:
        exif_copy_cmd = ['exiftool', '-TagsFromFile', original_file, '-all:all', '-overwrite_original', new_file]
        subprocess.run(exif_copy_cmd)
        print(f"EXIF data copied from {original_file} to {new_file}")
    except Exception as e:
        print(f"Failed to copy EXIF data: {e}")

def match_file_creation_date(original_file, new_file):
    try:
        subprocess.run(['touch', '-r', original_file, new_file])
        print(f"Creation date matched from {original_file} to {new_file}")
    except Exception as e:
        print(f"Failed to match file creation date: {e}")


match_file_creation_date("/Users/bachagabriel/Download/ALL_VIDEO_TESTS/FINALTEST/2018-01-04 16.48 El Calafate wind on wheat.MP4", "/Users/bachagabriel/Download/ALL_VIDEO_TESTS/FINALTEST/265 calafate.mp4")