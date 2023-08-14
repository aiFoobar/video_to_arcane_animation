from core import ArcaneGANImageConverter
from video_splitter import VideoSplitter
import os
import time

class App:
    def __init__(self, input_file_name, project_dir):
        if project_dir[-1] != "/":
            project_dir += "/"
        
        self.input_file_name = input_file_name
        self.project_dir = project_dir

        self.project_sub_dir_input_path = self.project_dir + "input"
        self.project_sub_dir_output_path = self.project_dir + "output"
        self.project_sub_dir_tmp_path = self.project_dir + "tmp"
    
    def make_folder(self, name):
        try:
            os.system("mkdir {}{}".format(self.project_dir, name))
        except:
            print("Couldnt create directory: {}{}. Maybe its already present".format(self.project_dir, name))

    def make_project_folders(self):
        self.make_folder("input")
        self.make_folder("output")
        self.make_folder("tmp")

    def clean_tmp_directory(self):
        print("Cleaning directory : "+self.project_sub_dir_tmp_path)
        os.system("rm {}/*.*".format(self.project_sub_dir_tmp_path))

    def clean_input_directory(self):
        print("Cleaning directory : "+self.project_sub_dir_input_path)
        os.system("rm {}/*.*".format(self.project_sub_dir_input_path))

    def clean_output_directory(self):
        print("Cleaning directory : "+self.project_sub_dir_output_path)
        os.system("rm {}/*.*".format(self.project_sub_dir_output_path))
        


    def copy_video_to_tmp_directory(self, video_number):
        print("Copying {}/{}.mp4 to {}/input.mp4".format(self.project_sub_dir_input_path,video_number, self.project_sub_dir_tmp_path))
        command = "cp {}/{}.mp4 {}/input.mp4".format(self.project_sub_dir_input_path,video_number, self.project_sub_dir_tmp_path)
        print(command)
        os.system(command)

    def extract_images_from_video(self):
        print("Extracting Images from Video into {}".format(self.project_sub_dir_tmp_path))
        command = "cd {}; ffmpeg -i input.mp4 %04d.png".format(self.project_sub_dir_tmp_path)
        os.system(command)

    def extract_audio_from_video(self):
        print("Extracting Audio from Video into {}".format(self.project_sub_dir_tmp_path))
        command = "cd {}; ffmpeg -i input.mp4 -vn -acodec copy input.m4a".format(self.project_sub_dir_tmp_path)
        print(command)
        os.system(command)

    def stich_images_to_video(self, video_number):
        output_video_file_name = "{}/{}.mp4".format(self.project_sub_dir_output_path, video_number)
        
        print("Stiching Images and Audio into Video : "+output_video_file_name)
        
        command = "cd {}; ffmpeg -i %04d.png -i input.m4a -c:v libx264 -pix_fmt yuv420p {}".format(self.project_sub_dir_tmp_path, output_video_file_name)
        os.system(command)

    def create_video_list(self,output_file_count,output_file_name):
        f = open(output_file_name, 'w')
        for video_num in range(1,output_file_count):
            content="file {}.mp4\n".format(video_num)
            f.write(content)
        f.close()

    def combine_all_small_videos_into_one_file(self, output_file_count):
        # Create list with videos in order
        list_file_name = "{}/list.txt".format(self.project_sub_dir_output_path)
        self.create_video_list(output_file_count,list_file_name)

        # Trigger combine command
        # File will be written into root of project directory as final.mp4
        print("Combining all videos into single file......")
        command = "cd {};ffmpeg -f concat -i list.txt -c copy ../final.mp4".format(self.project_sub_dir_output_path)
        os.system(command)
        


    def run(self):
        # Create required folders
        self.make_project_folders()

        # Clean existing files in input folder. In case of project folder re-use
        self.clean_input_directory()

        # Clean existing files in output folder. In case of project folder re-use
        self.clean_output_directory()

        # # Cut videos into pieces
        video_splitter = VideoSplitter(self.input_file_name, self.project_sub_dir_input_path)
        video_splitter.split_curr_video()

        # For each video do the following
        for video_number in range(1, video_splitter.output_file_count+1):
            message = "Processing video {}/{}".format(video_number,video_splitter.output_file_count)
            print(message)

            # 1. Clean tmp directory
            self.clean_tmp_directory()

            # 2. Copy input video file into tmp directory. Filename should be input.mp4
            self.copy_video_to_tmp_directory(video_number)

            # 3. Execute Image extractor
            self.extract_images_from_video()

            # 4. Execute Audio extractor
            self.extract_audio_from_video()

            # 5. Run Arcane GAN on Images
            arcane = ArcaneGANImageConverter(message)
            arcane.convert_directory(self.project_sub_dir_tmp_path,self.project_sub_dir_tmp_path)

            # 6. Run video joiner and save as output
            self.stich_images_to_video(video_number)
        
        # Combine everything into one
        self.combine_all_small_videos_into_one_file(video_splitter.output_file_count)

        # Final Cleanup
        self.clean_output_directory()

        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("                     DONE!!!!                                ")
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        


if __name__ == "__main__":
    input_file_name = "/home/aifoobar/test_video.mp4"

    # Project directory should be created before executing the script.
    project_dir = "/home/aifoobar/first_project"

    app = App(input_file_name, project_dir)
    app.run()
    print("Find the processed video output in {}/{}".format(project_dir,"final.mp4"))