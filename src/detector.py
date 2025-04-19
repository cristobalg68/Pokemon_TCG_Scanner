from ultralytics import YOLO

class Detector():

    def __init__(self, weights):
        self.model =YOLO(weights)

    def detect_objects(self, path_image, confidence, iou):
        return self.model(path_image, conf=confidence, iou=iou)[0]