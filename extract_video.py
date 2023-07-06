from operator import length_hint
import os
import cv2
import time

from multiprocessing import Pool

def extract_one_video(info):
    video_file, des_image_dir = info[0], info[1]
    print('--extracting video: ', video_file)
    cam = cv2.VideoCapture(video_file)
    length = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    currentframe = 0  
    while(True):
        t = time.time()
        ret,frame = cam.read()  
        if ret:
            if currentframe % 2 == 0:
                name = os.path.join(des_image_dir, des_image_dir.split('/')[-1] + '_frame_'+ str(currentframe).zfill(6)    + '.jpg')
                cv2.imwrite(name, frame)
            currentframe += 1
        else:
            break
    cam.release()
    cv2.destroyAllWindows()

def get_file_path(line):
    path = line.strip().split(' :  ')[0]
    return path

def main(source_video, des_image_root, extract_index = None):
    vid_lists = open('new_video_list.txt', 'r').readlines()
    vid_lists = list(map(get_file_path, vid_lists))
    video_files = []
    for vid_file in vid_lists:
        des_image_dir = vid_file.replace(source_video,des_image_root).replace('.mp4', '')
        if not os.path.exists(des_image_dir):
            os.makedirs(des_image_dir)
        video_files.append((vid_file,des_image_dir))

    if extract_index is not None:
        extract_files = video_files[extract_index[0]:extract_index[1]]
        with Pool(20) as p:
            p.map(extract_one_video, extract_files)
    else:
        with Pool(20) as p:
            p.map(extract_one_video, video_files)
  

def extract_specific_frame(video, des_video, sta, sto):
    sta_min = int(sta[0]+sta[1])
    sta_sec = int(sta[2]+sta[3])
    sto_min = int(sto[0]+sto[1])
    sto_sec = int(sto[2]+sto[3])
    start_time =  sta_min*60 + sta_sec   #+ 39
    stop_time =  sto_min*60 + sto_sec 
    start_frame = start_time*29.97
    stop_frame = (stop_time-start_time)*30
    cam = cv2.VideoCapture(video)

    cam.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(des_video, fourcc, 30.0, (1920,1280))
    cur_frame = 0
    while(True):
        
        ret,frame = cam.read()

        if ret:
            out.write(frame)
            cur_frame += 1           
        if cur_frame > stop_frame:
            break
       
    cam.release()
    out.release()
    cv2.destroyAllWindows()


  
        
            
if __name__ == '__main__':

    video_root = '/mnt/media01/D00050-00099/D00050_矢崎EC_次期型デジタルタコグラフ＆ドライブレコーダー/03_顧客データ/2022-11-11_矢崎ES_歩行者映像'
    des_root = '/mnt/media01/D00050-00099/D00050_矢崎EC_次期型デジタルタコグラフ＆ドライブレコーダー/04_学習データ/Car_Bike_Ped_TSR/Dungtd/auto_annotation_pes_vid'
    main(video_root, des_root)



    # video = '/mnt/media01/D00050-00099/D00050_矢崎EC_次期型デジタルタコグラフ＆ドライブレコーダー/03_顧客データ/2022-11-24_信号機用新カメラ実車走行映像/YDX8_20221028_中/WIN_20221028_16_18_30_Pro.mp4'
    # des_video = '/mnt/media01/D00050-00099/D00050_矢崎EC_次期型デジタルタコグラフ＆ドライブレコーダー/04_学習データ/Car_Bike_Ped_TSR/Dungtd/auto_annotation/2022-11-24_信号機用新カメラ実車走行映像_no_signal/YDX8_20221028_中/WIN_20221028_16_18_30_Pro_0305_0313.mp4'
    # video = '/mnt/media01/D00050-00099/D00050_矢崎EC_次期型デジタルタコグラフ＆ドライブレコーダー/03_顧客データ/2022-11-24_信号機用新カメラ実車走行映像/YDX8_20221031_中/WIN_20221031_10_32_38_Pro.mp4'
    # des_video = '/mnt/media01/D00050-00099/D00050_矢崎EC_次期型デジタルタコグラフ＆ドライブレコーダー/04_学習データ/Car_Bike_Ped_TSR/Dungtd/auto_annotation/2022-11-24_信号機用新カメラ実車走行映像_test_video/WIN_20221031_10_32_38_Pro_1341_1352.mp4'
    # name = os.path.basename(des_video)
    # t = name.replace('.mp4','').split('_')[-2:]
    # sta = list(t[0])
    # sto = list(t[1])
    # extract_specific_frame(video, des_video, sta, sto)    
    
    

