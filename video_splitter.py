import subprocess
import json
import os

class VideoSplitter:
    def __init__(self, input_file_name, output_dir):
        self.input_file_name = input_file_name
        
        if output_dir[-1:] != "/":
            output_dir+= "/"

        self.output_dir = output_dir
        self.output_file_count = 0
    
    def find_duration_of_video_in_seconds(self):
        out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", self.input_file_name])
        ffprobe_data = json.loads(out)
        duration_seconds = float(ffprobe_data["format"]["duration"])
        return duration_seconds

    
    def split_curr_video(self):
        current_second = 0
        completed = False

        print("\n\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print(" Video Splitter using FFmpeg")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        # Find length of the video
        video_duration_seconds = self.find_duration_of_video_in_seconds()
        print("Duration of video = {} seconds".format(video_duration_seconds))

        while not completed:
            video_number = current_second+1
            start_hour = int(current_second/(60*60))
            start_minute = int(current_second/60)
            start_second = current_second%60
            start_milli_second = "000"

            # end_hour = start_hour
            # end_minute = start_minute
            # end_second = start_second+1
            # end_milli_second = "000"

            if int(video_duration_seconds) == current_second:
                # Video duration will be like 4.527891
                # We only need first three number in millisecond
                # end_milli_second = str(video_duration_seconds).split(".")[1][0:3]
                # end_second = start_second
                completed = True
            
            # Format time values
            if start_hour < 10:
                start_hour = "0"+str(start_hour)
            
            if start_minute < 10:
                start_minute = "0"+str(start_minute)
            
            if start_second < 10:
                start_second = "0"+str(start_second)
            
            # if end_hour < 10:
            #     end_hour = "0"+str(end_hour)
            
            # if end_minute < 10:
            #     end_minute = "0"+str(end_minute)
            
            # if end_second < 10:
            #     end_second = "0"+str(end_second)

            output_file_name = "{}{}.mp4".format(self.output_dir, video_number)

            """
                Video Trim to second sample command :
                ffmpeg -ss 00:00:00.000 -i input.mp4 -to 1 trim.mp4
            """
            start_time_formatted = "{}:{}:{}.{}".format(start_hour,start_minute,start_second,start_milli_second)
            end_time_formatted = "00:00:01"

            # split_video_shell_command = "ffmpeg -ss {} -i {} -to {} -c:v copy -c:a copy {}".format(start_time_formatted,self.input_file_name, end_time_formatted, output_file_name)
            split_video_shell_command = "ffmpeg -ss {} -i {} -to 1 {}".format(start_time_formatted,self.input_file_name, output_file_name)
            
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Executing Command : "+split_video_shell_command)
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            os.system(split_video_shell_command)
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Completed video : "+output_file_name)
            self.output_file_count+=1
            current_second+=1
        