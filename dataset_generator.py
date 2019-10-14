from PIL import Image
import numpy as np
import os
import sys
import math
import argparse
import functools
import shutil

from noise_estimator import estimator
from utils import print_inline
from config import CONFIG
import dcraw

INPUT_IMAGE_EXTENSION = '.bmp'
OUPTUT_IMAGE_EXTENSION = '.png'

OUTPUT_INPUT_IMAGE_DIR = 'input'
OUTPUT_GROUNDTRUTH_IMAGE_DIR = 'output'

SUBSAMPLING_BLOCK_SIZE = 5
CHUNK_SIZE_MULTIPLIER = 30000
CHUNK_SIZE = SUBSAMPLING_BLOCK_SIZE * CHUNK_SIZE_MULTIPLIER
BAYER_PATTERN = [
  [0, 1],
  [1, 2]
]

NOISE_A_MAX_VALUE = 0.01
NOISE_A_MIN_VALUE = 0
NOISE_B_MAX_VALUE = 0.0004
NOISE_B_MIN_VALUE = 0

'''
  Given an image with three channels (RGB) this function returns a mono-channel
  image which corresponds to the mosaiced image using the Bayer pattern.

  Parameters:
    - original_image: a PIL image with three channels.
'''
def three_channel_to_bayer(original_image):
  original_width, original_height = original_image.size
  new_image = np.zeros((original_width, original_height), dtype=np.int8)
  for i in range(0, original_width):
    for j in range(0, original_height):
      current_channel = BAYER_PATTERN[i % 2][j % 2]
      new_image[i][j] = original_image.getpixel((i, j))[current_channel]
  return Image.fromarray(np.matrix.transpose(new_image), mode='L')

'''
  Given a mono-channel PIL image and a block size, this function returns a numpy matrix
  with three dimensions (W/B, H/B, 3), where W is the original image's width,
  H is the original image's height, B is the block size, and the last dimension represents
  the three usual RGB channels. The input image is assumed to be mosaiced using the Bayer pattern.

  The value of each channel is determined by taking the corresponding block of the input
  image and averaging the pixels that correspond to that color.

  Parameters:
    - image: a mono-channel PIL image that represents a mosaiced image using the Bayer pattern.
    - block_size: a non-zero positive integer. Blocks are square, and the recommended values are
                  3 or 5. You can experiment with different values though.
'''
def subsample_image(image, block_size):
  new_width = math.floor(image.shape[0] / block_size)
  new_height = math.floor(image.shape[1] / block_size)
  subsampled_matrix = np.zeros((new_height, new_width, 3), dtype=np.int8)
  for i in range(0, new_height):
    for j in range(0, new_width):
      channel_values = [0, 0, 0]
      channel_count = [0, 0, 0]
      for k in range(i * block_size, (i * block_size) + block_size):
        for l in range(j * block_size, (j * block_size) + block_size):
          current_channel = BAYER_PATTERN[l % 2][k % 2]
          channel_values[current_channel] += image[l][k]
          channel_count[current_channel] += 1
      subsampled_matrix[i][j][0] = math.floor(channel_values[0] / channel_count[0])
      subsampled_matrix[i][j][1] = math.floor(channel_values[1] / channel_count[1])
      subsampled_matrix[i][j][2] = math.floor(channel_values[2] / channel_count[2])
  return subsampled_matrix

'''
  Given the path to a directory and a list of file extensions, returns a list of file names
  in that directory that match any of those extensions.

  Parameters:
    - dir_path: path to some directory.
    - extensions: list of valid extensions (the dot that separates the name from extension must not be provided).
'''
def get_input_images_from_dir(dir_path, extensions):
  files = os.listdir(dir_path)
  return [
    os.path.join(dir_path, filename)
    for filename in files
    if functools.reduce((lambda acc, val: acc or os.path.splitext(filename)[1] == '.' + val), extensions, False)
  ]

def split_image_into_chunks(image):
  width, height = image.size
  if (width * height < (CHUNK_SIZE ** 2)):
      return [[image]]

  row_amount = math.ceil(height / CHUNK_SIZE)
  column_amount = math.ceil(width / CHUNK_SIZE)

  matrix = []
  for row_index in range (0, row_amount):
    row = []
    for column_index in range (0, column_amount):
      initial_row = row_index * CHUNK_SIZE
      final_row = min((row_index + 1) * CHUNK_SIZE, height)
      initial_column = column_index * CHUNK_SIZE
      final_column = min((column_index + 1) * CHUNK_SIZE, width)
      crop_box = (initial_column, initial_row, final_column, final_row)
      chunk = image.crop(crop_box)
      # Cropping is a lazy operation so we need to force the creation of a new
      # image, this is done with the load() function.
      chunk.load()
      row.append(chunk)
    matrix.append(row)
  return matrix

def join_chunks_into_image(chunk_matrix):
  last_width = chunk_matrix[0][-1].width
  last_height = chunk_matrix[-1][0].height
  width_image = (len(chunk_matrix[0]) - 1) * CHUNK_SIZE_MULTIPLIER + last_width
  height_image = (len(chunk_matrix) - 1) * CHUNK_SIZE_MULTIPLIER + last_height
  new_image = Image.new(chunk_matrix[0][0].mode, (width_image, height_image))

  for (current_row, row) in enumerate(chunk_matrix):
    for (current_column, chunk) in enumerate(row):
      new_image.paste(chunk, (current_column * CHUNK_SIZE_MULTIPLIER, current_row * CHUNK_SIZE_MULTIPLIER))

  return new_image

'''
  Given a file path and a block size, generates input and groundtruth images
  and returns them in a tuple.

  Parameters:
    - filepath: a path to the raw image file to use.
    - block_size: integer to use as block size when subsampling the image.

  Returns: two-item tuple containing the input image and groundtruth image in that order.
  Both are instances of PIL.Image.
'''
def generate_pair(filepath, block_size, add_noise):
  base_log = 'Processing ' + filepath + ' - '
  print_inline(base_log + 'reading raw')
  raw_image = dcraw.read_raw(filepath)
  chunk_matrix = split_image_into_chunks(raw_image)
  subsampled_chunks = []
  new_original_chunks = []
  print_inline(base_log + 'subsampling ' + str(len(chunk_matrix) * len(chunk_matrix[0])) + ' chunks')
  for row_index, row in enumerate(chunk_matrix):
    subsampled_row = []
    new_original_row = []
    for index, chunk in enumerate(row):
      if add_noise:
        [noise_params] = estimator.estimate_noise(chunk)
        # Clip the noise to a reasonable interval
        noise_params = [
          max(NOISE_A_MIN_VALUE, min(NOISE_A_MAX_VALUE, noise_params[0])),
          max(NOISE_B_MIN_VALUE, min(NOISE_B_MAX_VALUE, noise_params[1]))
        ]
      numpy_image = np.matrix.transpose(np.array(chunk))
      subsampled_chunk = subsample_image(numpy_image, block_size)
      groundtruth_chunk = Image.fromarray(subsampled_chunk, mode='RGB')
      input_chunk = three_channel_to_bayer(groundtruth_chunk)
      if add_noise:
        numpy_input_chunk = np.matrix.transpose(np.array(input_chunk))
        noised_input_chunk = estimator.apply_noise(numpy_input_chunk, noise_params[0], noise_params[1])
        input_chunk = Image.fromarray(np.matrix.transpose(noised_input_chunk), mode='L')
      subsampled_row.append(groundtruth_chunk)
      new_original_row.append(input_chunk)
    subsampled_chunks.append(subsampled_row)
    new_original_chunks.append(new_original_row)

  groundtruth_image = join_chunks_into_image(subsampled_chunks)
  new_original_image = join_chunks_into_image(new_original_chunks)

  # Generated images must have even dimensions.
  width, height = groundtruth_image.size
  if width % 2 != 0 or height % 2 != 0:
    new_width = width if width % 2 == 0 else (width - 1)
    new_height = height if height % 2 == 0 else (height - 1)
    groundtruth_image = groundtruth_image.crop((0, 0, new_width, new_height))
    new_original_image = new_original_image.crop((0, 0, new_width, new_height))

  print_inline(base_log + 'creating initial image')
  return new_original_image, groundtruth_image

'''
  Given a directory path, ensures the directories for input and groundtruth images exist.
  Throws an exception if any of those exist already.
'''
def ensure_directories(base_dir, force):
  input_dir = os.path.join(base_dir, OUTPUT_INPUT_IMAGE_DIR)
  groundtruth_dir = os.path.join(base_dir, OUTPUT_GROUNDTRUTH_IMAGE_DIR)
  if os.path.exists(input_dir) or os.path.exists(groundtruth_dir):
    if not force:
      raise Exception('Could not create output directories, check that "' + input_dir + '" and "' + groundtruth_dir + '" do not exist yet.' )
    if os.path.exists(input_dir):
      shutil.rmtree(input_dir)
    if os.path.exists(groundtruth_dir):
      shutil.rmtree(groundtruth_dir)
  os.mkdir(input_dir)
  os.mkdir(groundtruth_dir)

def generate_dataset(directory, extension, block_size=CONFIG['subsampling_block_size'], force=False, add_noise=False):
  arguments = setup_args()
  input_image_names = get_input_images_from_dir(directory, extension)
  ensure_directories(directory, force)
  for filepath in input_image_names:
    input_image, groundtruth_image = generate_pair(filepath, block_size, add_noise)
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    input_path = os.path.join(directory, OUTPUT_INPUT_IMAGE_DIR, base_filename + INPUT_IMAGE_EXTENSION)
    groundtruth_path = os.path.join(directory, OUTPUT_GROUNDTRUTH_IMAGE_DIR, base_filename + OUPTUT_IMAGE_EXTENSION)
    input_image.save(input_path)
    groundtruth_image.save(groundtruth_path)
