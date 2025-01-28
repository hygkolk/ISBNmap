import cv2
import numpy as np
import os

import isbnlib._data.data4info as countries
import isbnlib._data.data4mask as publishers

from get_tile import get_tile_file_path

def generate_country_image(z, y, x, use_cache=True):	
	tile_file = get_tile_file_path(z, y, x, "countries") # Determine tile file path

	# Check if the image is cached
	if os.path.exists(tile_file) and use_cache:
		print(f"Country cache found: {tile_file}.")
		return tile_file

	# Calculate section size and start ISBN
	section_size = 2 ** z # section size is width of books to check
	start_isbn = 978_000_000_000 + section_size * x + 2**16 * y * section_size
	# Set ISBN increment and output size. Check if sectionsize fits in 256x256 tile
	isbn_increment = 1 if section_size <= 256 else section_size / 256
	output_size = min(section_size, 256)

	# Create a 2D grid of x and y coordinates
	x_indices, y_indices = np.meshgrid(np.arange(output_size), np.arange(output_size))
	# Precompute string representation of isbn_array
	isbn_array_str = (start_isbn + isbn_increment * (x_indices + y_indices * 2**16)).astype(str)

	country_prefixes = [country_range.replace("-", "") for country_range in countries.countries] # remove dash for easier string compare
	# Precompute RGB color values for each prefix
	prefix_colors = [
		((i * 55 + 128) % 256, (i * 116 + 128) % 256, (i * 221 + 128) % 256) for i in range(len(country_prefixes))
	]

	rgb_image = np.zeros((output_size, output_size, 3), dtype=np.uint8)	# Initialize an RGB image (black by default)
	for country_prefix_index, prefix in enumerate(country_prefixes):
		mask = np.char.startswith(isbn_array_str, prefix)  # Vectorized string comparison
		rgb_image[mask] = prefix_colors[country_prefix_index]

	# Save the generated image
	cv2.imwrite(tile_file, rgb_image, [cv2.IMWRITE_WEBP_QUALITY, 1000])
	print(f"Country image created: {tile_file}.")
	return tile_file

def generate_publisher_image(z, y, x, use_cache=True):
	# Determine tile file path
	tile_file = get_tile_file_path(z, y, x, "publishers")

	# Check if the image is cached
	if os.path.exists(tile_file) and use_cache:
		print(f"Publisher cache found: {tile_file}.")
		return tile_file

	# Calculate section size and start ISBN
	section_size = 2 ** z
	start_isbn = 978_000_000_000 + section_size * x + 2**16 * y * section_size
	isbn_increment = 1 if section_size <= 256 else int(section_size / 256)
	output_size = min(section_size, 256)
	
	# Create a 2D grid of x and y coordinates
	x_indices, y_indices = np.meshgrid(np.arange(output_size), np.arange(output_size))
	# Precompute string representation of isbn_array
	isbn_array_str = (start_isbn + isbn_increment * (x_indices + y_indices * 2**16)).astype(str)

	# Precompute prefix keys and their lengths without hyphens
	prefix_keys = {key.replace("-", ""): key for key in publishers.ranges}
	# Initialize an RGB image (black by default)
	rgb_image = np.zeros((output_size, output_size, 3), dtype=np.uint8)

	for key_no_hyphen, original_key in prefix_keys.items():
		key_len = len(key_no_hyphen)
		
		# Create a boolean mask for all elements matching this prefix
		matching_mask = np.char.startswith(isbn_array_str, key_no_hyphen)
		matching_indices = np.argwhere(matching_mask)  # Positions of matches
		# Iterate over all matching positions for the current key
		for y, x in matching_indices:
			isbn = isbn_array_str[y, x]
			remainder = isbn[key_len:-1]
			# Process range conditions for the current key
			for index2, (start, end, length) in enumerate(publishers.ranges[original_key]):
				#print(isbn,remainder,start,end)
				if start <= float(remainder) <= end and length>0:
					i = int(str(list(prefix_keys.keys()).index(key_no_hyphen)) + str(index2))
					rgb_image[y, x] = ((i * 55+128) % 256, (i * 116+128) % 256, (i * 221+128) % 256)

	# Save the generated image
	cv2.imwrite(tile_file, rgb_image, [cv2.IMWRITE_WEBP_QUALITY, 1000])
	print(f"Publisher image created: {tile_file}.")
	return tile_file

def main():
	print("No need to run as main program, this gets imported by get_tile.py")

if __name__ == '__main__':
	main()