import cv2
import json
import pandas as pd

from detector import Detector
import utils

class Scanner():

    def __init__(self, path_weights, size, confidence, iou, hash_size, path_df):
        self.detector = Detector(path_weights)
        self.size = size
        self.confidence = confidence
        self.iou = iou
        self.hash_size = hash_size
        self.df = pd.read_excel(path_df)

class ImageScanner(Scanner):

    def run(self, path_image):
        img_original = utils.read_image(path_image, self.size)
        
        detections = self.detector.detect_objects(img_original, self.confidence, self.iou)
        detections = utils.process_detections(detections)

        utils.mask_to_card(img_original, detections)
        utils.hash_cards(detections, self.hash_size)
        utils.match_hashes(detections, self.df)

        print(detections)

class VideoScanner(Scanner):

    def run(self):
        pass

class LiveScanner(Scanner):

    def run(self, camera_id):

        camera = cv2.VideoCapture(camera_id)
        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(self.camera.get(cv2.CAP_PROP_FPS))
        print("Webcam started with resolution:", width, "x", height, 'fps:', fps)

        tracked_matches = {}

        while True:
            img_original = utils.read_frame(camera, self.size)
            img_original = cv2.flip(img_original, 1)
            if img_original is None:
                break

            img_copy = img_original.copy()

            detections = self.detector.detect_objects(img_original, self.confidence, self.iou)

            """
            # Add object tracking IDs to detections
            .track_objects(detections)

            # Make hashes and matches to detections
            .process_masks_to_cards(img_original, detections, mirror=True)
            .hash_cards(detections)
            .match_hashes(detections)

            # Store tracked matches
            for detection in detections:
                if 'track_id' in detection and 'match' in detection:
                    track_id = detection['track_id']
                    match = detection['match']
                    if track_id not in tracked_matches:
                        tracked_matches[track_id] = match
                        print(f'Match found: id {track_id} {match}')

            # Draw elements
            .draw_boxes(img_copy, detections)
            .draw_masks(img_copy, detections)
            """