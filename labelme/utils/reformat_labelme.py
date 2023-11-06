# import cv2
import glob
import os
import json
from typing import List, Tuple
from collections import namedtuple, deque, Counter
from natsort import natsorted
KeyPoint = namedtuple(
    'KeyPoint',
    ['label', 'xy', 'clearly_visible', 'auto_generated'],
)

def decode_point_data(point_data: dict) -> Tuple[str, tuple, bool]:
    label: str = point_data.label
    if label.startswith("inv_"):
        cur_visible = False
        label = label[4:]
    else:
        cur_visible = True

    xy = (point_data.points[0].x(), point_data.points[0].y())
        
    return label, xy, cur_visible

def encode_keypoint(kp: 'KeyPoint'):
    return kp._asdict()

def encode_slot(keypoints: List['KeyPoint']):
    return [encode_keypoint(kp) for kp in keypoints]

def verify_entrance(points: List[dict], img_p):
    '''verify if at least one of entrance, second-entrance or intermediate exist'''
    is_valid = True
    found_right = False
    for i in range(1):
        cur_label, _, _ = decode_point_data(points[i])
        if cur_label in ['entrance', 'second_entrance', 'intermediate']:
            found_right=True
            break
    if not found_right:
        is_valid = False
        print(f"Missing right entrance (or intermediate) point. (img_p: {img_p})")
        # raise Exception(f"Missing right entrance (or intermediate) point. (img_p: {img_p})")

    found_left = False
    for i in range(3):
        cur_label, _, _ = decode_point_data(points[-1-i])
        if cur_label in ['entrance', 'second_entrance', 'intermediate']:
            found_left=True
            break
    if not found_left:
        is_valid = False
        print(f"Missing left entrance (or intermediate) point. (img_p: {img_p})")
        # raise Exception(f"Missing left entrance (or intermediate) point. (img_p: {img_p})")
    return is_valid

def verify_entrance_only_second_entrance(points: List[dict], img_p):
    '''verify if at least one of entrance, second-entrance or intermediate exist'''
    is_valid = True
    found_right = False
    for i in range(1):
        cur_label, _, _ = decode_point_data(points[i])
        if cur_label in ['second_entrance']:
            found_right=True
            break
    if not found_right:
        is_valid = False
        print(f"Missing right entrance (or intermediate) point. (img_p: {img_p})")
        # raise Exception(f"Missing right entrance (or intermediate) point. (img_p: {img_p})")

    found_left = False
    for i in range(3):
        cur_label, _, _ = decode_point_data(points[-1-i])
        if cur_label in ['second_entrance']:
            found_left=True
            break
    if not found_left:
        is_valid = False
        print(f"Missing left entrance (or intermediate) point. (img_p: {img_p})")
        # raise Exception(f"Missing left entrance (or intermediate) point. (img_p: {img_p})")
    return is_valid

def verify_endpoint(points: List[dict], img_p: str):
    '''verify if 2 endpoints exist as a consecutive pair'''
    is_valid = True
    end_idx = []
    for i in range(len(points)):
        cur_label, _, _ = decode_point_data(points[i])
        if cur_label == 'endpoint':
            end_idx.append(i)
    if not( len(end_idx) == 2 and end_idx[1]-1 == end_idx[0]):
        is_valid = False
        print(f"endpoints must exist as a consecutive pair. (img_p: {img_p})")
        # raise Exception(f"endpoints must exist as a consecutive pair. (img_p: {img_p})")
    return is_valid

def verify_unique(points: List[dict], img_p: str):
    '''verify if there is only 1 point of each type left/right side.'''
    right_count = Counter()
    is_valid = True
    i = 0
    while True:
        label,_,_ = decode_point_data(points[i])
        if label == 'endpoint':
            break
        right_count[label] += 1
        if right_count[label] > 1:
            is_valid = False
            print(f"There are more than one right {label}. (img_p: {img_p})")
            # raise Exception(f"There are more than one right {label}. (img_p: {img_p})")
        i+=1
    left_count = Counter()
    i = -1
    while True:
        label,_,_ = decode_point_data(points[i])
        if label == 'endpoint':
            break
        left_count[label] += 1
        if left_count[label] > 1:
            is_valid = False
            print(f"There are more than one right {label}. (img_p: {img_p})")
            # raise Exception(f"There are more than one right {label}. (img_p: {img_p})")
        i-=1
    return is_valid

def verify_intermediate(points: List[dict], img_p: str):
    'If there is entrance/second entrance, there should NOT be intermediate point'
    is_valid = True
    is_entrance_found = False
    is_intermediate_found = False
    for i in range(len(points)):
        cur_label, _, _ = decode_point_data(points[i])
        if cur_label == 'entrance' or cur_label == 'second_entrance':
            is_entrance_found = True
        elif cur_label == 'intermediate':
            is_intermediate_found = True
        elif cur_label == 'endpoint':  # Check & Reset side
            if is_entrance_found and is_intermediate_found:
                is_valid = False
                print(f"Found entance point together with intermediate point. (img_p: {img_p})")
                # raise Exception(f"Found entance point together with intermediate point. (img_p: {img_p})")
            else:
                is_entrance_found, is_intermediate_found = False, False
    if is_entrance_found and is_intermediate_found:
        is_valid = False
        print(f"Found entance point together with intermediate point. (img_p: {img_p})")
        # raise Exception(f"Found entance point together with intermediate point. (img_p: {img_p})")

    return is_valid

def verify_points_old(points: List[dict], img_p: str):
    '''verify if annotated data is in correct format.'''
    r1 = verify_entrance(points, img_p)
    if r1:
        r2 = verify_endpoint(points, img_p)
        if r2:
            r3 = verify_unique(points, img_p)
            if r3:
                r4 = verify_intermediate(points, img_p)
                return r4
            else:
                return False
        else:
            return False
    else:
        return False
    
def verify_points(points: List[dict], img_p: str):
    '''verify if annotated data is in correct format.'''
    r1 = verify_entrance_only_second_entrance(points, img_p)
    return r1


def make_keypoint_list(points: List[dict]) -> List['KeyPoint']:

    points_queue = deque(points)

    # # If "entrance" does not exist, set to "second entrance" or "intermediate" line (in this order).  
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[0])
    if cur_label == 'entrance':
        right_entrance = KeyPoint('entrance', cur_xy, cur_visible, False)
        points_queue.popleft()
    else:
        right_entrance = KeyPoint('entrance', cur_xy, False, True)
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[-1])
    if cur_label == 'entrance':
        left_entrance = KeyPoint('entrance', cur_xy, cur_visible, False)
        points_queue.pop()
    else:
        left_entrance = KeyPoint('entrance', cur_xy, False, True)

    # # If "second entrance" does not exist, set to "second entrance" or "intermediate" line (in this order).  
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[0])
    if cur_label == 'second_entrance':
        right_2nd_entrance = KeyPoint('second_entrance', cur_xy, cur_visible, False)
        points_queue.popleft()
    else:
        right_2nd_entrance = KeyPoint('second_entrance', right_entrance.xy, False, True)
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[-1])
    if cur_label == 'second_entrance':
        left_2nd_entrance = KeyPoint('second_entrance', cur_xy, cur_visible, False)
        points_queue.pop()
    else:
        left_2nd_entrance = KeyPoint('second_entrance', left_entrance.xy, False, True)

    # # If "intermediate" does not exist, set to "second entrance" or "entrance" line (in this order).  
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[0])
    if cur_label == 'intermediate':
        right_intermediate = KeyPoint('intermediate', cur_xy, cur_visible, False)
        points_queue.popleft()
    else:
        right_intermediate = KeyPoint('intermediate', right_2nd_entrance.xy, False, True)
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[-1])
    if cur_label == 'intermediate':
        left_intermediate = KeyPoint('intermediate', cur_xy, cur_visible, False)
        points_queue.pop()
    else:
        left_intermediate = KeyPoint('intermediate', left_2nd_entrance.xy, False, True)

    # # If "stoppoint" does not exist, set to a point outside of image boundary (-1, -1).  
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[0])
    if cur_label == 'stoppoint':
        right_stoppoint = KeyPoint('stoppoint', cur_xy, cur_visible, False)
        points_queue.popleft()
    else:
        right_stoppoint = KeyPoint('stoppoint', (-1,- 1), False, True)
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[-1])
    if cur_label == 'stoppoint':
        left_stoppoint = KeyPoint('stoppoint', cur_xy, cur_visible, False)
        points_queue.pop()
    else:
        left_stoppoint = KeyPoint('stoppoint', (-1,- 1), False, True)

    # # "endpoint" MUST exist. (cannot be auto-generated)
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[0])
    if cur_label == 'endpoint':
        right_endpoint = KeyPoint('endpoint', cur_xy, cur_visible, False)
    else:
        raise Exception("Wrong reading sequence")
    cur_label, cur_xy, cur_visible = decode_point_data(points_queue[-1])
    if cur_label == 'endpoint':
        left_endpoint = KeyPoint('endpoint', cur_xy, cur_visible, False)
    else:
        raise Exception("Wrong reading sequence")

    return [
        right_entrance,
        right_2nd_entrance,
        right_intermediate,
        right_stoppoint,
        right_endpoint,
        left_endpoint,
        left_stoppoint,
        left_intermediate,
        left_2nd_entrance,
        left_entrance
    ]

def int_xy(kp):
    return (int(kp.xy[0]),int(kp.xy[1]))

# def draw_point(img, kp: 'KeyPoint', color):
#     if kp.clearly_visible:
#         cv2.circle(img, int_xy(kp), 5, color, -1)
#     else:
#         cv2.circle(img, int_xy(kp), 5, color, 1)
#         cv2.circle(img, int_xy(kp), 2, color, 1)

# def draw_line(img, kp1: 'KeyPoint', kp2: 'KeyPoint', color, draw_invisible = False):
#     draw_point(img,kp1,color)
#     draw_point(img,kp2,color)
#     if (kp1.clearly_visible and kp2.clearly_visible) or draw_invisible:
#         cv2.line(img, int_xy(kp1), int_xy(kp2), color, 2)
        
# def draw_intermediate_line(img, kp1: 'KeyPoint', kp2: 'KeyPoint', color):
#     draw_point(img,kp1,color)
#     cv2.line(img, int_xy(kp1), int_xy(kp2), color, 2)

# def draw_slot(img, keypoints: List['KeyPoint']):
#         right_entrance, \
#         right_2nd_entrance, \
#         right_intermediate, \
#         right_stoppoint, \
#         right_endpoint, \
#         left_endpoint, \
#         left_stoppoint, \
#         left_intermediate, \
#         left_2nd_entrance, \
#         left_entrance = keypoints

#         draw_line(img, right_entrance, left_entrance, (255,0,0))
#         draw_line(img, right_2nd_entrance, left_2nd_entrance, (0,0,255))
#         draw_line(img, right_stoppoint, left_stoppoint, (255,188,0))
#         draw_line(img, right_endpoint, left_endpoint, (0,255,0), draw_invisible=True)
#         draw_intermediate_line(img, right_intermediate, right_endpoint, (0,255,255))
#         draw_intermediate_line(img, left_intermediate, left_endpoint, (0,255,255))

# def visualize_slots(img_p: str, slots: List[list]):
#     img = cv2.imread(img_p)
#     for keypoint in slots:
#         draw_slot(img, keypoint)
#     cv2.namedWindow('img', cv2.WINDOW_NORMAL)
#     cv2.imshow('img', img)

def convert_from_labelme(basedir, outdir, visualize=False, first_slot_only=False):
    slot_cnt = 0
    for img_p in natsorted(glob.glob(os.path.join(basedir, '**', '*.json'))):
        labelme_p = os.path.splitext(img_p)[0] + '.json'
        labelme_data = json.load(open(labelme_p))

        labelme_slots = [[]]

        for point_data in labelme_data['shapes']:
            if len(labelme_slots[-1]) != 0 and labelme_slots[-1][0]['group_id'] != point_data['group_id']:
                labelme_slots.append([])
            labelme_slots[-1].append(point_data)
        if first_slot_only and len(labelme_slots) > 1:
            labelme_slots = [labelme_slots[0]]
        
        encoded_slots = []
        slots = []
        for points in labelme_slots:
            if len(points) == 0:
                continue
            verify_points(points, img_p)
            slot = make_keypoint_list(points)
            # if visualize:
            #     slots.append(slot)
            encoded_slots.append(encode_slot(slot))
            slot_cnt += 1
    
        out_data = {
            'flags' : labelme_data['flags'],
            'slots' : encoded_slots,
        }

        out_p = os.path.join(outdir, os.path.relpath(labelme_p, basedir))

        # os.makedirs(os.path.dirname(out_p), exist_ok=True)
        # json.dump(out_data, open(out_p, 'w'), indent=2)
        if visualize:
            visualize_slots(img_p, slots)
            k=cv2.waitKey()
            if k == 27:
                exit()
    print("Total count", slot_cnt)

def check_label(all_shapes):

    labelme_slots = [[]]

    for point_data in all_shapes:
        if len(labelme_slots[-1]) != 0 and labelme_slots[-1][0].group_id != point_data.group_id:
            labelme_slots.append([])
        labelme_slots[-1].append(point_data)
    flag = list()
    for points in labelme_slots:
        if len(points) == 0:
            continue
        flag.append(verify_points(points, ''))
    if False in flag:
        return False
    else:
        return True


if __name__=='__main__':
    basedir = '/home/kup2yh/Documents/Data/Annotation_skip150_fixed'
    outdir = '/home/kup2yh/Documents/Data/Annotation_skip150_fixed2'
    convert_from_labelme(basedir, outdir, visualize=False, first_slot_only=True)