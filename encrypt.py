import argparse
import pathlib
import qrcode
import cv2
import stegano
import numpy as np
from PIL import Image
from stegano import lsb

# Command line options
parser = argparse.ArgumentParser(
	description = "Uses QR codes to steganograph binary data in a video file.")
parser.add_argument("-v", "--video",
	type = pathlib.Path,
	required = True,
	help = "Video to use for the encryption.")
parser.add_argument("-b", "--binary",
	type = pathlib.Path,
	required = True,
	help = "Binary to encrypt in the video file.")
parser.add_argument("-o", "--output",
	type = pathlib.Path,
	required = True,
	help = "Video file where to save the encrypted version.")
parser.add_argument("--verbose",
	action = "store_true")
args = parser.parse_args()

# Set up the input binary file and video file
if not args.binary.is_file():
	raise ErrorBinaryFile("[ERROR] The binary file does not exist!")
else:
	binary_file = args.binary
	if args.verbose:
		print(f"[INFO] We will use the binary file: '{binary_file}'.")

if not args.video.is_file():
	raise ErrorVideoFile("[ERROR] The video to use for encryption does not exist!")
else:
	video_file = args.video
	if args.verbose:
		print(f"[INFO] We will use the video file: '{video_file}'.")

if args.output.exists() and args.output.samefile(video_file):
	raise ErrorOutputVideoFile("[ERROR] The video to use for encryption is the same as the output video!")
else:
	output_video_file = args.output
	if args.verbose:
		print(f"[INFO] We will output the encrypted file in the video: '{output_video_file}'.")

# Set up the QR code size and error correction level
if args.verbose:
	print("[INFO] Set up the QR code size and error correction level…")

qr_size = 200
qr_error_correction = qrcode.constants.ERROR_CORRECT_L

# Load the binary file
if args.verbose:
	print("[INFO] Load the binary file…")

with binary_file.open('rb') as f:
	binary_data = f.read()

# Convert the binary data into a list of QR codes
if args.verbose:
	print("[INFO] Convert the binary data into a list of QR codes…")

qr_codes = []
chunk_size = 200  # Adjust this value as necessary
for i in range(0, len(binary_data), chunk_size):
	chunk = binary_data[i:i + chunk_size]
	qr_code = qrcode.QRCode(
		version = 1,
		box_size = 10,
		border=0)
	qr_code.add_data(chunk)
	qr_code.make(fit = True)
	qr_codes.append(qr_code)

# Open the video file and get these properties
if args.verbose:
	print("[INFO] Open the video file and get these properties…")

video_cap = cv2.VideoCapture(str(video_file))
frame_width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(video_cap.get(cv2.CAP_PROP_FPS))
n_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Create the codec to save the video in the same format as the original
if args.verbose:
	print("[INFO] Create the codec to save the video in the same format as the original…")

fourcc = int(video_cap.get(cv2.CAP_PROP_FOURCC))
video_out = cv2.VideoWriter(str(output_video_file), fourcc, fps, (frame_width, frame_height), True)

# Iterate over the frames in the input video
if args.verbose:
	print("[INFO] Iterate over the frames in the input video…")
frame_count = 0
while video_cap.isOpened():
	# Read in the next frame of the video
	success, frame = video_cap.read()
	if not success:
		break

	image = Image.fromarray(frame)

	# Calculate the number of QR codes that can be inserted into this frame
	max_qr_codes = int((image.size[0] * image.size[1]) / (qr_size * qr_size))

	# If there are no QR codes left to insert, continue to the next frame
	if len(qr_codes) == 0:
		continue

	# Insert as many QR codes as possible into this frame
	n_qr_codes = min(max_qr_codes, len(qr_codes))
	for j in range(n_qr_codes):
		# Convert the QR code to an image
		qr_code = qr_codes[j]
		qr_code_image = qr_code.make_image(
			fill_color = "black",
			back_color = "white")
		qr_code_image_pil = qr_code_image.convert("RGB")

		# Hide the QR code in the frame using steganography
		steg_image = lsb.hide(image, qr_code_image_pil)

		# Remove the QR code from the list
		qr_codes.pop(j)

	# Convert the image back to a numpy array and write the frame to the video
	frame = np.array(steg_image)
	video_out.write(frame)
	frame_count += 1

if args.verbose:
	# Print the number of frames written to the output video
	print(f"[INFO] Number of frames in output video: {frame_count}.")

# Release the videos files
if args.verbose:
	print("[INFO] Release the videos files…")

video_cap.release()
video_out.release()