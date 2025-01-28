import numpy as np
from tqdm import tqdm
import zstandard
import bencodepy
import struct
import os
import requests

def download_isbn_file(url, filename):
    """Download a file from a URL if it doesn't already exist or if user agrees to redownload."""
    if os.path.exists(f"datasets/{filename}"):
        choice = input(f"{filename} already exists. Do you want to redownload it? (yes/NO): ").strip().lower()
        if choice != 'yes':
            print("Skipping download.")
            return
    print(f"Downloading {filename}...")
    response = requests.get(url + filename)
    if response.status_code == 200:
        with open(f"datasets/{filename}", 'wb') as file:
            file.write(response.content)
        print(f"Download completed: {filename}")
    else:
        print(f"Failed to download {filename}. Status code: {response.status_code}")

def decompress_and_decode(file_name):
    """Decompress and decode bencoded data from a Zstandard-compressed file."""
    print("Decompression start")
    with open(file_name, 'rb') as file:
        decompressor = zstandard.ZstdDecompressor().stream_reader(file)
        data = bencodepy.bread(decompressor)
    return data

def extract_integers(data, key):
    """Extract integers from binary data associated with a specified key."""
    print(f"Extract {key} start")
    binary_data = data[key]
    count = len(binary_data) // 4
    integers = struct.unpack(f'{count}I', binary_data)
    #print("Extract/unpack Finished")    
    return integers

def generate_isbn_list_numpy(integer_sequence):
    """Generate a list of ISBNs using alternating streak and gap values."""
    current_position = 0
    isbn_list = []
    isbn_mode = True

    for value in tqdm(integer_sequence, desc="Extracting ISBNs"):
        if isbn_mode:
            streak = np.arange(current_position, current_position + value)
            isbn_list.append(streak)
            current_position += value
        else:
            current_position += value
        isbn_mode = not isbn_mode

    return np.concatenate(isbn_list)

def save_isbn_list_to_disk(isbn_list, filename):
    """Save ISBN list to disk in NumPy's .npy format."""
    print(f"Saving: {filename}")
    np.save(filename, isbn_list)

def load_isbn_list_from_disk(filename):
    """Load ISBN list from a .npy file on disk."""
    return np.load(filename)

def get_npy_files_without_extension(folder_path="./"):
    files = [os.path.splitext(file)[0] for file in os.listdir(folder_path) if file.endswith('.npy')]
    return files

def make_all_isbns(dataset_list):
    """Make the all_isbns dataset by combining all the isbn datsets"""
    all_isbns = np.array([], dtype=int)

    for dataset in tqdm(dataset_list, desc="Merging datasets into all_isbns"):
        new_array = load_isbn_list_from_disk(f"datasets/{dataset}.npy")
        all_isbns = np.union1d(all_isbns, new_array)  # Efficient unique merge

    return all_isbns

def main():
    base_url = "https://software.annas-archive.li/AnnaArchivist/annas-archive/-/raw/main/isbn_images/"
    filename = "aa_isbn13_codes_20241204T185335Z.benc.zst"
    #check if file already exists
    download_isbn_file(base_url, filename)

    data = decompress_and_decode(f"datasets/{filename}")
    dataset_list=[]
    for dataset_key in data:
        dataset_name = dataset_key.decode()  # Decode binary key to string
        dataset_list.append(dataset_name)
        filename=f"datasets/{dataset_name}.npy"

        if os.path.exists(filename):
            print(f"{filename} already exists, skipping")
            continue

        integer_sequence = extract_integers(data, dataset_key)
        isbn_list = generate_isbn_list_numpy(integer_sequence)
        save_isbn_list_to_disk(isbn_list, filename)

    try:
        isbn_list_loaded = load_isbn_list_from_disk("datasets/ia.npy") #load a random dataset, and check if it can be read correctly
        isbn_list_loaded[:10]
    except Exception as e:
        print("Dataset preparation failed.", e)
        quit()

    print("Dataset preperation success, now building all_isbns")
    if os.path.exists(f"datasets/all_isbns.npy"):
        print(f"{filename} already exists, skipping")
    else:
        isbn_list=make_all_isbns(dataset_list)
        save_isbn_list_to_disk(isbn_list, 'datasets/all_isbns.npy')

    print("Dataset preparation finished successfully!")

if __name__ == '__main__':
    main()
