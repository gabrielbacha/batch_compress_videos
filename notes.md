CHECK ALL THE LOGIC -- ADD PRINT DIALOG TO FOLLOW FLOWS TO MAKE SURE THAT EVERYTHING NOT BEING UNNECESSARILY REPEATED
COPY RATING



get_video_info(input_path)

    video_info = {
        'video_codec': video_codec,
        'dimensions': dimensions,
        'bitrate_mbps': bitrate_mbps,
        'fps': fps,
        'duration_str': duration_str,
        'size_mb': size_mb
        'rating': rating
    }

get_export_bitrate(video_info)

    export_settings










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









dji


File Modification Date/Time     : 2023:06:25 16:25:50+04:00
File Access Date/Time           : 2023:11:16 12:16:27+04:00
File Inode Change Date/Time     : 2023:11:16 12:16:29+04:00
Create Date                     : 2023:06:25 14:24:23
Modify Date                     : 2023:06:25 14:24:23
Track Create Date               : 2023:06:25 14:24:23
Track Modify Date               : 2023:06:25 14:24:23
Media Create Date               : 2023:06:25 14:24:23
Media Modify Date               : 2023:06:25 14:24:23



apple

Create Date                     : 2023:11:13 17:35:31
Modify Date                     : 2023:11:13 17:35:40
Track Create Date               : 2023:11:13 17:35:31
Track Modify Date               : 2023:11:13 17:35:40
Media Create Date               : 2023:11:13 17:35:31
Media Modify Date               : 2023:11:13 17:35:40
Creation Date                   : 2023:11:13 21:35:31+04:00


sony
Create Date                     : 2023:04:24 08:47:58
Modify Date                     : 2023:04:24 08:47:58
Track Create Date               : 2023:04:24 08:47:58
Track Modify Date               : 2023:04:24 08:47:58
Media Create Date               : 2023:04:24 08:47:58
Media Modify Date               : 2023:04:24 08:47:58

Creation Date Value             : 2023:04:24 17:47:58+09:00
