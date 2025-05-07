import cv2
import numpy as np
import imagehash
from PIL import Image, ImageTk
import pandas as pd
import tkinter as tk

def read_frame(camera, size):
    ret, frame = camera.read()

    if not ret:
        print("Failed to read frame from the webcam")
        return None

    resized_frame = cv2.resize(frame, (size, size))
    return resized_frame

def read_image(path_image, size):
    img = cv2.imread(path_image)
    img = cv2.resize(img, (size, size))
    return img

def process_detections(detections):
    new_detections = []
    if detections.masks != None:
        for mask, segmentation, bbox in zip(detections.masks.data, detections.masks.xy, detections.boxes.xywh):
            det = {
                'bbox': bbox.cpu().numpy().astype(int),
                'segmentation': segmentation,
                'mask': mask.cpu().numpy()
            }
            new_detections.append(det)
    return new_detections

def mask_to_card(image, detections):
    for detection in detections:
        mask = detection['mask'].astype(np.uint8) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        card = None
        
        for contour in contours:
            epsilon = 0.1 * cv2.arcLength(contour, True)
            points = cv2.approxPolyDP(contour, epsilon, True)
            if len(points) == 4:
                centroids = np.mean(points, axis=0)
                corners = np.array(sorted(points, key=lambda x: np.arctan2(x[0][1] - centroids[0][1], x[0][0] - centroids[0][0])))

                width = np.linalg.norm(corners[0] - corners[1])
                height = np.linalg.norm(corners[1] - corners[2])
                dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
                M = cv2.getPerspectiveTransform(points.astype(np.float32), dst)

                card = cv2.warpPerspective(image, M, (int(width), int(height)))
                
                if width > height:
                    card = cv2.rotate(card, cv2.ROTATE_90_CLOCKWISE)

                card = cv2.resize(card, (320, 444))
                card = cv2.flip(card, 1)

        if card is not None:
            detection['card_image'] = card

def hash_image(img, hash_size):
    img = Image.fromarray(img)
    img = img.convert('RGB')

    dhash = imagehash.dhash(img, hash_size)
    phash = imagehash.phash(img, hash_size)

    return f'{dhash}{phash}'

def hash_cards(detections, hash_size):
    for detection in detections:
        if 'card_image' in detection:
            image_hash = hash_image(detection['card_image'], hash_size)
            detection['hash'] = image_hash
            card_image = cv2.rotate(detection['card_image'], cv2.ROTATE_180)
            image_hash = hash_image(card_image, hash_size)
            detection['hash_flipped'] = image_hash

def hamming_distance(hash1, hash2):
    return sum(ch1 != ch2 for ch1, ch2 in zip(hash1, hash2))

def find_match(hash_a, df):
    min_sim = 14*6.8

    df['similarity'] = df['hash'].apply(lambda x: hamming_distance(x, hash_a))
    min_row = df.loc[df['similarity'].idxmin()]
    if min_row['similarity'] < min_sim:
        card_name = min_row['Name']
        set_card_name = min_row['Set_Name']
        local_id = min_row['Local_ID']
        return f"{card_name} {set_card_name} {local_id}", min_row['similarity']
    return None, None

def match_hashes(detections, df):
    for detection in detections:
        if 'hash' in detection:
            match1, sim1 = find_match(detection['hash'], df)
            match2, sim2 = find_match(detection['hash_flipped'], df)
            if match1 is None and match2 is None:
                continue
            elif match1 is None:
                detection['match'] = match2
            elif match2 is None:
                detection['match'] = match1
            else:
                if sim2 > sim1:
                    detection['match'] = match1
                else:
                    detection['match'] = match2

def draw_boxes_and_segmentation(image, x, y, w, h, segmentation, bbox=False):
    if bbox:
        cv2.rectangle(image, (x - int(w/2), y - int(h/2)), (x + int(w/2), y + int(h/2)), (0, 255, 0), 2)
    overlay = image.copy()
    cv2.polylines(image, [segmentation], isClosed=True, color=(0, 0, 255), thickness=2)
    cv2.fillPoly(overlay, [segmentation], color=(0, 0, 255))
    alpha = 0.3
    image[:] = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)

def draw(image, detections):
    for detection in detections:
        x, y, w, h = detection["bbox"]
        segmentation = np.array(detection["segmentation"]).reshape(-1, 2).astype(np.int32)
        draw_boxes_and_segmentation(image, x, y, w, h, segmentation)

def draw_t(image, tracker):
    for id in tracker['matches']:
        x, y, w, h = tracker['matches'][id]["bbox"]
        segmentation = np.array(tracker['matches'][id]["segmentation"]).reshape(-1, 2).astype(np.int32)
        draw_boxes_and_segmentation(image, x, y, w, h, segmentation)

def show_image(image, container):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(image)
    img_tk = ImageTk.PhotoImage(img_pil)

    label = tk.Label(container, image=img_tk, bg="black")
    label.image = img_tk
    label.pack(expand=True)

def show_video(image, video_label):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(image)
    img_tk = ImageTk.PhotoImage(image=img_pil)

    video_label.imgtk = img_tk
    video_label.config(image=img_tk)

def calcular_iou(bbox1, bbox2):
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    xA = max(x1_1, x1_2)
    yA = max(y1_1, y1_2)
    xB = min(x2_1, x2_2)
    yB = min(y2_1, y2_2)

    inter_ancho = max(0, xB - xA)
    inter_alto = max(0, yB - yA)
    inter_area = inter_ancho * inter_alto

    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0.0

    iou = inter_area / union_area
    return iou

def track_objects(detections, tracked_matches, threshold):
    new_detections = []
    new_matches = {}
    for detection in detections:
        x, y, w, h = detection["bbox"]
        x1_2 = x - int(w/2)
        y1_2 = y - int(h/2) 
        x2_2 = x + int(w/2)
        y2_2 = y + int(h/2)
        for key in tracked_matches['matches']:
            x, y, w, h = tracked_matches['matches'][key]["bbox"]
            x1_1 = x - int(w/2) 
            y1_1 = y - int(h/2) 
            x2_1 = x + int(w/2)
            y2_1 = y + int(h/2)
            iou = calcular_iou([x1_1, y1_1, x2_1, y2_1], [x1_2, y1_2, x2_2, y2_2])
            if iou > threshold:
                new_matches[key] = tracked_matches['matches'][key]
                detection['match'] = True
        if 'match' not in detection.keys():
            new_detections.append(detection)
            id = str(tracked_matches['last_id'])
            new_matches[id] = {}
            new_matches[id]["bbox"] = detection["bbox"]
            new_matches[id]["segmentation"] = detection["segmentation"]
            tracked_matches['last_id'] += 1
                
    detections = new_detections
    tracked_matches['matches'] = new_matches