from scanner import ImageScanner, VideoScanner, LiveScanner

path_weights = "weights/best_1.pt"
path_df = "D:/Proyectos/Pokemon_TCG_Scanner/datasets/cards_of_pokemon.xlsx"
hash_size = 16
size = 640
confidence = 0.5
iou = 0.5

def main(mode, source):
    if mode == 'image':
        scanner = ImageScanner(path_weights, size, confidence, iou, hash_size, path_df)
    elif mode == 'video':
        scanner = VideoScanner(path_weights, size, confidence, iou, hash_size, path_df)
    elif mode == 'live':
        scanner = LiveScanner(path_weights, size, confidence, iou, hash_size, path_df)
    else:
        print('Mode is not recognized')
        exit()
    
    scanner.run(source)

if __name__ == '__main__':
    mode = 'image' # image / video / live
    source = 'C:/Users/Cristobal/Desktop/test.jpg'
    main(mode, source)