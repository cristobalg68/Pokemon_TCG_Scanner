import pandas as pd
import requests
import os
import json
import re
import sys
import imagehash
from PIL import Image
from io import BytesIO
from tqdm import tqdm


def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    return re.sub(invalid_chars, '_', filename)

def print_clear(msn):
    sys.stdout.write("\r" + " " * 50)
    sys.stdout.write("\r" + msn)
    sys.stdout.flush()

def creation_db_cards(dir):

    if os.path.exists(os.path.join(dir, 'log.json')):
        with open(os.path.join(dir, 'log.json')) as file:
            log_data = json.load(file)
    else:
        log_data = {
            'completed_set': [],
            'error_with_a_set': [],
            'error_with_a_symbol_set': [],
            'set_without_symbol': [],
            'error_with_a_logo_set': [],
            'set_without_logo': [],
            'error_with_a_card': [],
            'card_without_image': [],
            'error_with_a_image_card': [],
        }
        with open(os.path.join(dir, 'log.json'), 'w') as file:
            json.dump(log_data, file, indent=4)

        init_df = pd.DataFrame([], columns=['ID','Local_ID','Set_ID','Set_Name','Name','Rarity','Firt_Edition','Holo','Normal','Reverse','Promo','Image_Card_URL'])
        init_df.to_excel(os.path.join(dir, 'cards_of_pokemon.xlsx'), index=False)

    response_1 = requests.get('https://api.tcgdex.net/v2/en/sets', headers='')
    if response_1.status_code == 200:
        sets = response_1.json()  
        for set in sets:
            set_id = set['id']
            if set_id not in log_data['completed_set']:
                set_name = set['name'].replace(' ', '_')
                response_2 = requests.get(f'https://api.tcgdex.net/v2/en/sets/{set_id}', headers='')
                if response_2.status_code == 200:
                    set = response_2.json()
                    list_cards = []
                    safe_filename = sanitize_filename(f'{set_name}.png')
    
                    if 'symbol' in set:
                        image_symbol_url = set['symbol'] + '.png'
                        response_4 = requests.get(image_symbol_url)
                        if response_4.status_code == 200:
                            with open(os.path.join(dir, 'images', 'symbols', safe_filename), 'wb') as f:
                                f.write(response_4.content)
                        else:
                            log_data['error_with_a_symbol_set'].append(set_id)
                            with open(os.path.join(dir, 'log.json'), 'w') as file:
                                json.dump(log_data, file, indent=4)
                    else:
                        log_data['set_without_symbol'].append(set_id)
                        with open(os.path.join(dir, 'log.json'), 'w') as file:
                            json.dump(log_data, file, indent=4)
                    
                    if 'logo' in set:
                        image_logo_url = set['logo'] + '.png'
                        response_5 = requests.get(image_logo_url)
                        if response_5.status_code == 200:
                            with open(os.path.join(dir, 'images', 'logos', safe_filename), 'wb') as f:
                                f.write(response_5.content)
                        else:
                            log_data['error_with_a_logo_set'].append(set_id)
                            with open(os.path.join(dir, 'log.json'), 'w') as file:
                                json.dump(log_data, file, indent=4)
                    else:
                        log_data['set_without_logo'].append(set_id)
                        with open(os.path.join(dir, 'log.json'), 'w') as file:
                            json.dump(log_data, file, indent=4)

                    for card in tqdm(set['cards'], desc="Procesando cartas")
                        card_id = card['id']
                        response_3 = requests.get(f'https://api.tcgdex.net/v2/en/cards/{card_id}', headers='')
                        if response_3.status_code == 200:
                            info_card = response_3.json()
                            card_local_id = card['localId'],
                            card_name = card['name'].replace(' ', '_')

                            if 'image' in info_card:
                                image_card_url = info_card['image'] + '/high.png'
                                response_6 = requests.get(image_card_url)
                                if response_6.status_code == 200:
                                    safe_filename = sanitize_filename(f'{set_name}_{card_local_id}_{card_name}.png')
                                    with open(os.path.join(dir, 'images', 'cards', safe_filename), 'wb') as f:
                                        f.write(response_6.content)
                                else:
                                    log_data['error_with_a_image_card'].append((set_id, card_id))
                                    with open(os.path.join(dir, 'log.json'), 'w') as file:
                                        json.dump(log_data, file, indent=4)
                            else:
                                image_card_url = ''
                                log_data['card_without_image'].append((set_id, card_id))
                                with open(os.path.join(dir, 'log.json'), 'w') as file:
                                    json.dump(log_data, file, indent=4)
                            
                            list_cards.append({
                                'ID': card_id, 
                                'Local_ID': card['localId'], 
                                'Set_ID': set['id'],
                                'Set_Name': set['name'],
                                'Name': card['name'], 
                                'Rarity': info_card['rarity'],
                                'Firt_Edition': int(info_card['variants']['firstEdition']),
                                'Holo': int(info_card['variants']['holo']),
                                'Normal': int(info_card['variants']['normal']),
                                'Reverse': int(info_card['variants']['reverse']),
                                'Promo': int(info_card['variants']['wPromo']),
                                'Image_Card_URL': image_card_url,
                                })
                        else:
                            log_data['error_with_a_card'].append((set_id, card_id))
                            with open(os.path.join(dir, 'log.json'), 'w') as file:
                                json.dump(log_data, file, indent=4)
                                
                    log_data['completed_set'].append(set_id)
                    with open(os.path.join(dir, 'log.json'), 'w') as file:
                        json.dump(log_data, file, indent=4)

                    old_df = pd.read_excel(os.path.join(dir, 'cards_of_pokemon.xlsx'))
                    new_df = pd.DataFrame(list_cards)
                    df = pd.concat([old_df, new_df])
                    df.to_excel(os.path.join(dir, 'cards_of_pokemon.xlsx'), index=False)

                else:
                    log_data['error_with_a_set'].append(set_id)
                    with open(os.path.join(dir, 'log.json'), 'w') as file:
                        json.dump(log_data, file, indent=4)

def solve_errors(dir):
    with open(os.path.join(dir, 'log.json')) as file:
        log_data = json.load(file)

    # Error with a symbol set
    errors = []
    for error in log_data["error_with_a_symbol_set"]:
        response = requests.get(f'https://api.tcgdex.net/v2/en/sets/{error}', headers='')
        if response.status_code == 200:
            set = response.json()
            safe_filename = sanitize_filename(f'{set_name}.png')

            if 'symbol' in set:
                image_symbol_url = set['symbol'] + '.png'
                response = requests.get(image_symbol_url)
                if response.status_code == 200:
                    with open(os.path.join(dir, 'images', 'symbols', safe_filename), 'wb') as f:
                        f.write(response.content)
                else:
                    errors.append(error)
    
    log_data["error_with_a_symbol_set"] = errors
    with open(os.path.join(dir, 'log.json'), 'w') as file:
        json.dump(log_data, file, indent=4)

    # Error with a logo set
    errors = []
    for error in log_data["error_with_a_logo_set"]:
        response = requests.get(f'https://api.tcgdex.net/v2/en/sets/{error}', headers='')
        if response.status_code == 200:
            set = response.json()
            safe_filename = sanitize_filename(f'{set_name}.png')

            if 'logo' in set:
                image_logo_url = set['logo'] + '.png'
                response = requests.get(image_logo_url)
                if response.status_code == 200:
                    with open(os.path.join(dir, 'images', 'logos', safe_filename), 'wb') as f:
                        f.write(response.content)
                else:
                    errors.append(error)
    
    log_data["error_with_a_logo_set"] = errors
    with open(os.path.join(dir, 'log.json'), 'w') as file:
        json.dump(log_data, file, indent=4)

    list_cards = []

    # Error with a card
    errors = []
    for error in log_data["error_with_a_card"]:
        card_id = error[1]
        response = requests.get(f'https://api.tcgdex.net/v2/en/cards/{card_id}', headers='')
        if response.status_code == 200:
            info_card = response.json()
            if 'image' in info_card:
                image_card_url = info_card['image'] + '/high.png'
                card_local_id = info_card['localId']
                card_name = info_card['name']
                set_name = info_card['set']['name']
                response = requests.get(image_card_url)
                if response.status_code == 200:
                    safe_filename = sanitize_filename(f'{set_name}_{card_local_id}_{card_name}.png')
                    with open(os.path.join(dir, 'images', 'cards', safe_filename), 'wb') as f:
                        f.write(response.content)
                    list_cards.append({
                                'ID': card_id, 
                                'Local_ID': card_local_id, 
                                'Set_ID': info_card['set']['id'],
                                'Set_Name': set_name,
                                'Name': card_name, 
                                'Rarity': info_card['rarity'],
                                'Firt_Edition': int(info_card['variants']['firstEdition']),
                                'Holo': int(info_card['variants']['holo']),
                                'Normal': int(info_card['variants']['normal']),
                                'Reverse': int(info_card['variants']['reverse']),
                                'Promo': int(info_card['variants']['wPromo']),
                                'Image_Card_URL': image_card_url,
                                })
                else:
                    errors.append(error)

    log_data["error_with_a_card"] = errors
    with open(os.path.join(dir, 'log.json'), 'w') as file:
        json.dump(log_data, file, indent=4)

    old_df = pd.read_excel(os.path.join(dir, 'cards_of_pokemon.xlsx'))
    new_df = pd.DataFrame(list_cards)
    df = pd.concat([old_df, new_df])
    df.to_excel(os.path.join(dir, 'cards_of_pokemon.xlsx'), index=False)

    # Error with a image card
    errors = []
    for error in log_data["error_with_a_image_card"]:
        card_id = error[1]
        response = requests.get(f'https://api.tcgdex.net/v2/en/cards/{card_id}', headers='')
        if response.status_code == 200:
            info_card = response.json()
            if 'image' in info_card:
                image_card_url = info_card['image'] + '/high.png'
                card_local_id = info_card['localId']
                card_name = info_card['name']
                set_name = info_card['set']['name']
                response = requests.get(image_card_url)
                if response.status_code == 200:
                    safe_filename = sanitize_filename(f'{set_name}_{card_local_id}_{card_name}.png')
                    with open(os.path.join(dir, 'images', 'cards', safe_filename), 'wb') as f:
                        f.write(response.content)
                else:
                    errors.append(error)

    log_data["error_with_a_image_card"] = errors
    with open(os.path.join(dir, 'log.json'), 'w') as file:
        json.dump(log_data, file, indent=4)

def hash_image(img, hash_size):
    img = img.convert('RGB')
    dhash = imagehash.dhash(img, hash_size)
    phash = imagehash.phash(img, hash_size)

    return f'{dhash}{phash}'

def add_hash_column(dir, save_per=100):
    log_path = os.path.join(dir, 'log.json')
    with open(log_path, 'r') as file:
        log_data = json.load(file)

    last_index = log_data["last_saved_index"]

    file_path = os.path.join(dir, 'cards_of_pokemon.xlsx')
    df = pd.read_excel(file_path)

    if 'hash' not in df.columns:
        df['hash'] = None

    count_since_last_save = 0
    for index in tqdm(range(last_index, len(df)), initial=last_index, desc="Procesando imágenes"):
        row = df.iloc[index]
        if pd.notna(row['hash']):
            continue

        url = row['Image_Card_URL']

        if pd.isna(url):
            df.at[index, 'hash'] = None
        else:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                hash_val = hash_image(img, 16)
                df.at[index, 'hash'] = hash_val
            except Exception as e:
                print(f"Error en fila {index} con URL '{url}': {e}")
                df.at[index, 'hash'] = None

        count_since_last_save += 1

        if count_since_last_save >= save_per:
            df.to_excel(file_path, index=False)
            log_data['last_saved_index'] = index
            with open(log_path, 'w') as file:
                json.dump(log_data, file, indent=4)
            count_since_last_save = 0

    df.to_excel(file_path, index=False)
    log_data['last_saved_index'] = len(df)
    with open(log_path, 'w') as file:
        json.dump(log_data, file, indent=4)

#creation_db_cards('D:/Proyectos/Pokemon_TCG_Scanner/datasets')

#solve_errors('D:/Proyectos/Pokemon_TCG_Scanner/datasets')

add_hash_column('D:/Proyectos/Pokemon_TCG_Scanner/datasets')