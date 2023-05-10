import argparse
import pathlib
import zbarlight
import cv2
import numpy as np
from steganography import Steganography
from PIL import Image
from tqdm import tqdm

# Command line options
parser = argparse.ArgumentParser(
	description = "Uses QR codes to steganograph binary data in a video file.")
parser.add_argument("-v", "--video",
	type = pathlib.Path,
	required = True,
	help = "Video containing the encrypted binary file.")
parser.add_argument("-o", "--output",
	type = pathlib.Path,
	required = True,
	help = "Path to extract the binary file.")
parser.add_argument("--verbose",
	action = "store_true",
	help = "Display informations messages.")
args = parser.parse_args()

# Set up the input video file
if not args.video.is_file():
	raise ErrorVideoFile("[ERROR] The video file does not exist!")
else:
	video_file = args.video
	if args.verbose:
		print(f"[INFO] We will use the video file: {video_file}.")

# Set up the output binary file
if args.output.exist() and args.output.samefile(video_file):
	raise ErrorOutputBinaryFile("[ERROR] The file to use to output the binary datas is the same as the encrypted video file!")
else:
	output_binary_file = args.output
	if args.verbose:
		print(f"[INFO] We will output the encrypted datas in the file: '{output_binary_file}'.")

# Open the video file
if args.verbose:
	print(f"[INFO] Open the video file…")

video_cap = cv2.VideoCapture(str(video_file))

# Set up the binary data buffer
binary_data = ""

# Loop through each frame of the video
for i in tqdm(range(int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT)))):
	# Read the frame
	success, frame = video_cap.read()
	if not success:
		break

	# Extract the QR code from the frame
	qr_code_image_pil = Steganography().unmerge(frame)

	# Detect QR codes in the frame
	qr_code_data = zbarlight.scan_codes("qrcode", qr_code_image_pil)

	# If a QR code was detected, extract the steganographed binary data
	if qr_code_data is not None:
		binary_data += steg.extract_binary_data(qr_code_data)

# Write the binary data to the output file
with open(output_binary_file, "wb") as f:
	f.write(binary_data.encode())

# Release the video file
if args.verbose:
	print("[INFO] Release the video file…")

video_cap.release()