import os
import random
import cv2
import numpy as np
import json
import uuid
import shutil
from shapely.geometry import Polygon
from tqdm import tqdm


def load_images(folder):
    return [os.path.join(folder, filename) for filename in os.listdir(folder)]

def generate_name():
    random_uuid = str(uuid.uuid4().hex)
    return random_uuid

def rotate_image_keep_size(image, angle):
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    M = cv2.getRotationMatrix2D(center, angle, 1)
    cos, sin = np.abs(M[0, 0]), np.abs(M[0, 1])
    
    new_w, new_h = int(h * sin + w * cos), int(h * cos + w * sin)
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2
    
    rotated = cv2.warpAffine(image, M, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    return rotated

def get_card_contour(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        return max(contours, key=cv2.contourArea)
    return None

def place_cards_on_background(background, cards, margin=20):
    background = cv2.imread(background, cv2.IMREAD_COLOR)
    h_bg, w_bg, _ = background.shape

    scale_factor = random.uniform(0.5, 1.0)

    placed_cards, annotation_data = [], []
    mask_overlay = np.zeros((h_bg, w_bg), dtype=np.uint8)
    
    for card_path in cards:
        card = cv2.imread(card_path, cv2.IMREAD_UNCHANGED)
        h_card, w_card = card.shape[:2]
        
        w_card, h_card = int(w_card * scale_factor), int(h_card * scale_factor)
        card_resized = cv2.resize(card, (w_card, h_card))
        
        alpha = card_resized[:, :, 3] if card.shape[2] == 4 else np.ones((h_card, w_card), dtype=np.uint8) * 255
        
        angle = random.uniform(-180, 180)
        card_rotated = rotate_image_keep_size(card_resized, angle)
        alpha_rotated = rotate_image_keep_size(alpha, angle)
        h_rot, w_rot = card_rotated.shape[:2]

        for _ in range(50):
            x_pos, y_pos = random.randint(margin, w_bg - w_rot - margin), random.randint(margin, h_bg - h_rot - margin)
            overlap = any(
                (x_pos < px + pw and x_pos + w_rot > px and
                y_pos < py + ph and y_pos + h_rot > py)
                for px, py, pw, ph in placed_cards)
            
            if not overlap:
                placed_cards.append((x_pos, y_pos, w_rot, h_rot))

                alpha_mask = alpha_rotated / 255.0

                for c in range(3):
                    background[y_pos:y_pos+h_rot, x_pos:x_pos+w_rot, c] = (
                        card_rotated[:, :, c] * alpha_mask +
                        background[y_pos:y_pos+h_rot, x_pos:x_pos+w_rot, c] * (1 - alpha_mask)
                    )

                card_mask = np.zeros((h_rot, w_rot), dtype=np.uint8)
                card_mask[alpha_rotated > 0] = 255
                
                contour = get_card_contour(card_mask)
                if contour is not None:
                    contour[:, 0, 0] += x_pos
                    contour[:, 0, 1] += y_pos
                    segmentation = contour.reshape(-1).tolist()
                    
                    annotation_data.append({
                        "bbox": [x_pos, y_pos, w_rot, h_rot],
                        "category_id": 0,
                        "segmentation": [segmentation]
                    })
                    cv2.fillPoly(mask_overlay, [contour], 255)
                break
    
    return background, annotation_data, mask_overlay, w_bg, h_bg

def generate_synthetic_dataset(bg_folder, card_folder, output_folder, P):
    backgrounds, cards = load_images(bg_folder), load_images(card_folder)
    os.makedirs(f"{output_folder}", exist_ok=True)
    os.makedirs(f"{output_folder}/images", exist_ok=True)
    os.makedirs(f"{output_folder}/annotations", exist_ok=True)
    os.makedirs(f"{output_folder}/masks", exist_ok=True)
    
    for i in tqdm(range(P), desc="Creating Images"):
        bg, selected_cards = random.choice(backgrounds), random.sample(cards, random.randint(1, min(5, len(cards))))
        img, annotations, mask, w_image, h_image = place_cards_on_background(bg, selected_cards)

        image_id = generate_name()
        
        cv2.imwrite(f"{output_folder}/images/{image_id}.jpg", img)
        cv2.imwrite(f"{output_folder}/masks/{image_id}.png", mask)
        
        json_data = {"image_id": image_id, "height_image": h_image, "width_image": w_image, "annotations": annotations}
        with open(f"{output_folder}/annotations/{image_id}.json", "w") as f:
            json.dump(json_data, f, indent=4)

def convert_coco_to_yolo(annotation_folder, label_folder, mode="bbox"):
    os.makedirs(label_folder, exist_ok=True)
    for file in os.listdir(annotation_folder):
        with open(os.path.join(annotation_folder, file), "r") as f:
            data = json.load(f)
        
        txt_path = os.path.join(label_folder, file.replace(".json", ".txt"))
        with open(txt_path, "w") as f:
            h_image = data["height_image"]
            w_image = data["width_image"]
            for ann in data["annotations"]:
                n_class = ann["category_id"]
                if mode == "bbox":
                    x, y, w, h = ann["bbox"]
                    x_center, y_center, w_norm, h_norm = (x + w/2)/w_image, (y + h/2)/h_image, w/w_image, h/h_image
                    f.write(f"{n_class} {x_center} {y_center} {w_norm} {h_norm}\n")
                elif mode == "segmentation":
                    seg = ann["segmentation"][0]
                    seg_str = " ".join(map(str, [v/w_image if i%2==0 else v/h_image for i, v in enumerate(seg)]))
                    f.write(f"{n_class} {seg_str}\n")

def visualize_annotations(image_path, annotation_path):
    image = cv2.imread(image_path)
    with open(annotation_path, "r") as f:
        data = json.load(f)
    
    for ann in data["annotations"]:
        bbox = ann["bbox"]
        segmentation = np.array(ann["segmentation"][0]).reshape(-1, 2)
        
        cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)
        cv2.polylines(image, [segmentation.astype(np.int32)], isClosed=True, color=(0, 0, 255), thickness=2)
    
    cv2.imshow("Annotations", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def split_dataset(splits, path, class_names):
    assert sum([splits[s] for s in splits]) == 1.0
    os.makedirs(os.path.join(path, 'splited_dataset'), exist_ok=True)
    names = os.listdir(os.path.join(path, 'images'))
    random.seed(0)
    random.shuffle(names)
    last = 0
    splits_rows = []
    for split in splits:
        splits_rows.append(f'{split}: {os.path.join(path, 'splited_dataset', split, 'images')}     # {split} images\n')
        os.makedirs(os.path.join(path, 'splited_dataset', split), exist_ok=True)
        os.makedirs(os.path.join(path, 'splited_dataset', split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(path, 'splited_dataset', split, 'labels'), exist_ok=True)
        for i in tqdm(range(last, int(splits[split] * len(names)) + last), desc=f"Creating Split - {split}"):
            shutil.copy(os.path.join(path, 'images', names[i]), os.path.join(path, 'splited_dataset', split, 'images', names[i]))
            shutil.copy(os.path.join(path, 'labels', names[i].split('.')[0] + '.txt'), os.path.join(path, 'splited_dataset', split, 'labels', names[i].split('.')[0] + '.txt'))
        last = int(splits[split] * len(names))
        simplify_all_segmentations(os.path.join(path, 'splited_dataset', split, 'labels'))

    formatted_names = "\n" + "\n".join([f"  {i}: {name}" for i, name in enumerate(class_names)])
    splits_path = "".join(splits_rows)
    yaml_file = """{}\nis_coco: False\n\n# Classes\nnames:{}""".format(splits_path, formatted_names)
    with open(os.path.join(path, 'splited_dataset','data.yaml'), 'w') as file1:
        file1.write(yaml_file)

def simplify_segmentation(points, tolerance):
    coords = np.array(points).reshape(-1, 2)
    poly = Polygon(coords)

    if not poly.is_valid or poly.is_empty:
        return points

    simplified = poly.simplify(tolerance, preserve_topology=True)

    simplified_coords = np.array(simplified.exterior.coords[:-1])
    return simplified_coords.flatten().tolist()

def simplify_all_segmentations(label_dir, tolerance=0.001):
    for fname in tqdm(os.listdir(label_dir), desc=f"Optimizing split labels"):
        if not fname.endswith('.txt'):
            continue

        fpath = os.path.join(label_dir, fname)

        with open(fpath, 'r') as file:
            lines = file.readlines()

        simplified_lines = []
        for line in lines:
            parts = line.strip().split()
            cls = parts[0]
            coords = list(map(float, parts[1:]))

            simplified_coords = simplify_segmentation(coords, tolerance)
            simplified_line = cls + ' ' + ' '.join(map(str, simplified_coords))
            simplified_lines.append(simplified_line)

        with open(fpath, 'w') as file:
            file.write('\n'.join(simplified_lines))
        
if __name__ == "__main__":
    output_folder = "D:/Proyectos/Pokemon_TCG_Scanner/datasets/synthetic_dataset"
    
    generate_synthetic_dataset("D:/Proyectos/Pokemon_TCG_Scanner/datasets/images/background", 
                            "D:/Proyectos/Pokemon_TCG_Scanner/datasets/images/cards", 
                            output_folder, 
                            1500)
    
    convert_coco_to_yolo(f"{output_folder}/annotations", 
                        f"{output_folder}/labels", 
                        mode="segmentation")

    split_dataset({'train': 0.8, 'val': 0.1, 'test': 0.1}, 
                  output_folder,
                  ['card'])
    