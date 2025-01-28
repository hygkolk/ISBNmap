import cv2
import numpy as np
import requests
import os
import io
from isbnlib import check_digit13

def get_tile_file_path(z, y, x, folder, extension="webp"):
	os.makedirs(f"./static/tiles/{folder}/{z}/{y}", exist_ok=True)
	return f"./static/tiles/{folder}/{z}/{y}/{x}.{extension}"

def change_tile_color(image,red=True):
	b, g, r = cv2.split(image) # Split the channels
	if red:
		new_image = cv2.merge((b, r, g)) # Shift the green channel to red
	else:
		new_image = cv2.merge((g, b, r)) # Shift the green channel to blue
	return new_image

def generate_image(z, y, x, color, dataset_name, isbn_dict, use_cache=True):
	"""Generate and save an image for the given tile coordinates."""
	section_size = 2 ** z
	output_size = min(section_size, 256)

	tile_file = get_tile_file_path(z, y, x, dataset_name)
	if os.path.exists(tile_file) and use_cache:
		image = cv2.imread(tile_file)
		print(f"File served: {tile_file}.")
	else:
		image = get_tile_grouped(z, y, x, isbn_dict[dataset_name], section_size, output_size)
		cv2.imwrite(tile_file, image, [cv2.IMWRITE_WEBP_QUALITY, 1000]) #For WEBP, it can be a quality from 1 to 100 (the higher is the better). By default (without any parameter) and for quality above 100 the lossless compression is used. 
		print(f"File created: {tile_file}.")

	if color == 'red':
		image = change_tile_color(image, True)
	elif color == 'blue':
		image = change_tile_color(image, False)

	_, buffer = cv2.imencode('.webp', image)
	return io.BytesIO(buffer)

def get_tile_grouped(z, y, x, isbn_dict, section_size, output_size):
	"""Generate a grouped tile image."""
	block_size = section_size // output_size
	rows, cols = np.divmod(isbn_dict, 2**16)
	row_start, col_start = y * section_size, x * section_size

	mask = (row_start <= rows) & (rows < row_start + section_size) & (col_start <= cols) & (cols < col_start + section_size)
	filtered_rows, filtered_cols = rows[mask] - row_start, cols[mask] - col_start

	grid = np.zeros((section_size, section_size), dtype=np.uint16)
	grid[filtered_rows, filtered_cols] = 1

	if block_size > 1: #for cases where you multiple books fill one pixel.
		output_grid = grid.reshape(output_size, block_size, output_size, block_size).sum(axis=(1, 3))
	else:
		output_grid = grid

	gamma = 0.5 # Choose a value less than 1 to enhance small values.
	normalized_output_grid = output_grid / (block_size * block_size) # normalize so output_grid has the values 0 through 1
	exponential_scaled = (normalized_output_grid ** gamma) * 255 # Apply the exponential scaling

	# Update the image array
	rgb_image_array = np.zeros((output_size, output_size, 3), dtype=np.uint8)
	rgb_image_array[:, :, 1] = exponential_scaled.astype(np.uint8) # Set green pixels.

	return rgb_image_array

def download_book_cover(z,y,x, use_cache=True):
	"""Download a book cover image for a given ISBN."""
	isbn12 = 978_000_000_000 + x + y * 2**16
	isbn13=str(isbn12) + check_digit13(str(isbn12))
	url = f"https://covers.openlibrary.org/b/isbn/{isbn13}-M.jpg"
	image_path=get_tile_file_path(z,y,x,"book_covers","jpg")

	if os.path.exists(image_path) and use_cache:
		print(f"Cover served: {image_path}.")
		return image_path

	response = requests.get(url)
	with open(image_path, 'wb') as file:
		file.write(response.content)

	print(f"Cover created: {image_path}.")
	return image_path

def main():
	print("No need to run this, it is imported by flask_app.py")

if __name__ == '__main__':
	main()