- Checkbox
- --name
- --rating
- duration = duration_str
- dimensions = dimensions
- fps = fps
- codec = video_codec
- bit rate = bitrate_mbps
- --size = size_mb
- new proposed codec = "vt_h265"
- new proposed bit rate = get_export_bitrate
- estimated new file size = [PLACEHOLDER]
- estimated compression ratio [PLACEHOLDER]
- converted file name = save_new_filename([input])
- renamed old file name





get_video_info
get_rating
get_export_bitrate
bitrate_to_size
estimate_new_file_size
parse_videos
save_new_filename
convert_video_handbrake
MainWindow













get_video_info(input_path):

returns video_info

which is     video_info = {

​        'video_codec': video_codec,

​        'dimensions': dimensions,

​        'bitrate_mbps': bitrate_mbps,

​        'fps': fps,

​        'duration_str': duration_str,

​        'size_mb': size_mb

​    }



