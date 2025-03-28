import os
import random
import cv2
import numpy as np


def load_images(folder):
    images = []
    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        images.append(img_path)
    return images

def rotate_image_keep_size(image, angle):
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    
    new_w = int(h * sin + w * cos)
    new_h = int(h * cos + w * sin)

    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2

    rotated_image = cv2.warpAffine(image, M, (new_w, new_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    
    return rotated_image

def place_cards_on_background(background, cards, margin=20):
    background = cv2.imread(background, cv2.IMREAD_COLOR)

    cards_images = []
    for card in cards:
        img = cv2.imread(card, cv2.IMREAD_UNCHANGED)
        cards_images.append(img)

    h_bg, w_bg, _ = background.shape
    h_card, w_card, c_card = cards_images[0].shape
    
    scale_factor = random.uniform(0.5, 1.5)
    
    w_card_scaled = int(w_card * scale_factor)
    h_card_scaled = int(h_card * scale_factor)
    
    placed_cards = []
    annotation_data = []
    bg_copy = background.copy()
    
    for card in cards_images:
        card_resized = cv2.resize(card, (w_card_scaled, h_card_scaled), interpolation=cv2.INTER_AREA)

        if c_card == 4:
            alpha = card_resized[:, :, 3] / 255.0
            card_rgb = card_resized[:, :, :3]
        else:
            alpha = np.ones((h_card_scaled, w_card_scaled))
            card_rgb = card_resized

        angle = random.uniform(-15, 15)
        card_rotated = rotate_image_keep_size(card_rgb, angle)
        alpha_rotated = rotate_image_keep_size(alpha, angle)

        h_rot, w_rot = card_rotated.shape[:2]

        valid_placement = False
        while not valid_placement:
            x_pos = random.randint(margin, w_bg - w_rot - margin)
            y_pos = random.randint(margin, h_bg - h_rot - margin)

            overlap = any(
                (x_pos < px + w_rot and x_pos + w_rot > px and
                 y_pos < py + h_rot and y_pos + h_rot > py)
                for px, py, _, _ in placed_cards
            )

            if not overlap:
                valid_placement = True
                placed_cards.append((x_pos, y_pos, w_rot, h_rot))

                for c in range(3):
                    bg_copy[y_pos:y_pos+h_rot, x_pos:x_pos+w_rot, c] = (
                        card_rotated[:, :, c] * alpha_rotated +
                        bg_copy[y_pos:y_pos+h_rot, x_pos:x_pos+w_rot, c] * (1 - alpha_rotated)
                    )

                x_center = (x_pos + w_rot / 2) / w_bg
                y_center = (y_pos + h_rot / 2) / h_bg
                width_norm = w_rot / w_bg
                height_norm = h_rot / h_bg
                annotation_data.append(f"0 {x_center} {y_center} {width_norm} {height_norm}")

    return bg_copy, annotation_data

def generate_synthetic_dataset(background_folder, cards_folder, output_folder, P):
    backgrounds = load_images(background_folder)
    cards = load_images(cards_folder)
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(os.path.join(output_folder, "labels"), exist_ok=True)
    os.makedirs(os.path.join(output_folder, "images"), exist_ok=True)
    
    for i in range(P):
        bg = random.choice(backgrounds)
        J = random.randint(1, min(5, len(cards)))
        selected_cards = random.sample(cards, J)
        
        synthetic_image, annotations = place_cards_on_background(bg, selected_cards)
        
        img_path = os.path.join(output_folder, "images", f"synthetic_{i}.jpg")
        label_path = os.path.join(output_folder, "labels", f"synthetic_{i}.txt")
        
        cv2.imwrite(img_path, synthetic_image)
        with open(label_path, "w") as f:
            f.write("\n".join(annotations))
    
    print(f"Generadas {P} imágenes sintéticas en {output_folder}")

generate_synthetic_dataset("D:/Proyectos/Pokemon_TCG_Scanner/datasets/images/background", 
                           "D:/Proyectos/Pokemon_TCG_Scanner/datasets/images/cards", 
                           "D:/Proyectos/Pokemon_TCG_Scanner/datasets/dataset_sintetico", 
                           5)