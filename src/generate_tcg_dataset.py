import os
import random
import cv2


def load_images(folder):
    images = []
    for filename in os.listdir(folder):
        img_path = os.path.join(folder, filename)
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            images.append(img)
    return images

def place_cards_on_background(background, cards, margin=20):
    h_bg, w_bg, _ = background.shape
    h_card, w_card, _ = cards[0].shape
    
    max_scale = min((w_bg - 2 * margin) / w_card, (h_bg - 2 * margin) / h_card)
    scale_factor = random.uniform(0.5, max_scale)
    
    w_card_scaled = int(w_card * scale_factor)
    h_card_scaled = int(h_card * scale_factor)
    
    placed_cards = []
    annotation_data = []
    bg_copy = background.copy()
    
    for card in cards:
        card_resized = cv2.resize(card, (w_card_scaled, h_card_scaled))
        angle = random.uniform(-15, 15)
        M = cv2.getRotationMatrix2D((w_card_scaled // 2, h_card_scaled // 2), angle, 1)
        card_rotated = cv2.warpAffine(card_resized, M, (w_card_scaled, h_card_scaled))
        
        valid_placement = False
        while not valid_placement:
            x_pos = random.randint(margin, w_bg - w_card_scaled - margin)
            y_pos = random.randint(margin, h_bg - h_card_scaled - margin)
            
            overlap = any(
                (x_pos < px + w_card_scaled and x_pos + w_card_scaled > px and
                 y_pos < py + h_card_scaled and y_pos + h_card_scaled > py)
                for px, py, _, _ in placed_cards
            )
            
            if not overlap:
                valid_placement = True
                placed_cards.append((x_pos, y_pos, w_card_scaled, h_card_scaled))
                
                bg_copy[y_pos:y_pos+h_card_scaled, x_pos:x_pos+w_card_scaled] = card_rotated
                
                x_center = (x_pos + w_card_scaled / 2) / w_bg
                y_center = (y_pos + h_card_scaled / 2) / h_bg
                width_norm = w_card_scaled / w_bg
                height_norm = h_card_scaled / h_bg
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

generate_synthetic_dataset("fondos", "cartas", "dataset_sintetico", 100)