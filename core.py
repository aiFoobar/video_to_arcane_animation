import os
os.system("pip3 -qq install facenet_pytorch")
from facenet_pytorch import MTCNN
from torchvision import transforms
import torch, PIL
import torch

print(" Loading Trained Models.... Please Wait")
modelarcanev4 = "ArcaneGANv0.4.jit"
modelv4 = torch.jit.load(modelarcanev4).eval().cuda().half()

valid_extensions = [".png"]
mtcnn = MTCNN(image_size=256, margin=80)

size = 256

means = [0.485, 0.456, 0.406]
stds = [0.229, 0.224, 0.225]

t_stds = torch.tensor(stds).cuda().half()[:,None,None]
t_means = torch.tensor(means).cuda().half()[:,None,None]


class ArcaneGANImageConverter:
    def __init__(self, present_message=None):
        self.full_path_file_names_map = []
        self.present_message = present_message

    def run(self):
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("Starte Arcane Image Convertion")
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("\n\n")
        for index in range(0,len(self.full_path_file_names_map)):
            input_file_name = self.full_path_file_names_map[index]['input']
            output_file_name = self.full_path_file_names_map[index]['output']
            if input_file_name[-4:] in valid_extensions:
                print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                if self.present_message != None:
                    print(self.present_message)
                print("Processing File {}/{} : {}".format(str(index+1), len(self.full_path_file_names_map), input_file_name))
                # try:
                image = PIL.Image.open(input_file_name)
                ab = self.process(image)
                ab.save(output_file_name)
                print("Completed File : "+output_file_name)
                print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                # except:
                #     print("Error Processing File : "+input_file_name)
            progress = (float(index+1)*100)/float(len(self.full_path_file_names_map))
            print("Progress = {} %".format(progress))
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("\n")

    
    # MAIN METHOD 
    def convert_directory(self, input_dir, output_dir):
        if output_dir[-1:] != "/":
            output_dir+="/"
        
        if input_dir[-1:] != "/":
            input_dir+="/"
        
        all_files = os.listdir(input_dir)
        for curr_file_name in all_files:
            self.full_path_file_names_map.append(
                {
                    "input": input_dir+curr_file_name,
                    "output": output_dir+curr_file_name
                }
            )
        
        # Trigger conversion
        self.run()


    # simplest ye olde trustworthy MTCNN for face detection with landmarks
    def detect(self, img):
    
            # Detect faces
            batch_boxes, batch_probs, batch_points = mtcnn.detect(img, landmarks=True)
            # Select faces
            if not mtcnn.keep_all:
                batch_boxes, batch_probs, batch_points = mtcnn.select_boxes(
                    batch_boxes, batch_probs, batch_points, img, method=mtcnn.selection_method
                )
    
            return batch_boxes, batch_points

    # my version of isOdd, should make a separate repo for it :D
    def makeEven(self, _x):
        return _x if (_x % 2 == 0) else _x+1

    # the actual scaler function
    def scale(self, boxes, _img, max_res=1_500_000, target_face=256, fixed_ratio=0, max_upscale=2, VERBOSE=False):
        x, y = _img.size
    
        ratio = 2 #initial ratio
    
        #scale to desired face size
        if (boxes is not None):
            if len(boxes)>0:
                ratio = target_face/max(boxes[0][2:]-boxes[0][:2]); 
                ratio = min(ratio, max_upscale)
                if VERBOSE: print('up by', ratio)

        if fixed_ratio>0:
            if VERBOSE: print('fixed ratio')
            ratio = fixed_ratio
    
        x*=ratio
        y*=ratio
    
        #downscale to fit into max res 
        res = x*y
        if res > max_res:
            ratio = pow(res/max_res,1/2); 
            if VERBOSE: print(ratio)
            x=int(x/ratio)
            y=int(y/ratio)
    
        #make dimensions even, because usually NNs fail on uneven dimensions due skip connection size mismatch
        x = self.makeEven(int(x))
        y = self.makeEven(int(y))
        
        size = (x, y)

        return _img.resize(size)

    """ 
        A useful scaler algorithm, based on face detection.
        Takes PIL.Image, returns a uniformly scaled PIL.Image
        boxes: a list of detected bboxes
        _img: PIL.Image
        max_res: maximum pixel area to fit into. Use to stay below the VRAM limits of your GPU.
        target_face: desired face size. Upscale or downscale the whole image to fit the detected face into that dimension.
        fixed_ratio: fixed scale. Ignores the face size, but doesn't ignore the max_res limit.
        max_upscale: maximum upscale ratio. Prevents from scaling images with tiny faces to a blurry mess.
    """

    def scale_by_face_size(self, _img, max_res=1_500_000, target_face=256, fix_ratio=0, max_upscale=2, VERBOSE=False):
        boxes = None
        boxes, _ = self.detect(_img)
        if VERBOSE: print('boxes',boxes)
        img_resized = self.scale(boxes, _img, max_res, target_face, fix_ratio, max_upscale, VERBOSE)
        return img_resized

    def makeEven(self, _x):
        return int(_x) if (_x % 2 == 0) else int(_x+1)

    img_transforms = transforms.Compose([                        
                transforms.ToTensor(),
                transforms.Normalize(means,stds)])
    
    def tensor2im(self, var):
        return var.mul(t_stds).add(t_means).mul(255.).clamp(0,255).permute(1,2,0)

    def proc_pil_img(self,input_image, model):
        transformed_image = self.img_transforms(input_image)[None,...].cuda().half()
                
        with torch.no_grad():
            result_image = model(transformed_image)[0]
            output_image = self.tensor2im(result_image)
            output_image = output_image.detach().cpu().numpy().astype('uint8')
            output_image = PIL.Image.fromarray(output_image)
        return output_image
        

    def process(self, im):
        im = self.scale_by_face_size(im, target_face=256, max_res=1_500_000, max_upscale=1)
        res = self.proc_pil_img(im, modelv4)
        return res
        

# if __name__ == "__main__":
#     input_dir="/home/kamar/batch/tmp/"
#     output_dir="/home/kamar/batch/tmp/"
#     all_files = os.listdir(input_dir)

#     for name in all_files:
#         if name[-4:] in valid_extensions:
#             image = PIL.Image.open(input_dir+name)
#             ab = process(image)
#             ab.save(output_dir+name)
#             print("Completed :"+name)