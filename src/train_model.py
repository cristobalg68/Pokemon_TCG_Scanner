import comet_ml
import os
import shutil
import torch
from ultralytics import YOLO

if __name__ == "__main__":

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Using device: {device}')

    API_KEY_COMET = 'dsAlnIxEVCZKtbhrTcYjV5QzE'
    project_name = 'yolo_card'
    yolo_model_version = "yolo11l-seg"
    class_name = ["card"]
    yaml_path = 'D:/Proyectos/Pokemon_TCG_Scanner/datasets/synthetic_dataset/splited_dataset/data.yaml'
    pt_path = 'weights/'

    training_params = {
        "ID": 1,
        "name": yolo_model_version,
        "single_cls": True if len(class_name) == 1 else False,
        "epochs": 20,
        "classes": class_name
    }

    comet_ml.login(project_name=project_name)
    exp = comet_ml.Experiment(API_KEY_COMET, project_name=project_name)

    model = YOLO(training_params['name'] + '.pt')

    exp.set_name('experiment_{}'.format(training_params['ID']))
    results = model.train(data=yaml_path,
                        epochs=training_params['epochs'],
                        project=project_name,
                        single_cls=training_params['single_cls'],
                        save_period=1,
                        exist_ok=True,
                        save_json=True,
                        imgsz=720)

    exp.end()

    results = model.val(data=yaml_path,
                        split='test')

    shutil.move(f'{project_name}/train/weights/best.pt', pt_path + f'best_{training_params['ID']}.pt')