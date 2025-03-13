import pandas as pd
import requests
import os
import json


def creation_db_cards(dir):

    if os.path.exists(os.path.join(dir, 'log.json')):
        with open(os.path.join(dir, 'log.json')) as file:
            log_data = json.load(file)
    else:
        log_data = {
            'completed_set': [],
            'error_with_a_set': [],
            'error_with_a_symbol_set': [],
            'error_with_a_logo_set': [],
            'error_with_a_card': [],
            'error_with_a_image_card': [],
        }
        with open(os.path.join(dir, 'log.json'), 'w') as file:
            json.dump(log_data, file, indent=4)
    list_cards = []
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
    
                    if 'symbol' in set:
                        image_symbol_url = set['symbol'] + '.png'
                        response_4 = requests.get(image_symbol_url)
                        if response_4.status_code == 200:
                            with open(os.path.join(dir, 'images', 'symbols', f'{set_name}.png'), 'wb') as f:
                                f.write(response_4.content)
                        else:
                            log_data['error_with_a_symbol_set'].append(set_id)
                            with open(os.path.join(dir, 'log.json'), 'w') as file:
                                json.dump(log_data, file, indent=4)
                    else:
                        print(f'The {set_name} set has no symbol.')
                    
                    if 'logo' in set:
                        image_logo_url = set['logo'] + '.png'
                        response_5 = requests.get(image_logo_url)
                        if response_5.status_code == 200:
                            with open(os.path.join(dir, 'images', 'logos', f'{set_name}.png'), 'wb') as f:
                                f.write(response_5.content)
                        else:
                            log_data['error_with_a_logo_set'].append(set_id)
                            with open(os.path.join(dir, 'log.json'), 'w') as file:
                                json.dump(log_data, file, indent=4)
                    else:
                        print(f'The {set_name} set has no logo.')

                    for card in set['cards']:
                        card_id = card['id']
                        response_3 = requests.get(f'https://api.tcgdex.net/v2/en/cards/{card_id}', headers='')
                        if response_3.status_code == 200:
                            info_card = response_3.json()
                            card_local_id = card['localId'],
                            card_name = card['name'].replace(' ', '_')
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
                                })
                            image_card_url = info_card['image'] + '/high.png'
                            response_6 = requests.get(image_card_url)
                            if response_6.status_code == 200:
                                with open(os.path.join(dir, 'images', 'cards', f'{set_name}_{card_local_id}_{card_name}.png'), 'wb') as f:
                                    f.write(response_6.content)
                            else:
                                log_data['error_with_a_image_card'].append((set_id, card_id))
                                with open(os.path.join(dir, 'log.json'), 'w') as file:
                                    json.dump(log_data, file, indent=4)
                        else:
                            log_data['error_with_a_card'].append((set_id, card_id))
                            with open(os.path.join(dir, 'log.json'), 'w') as file:
                                json.dump(log_data, file, indent=4)
                                
                    log_data['completed_set'].append(set_id)
                    with open(os.path.join(dir, 'log.json'), 'w') as file:
                        json.dump(log_data, file, indent=4)

                else:
                    log_data['error_with_a_set'].append(set_id)
                    with open(os.path.join(dir, 'log.json'), 'w') as file:
                        json.dump(log_data, file, indent=4)
    else:
        print('Extraction of failure sets.')
    df = pd.DataFrame(list_cards)
    df.to_excel(os.path.join(dir, 'cards_of_pokemon.xlsx'), index=False)

creation_db_cards('datasets')