import argparse

from config import CONFIG
from dataset_generator import generate_dataset

def setup_args():
  parser = argparse.ArgumentParser(
    description='Demosaicing dataset generator.'
  )

  parser.add_argument(
    '-e',
    action='append',
    help='extension of raw images to process',
    required=True,
    type=str
  )
  parser.add_argument(
    '-s',
    help='block size, must be a positive integer',
    default=CONFIG['subsampling_block_size'],
    type=int
  )
  parser.add_argument(
    '-f',
    action='store_true',
    help='Forces the deletion of result directories if they already exists. Use carefully',
    default=False
  )
  parser.add_argument(
    '-n',
    '--add-noise',
    action='store_true',
    help='Adds noise to resulting images',
    default=False
  )
  parser.add_argument(
    'directory',
    help='Directory to search raw images in.'
  )
  return parser.parse_args()

def main():
  arguments = setup_args()
  generate_dataset(arguments.directory, arguments.e, block_size=arguments.s, force=arguments.f, add_noise=arguments.add_noise)

main()
