import cv2
import pandas as pd

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

    def run(self):
        pass

class LiveScanner(Scanner):

    def run(self, camera_id):

        camera = cv2.VideoCapture(camera_id)
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(camera.get(cv2.CAP_PROP_FPS))
        print("Webcam started with resolution:", width, "x", height, 'fps:', fps)

        tracked_matches = {}

        while True:
            img_original = utils.read_frame(camera, self.size)
            #img_original = cv2.flip(img_original, 1)
            if img_original is None:
                break

            img_original_copy = img_original.copy()

            detections = self.detector.detect_objects(img_original, self.confidence, self.iou)

            detections = utils.process_detections(detections)
            #utils.track_objects(detections, tracked_matches, self.iou)

            utils.mask_to_card(img_original, detections)
            utils.hash_cards(detections, self.hash_size)
            utils.match_hashes(detections, self.df)

            utils.draw_boxes_and_segmentation(img_original_copy, detections)

            utils.show_image(img_original_copy)

            if cv2.waitKey(1) == ord('q'):
                break