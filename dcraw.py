import subprocess
from PIL import Image
import io

DCRAW = 'dcraw'
VERBOSE = '-v'
DOCUMENT_MODE = '-d'
USE_STDOUT = '-c'
CAMERA_WHITE_BALANCE = '-W'

# This file relies on `dcraw`. Please be sure you have it installed on your system.
# To download `dcraw`, visit https://www.cybercom.net/~dcoffin/dcraw/

def read_raw(image_path):
  # Use dcraw to interpret the raw image.
  # The image is obtained from piping the standard output.
  a = subprocess.run([DCRAW, DOCUMENT_MODE, USE_STDOUT, CAMERA_WHITE_BALANCE, image_path], stdout=subprocess.PIPE)
  a.check_returncode()
  # Mount the image using Pillow, by reading the standard output as
  # a sequence of bytes.
  raw_image = Image.open(io.BytesIO(a.stdout))
  return raw_image


