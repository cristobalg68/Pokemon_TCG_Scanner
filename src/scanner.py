import cv2
import pandas as pd
import tkinter as tk

from detector import Detector
import utils

class Scanner():

    def __init__(self, path_weights, size, confidence, iou, hash_size, path_df, save, path):
        self.detector = Detector(path_weights)
        self.size = size
        self.confidence = confidence
        self.iou = iou
        self.hash_size = hash_size
        self.df = pd.read_excel(path_df).dropna(subset=['hash'])
        self.save = save
        self.path_saved = path

class ImageScanner(Scanner):

    def run(self, path_image, container):
        container.master.geometry(f"680x680")

        img_original = utils.read_image(path_image, self.size)
        img_original_copy = img_original.copy()
        
        detections = self.detector.detect_objects(img_original, self.confidence, self.iou)
        detections = utils.process_detections(detections)

        utils.mask_to_card(img_original, detections)
        utils.hash_cards(detections, self.hash_size)
        utils.match_hashes(detections, self.df)

        utils.draw_boxes_and_segmentation(img_original_copy, detections)

        utils.show_image(img_original_copy, container)

class VideoScanner(Scanner):

    def run(self, path_video, container):
        pass

class LiveScanner(Scanner):

    def run(self, camera_id, container):
        container.master.geometry(f"680x680")

        self.camera = cv2.VideoCapture(camera_id)
        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self.camera.get(cv2.CAP_PROP_FPS))
        print("Webcam started with resolution:", width, "x", height, 'fps:', fps)

        self.video_label = tk.Label(container)
        self.video_label.pack(expand=True)

        self.update_frame()

    def update_frame(self):
        img_original = utils.read_frame(self.camera, self.size)
        if img_original is None:
            return

        img_original_copy = img_original.copy()

        detections = self.detector.detect_objects(img_original, self.confidence, self.iou)
        detections = utils.process_detections(detections)
        utils.mask_to_card(img_original, detections)
        utils.hash_cards(detections, self.hash_size)
        utils.match_hashes(detections, self.df)
        utils.draw_boxes_and_segmentation(img_original_copy, detections)

        utils.show_live(img_original_copy, self.video_label)

        self.video_label.after(30, self.update_frame)