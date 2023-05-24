import argparse
import pathlib
import cv2
import qrcode
import base64
from tqdm import tqdm
from PIL import Image
from steganography import Steganography

def encode_binary_in_base64(binary_file):
	"""Encodes a binary file into Base 64.

	Parameters
	----------
	binary_file : bytes
		Binary file to convert into Base 64.

	Returns
	-------
	bytes
		The binary file encoded in Base 64.
	"""
	with binary_file.open('rb') as f:
		binary_data = f.read()

	return base64.b64encode(binary_data)

def embed_qr_code_in_frame(frame, qr_code):
	"""Embeds a QR code in a video frame.

	Parameters
	----------
	frame : numpy.ndarray
		The video frame to embed the QR code in.
	qr_code : qrcode.main.QRCode
		The bytes of the QR code to embed in the video frame.
	"""
	# Convert the QR code bytes to a QR code image
	qr_code_image = qr_code.make_image(
		fill_color = "black",
		back_color = "white")

	# Find the center of the video frame
	frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)

	# Create the QR code to steganograph in the frame
	qr_code_image_pil = qr_code_image.convert("RGB")
			
	# Hide the QR code in the frame using steganography
	frame_qr_code = frame[frame_center[0] - qr_code_image_pil.height // 2, frame_center[1] + qr_code_image_pil.width // 2]
	frame_qr_code = Steganography().merge(frame_qr_code, qr_code_image_pil)

def embed_qr_codes_in_video(video_file, binary_file, output_video_file):
	"""Embeds QR codes in a video file.
	
	Parameters
	----------
	video_file : pathlib.Path
		The path to the video file to use for embedding QR codes.
	binary_file : pathlib.Path
		The binary file to encrypt in the video file.
	output_video_file : pathlib.Path
		The path to the output video file where to save the encrypted version.
	"""
	# Open the video file
	if args.verbose:
		print("[INFO] Open the video file…")
	video = cv2.VideoCapture(str(video_file))

	# Get the number of frames in the video
	if args.verbose:
		print("[INFO] Get the number of frames in the video…")
	num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
	if args.verbose:
		print(f"[INFO] There is {num_frames} frames in the video.")

	# Create a list to store the QR codes
	qr_codes = []

	# Encode the binary file into Base 64
	if args.verbose:
		print("[INFO] Encode the binary file into Base 64…")
	base64_file = encode_binary_in_base64(binary_file)

	# Set up the QR code size and error correction level
	if args.verbose:
		print("[INFO] Set up the QR code size and error correction level…")

	qr_version = 40
	qr_size = 200
	qr_error_correction = qrcode.constants.ERROR_CORRECT_M

	# Maximum of characters for QR code of the version
	chunk_size = qrcode.make(
		"Test",
		version = qr_version,
		border = 0,
		error_correction = qr_error_correction).size[0] - 1

	if args.verbose:
		print(f"[INFO] They can be {chunk_size} ASCII characters by QR code.")

	# Convert the binary data into a list of QR codes
	if args.verbose:
		print("[INFO] Convert the binary data into a list of QR codes…")

	for i in tqdm(range(0, len(base64_file), chunk_size)):
		chunk = base64_file[i:i + chunk_size]
		qr_code = qrcode.QRCode(
			version = qr_version,
			box_size = qr_size,
			error_correction = qr_error_correction,
			border = 0)
		qr_code.add_data(chunk)
		qr_code.make(fit = True)
		qr_codes.append(qr_code)

	# Check if there is enought frames in the video for all the QR codes
	if len(qr_codes) > num_frames:
		raise ErrorNumFrames("[ERROR] There is not enought frames in the video for all the file!")

	# Embed the QR codes in the video frames
	for i in tqdm(range(num_frames)):
		embed_qr_code_in_frame(video.read()[1], qr_codes[i])

	# Close the video file
	video.release()

	# Save the video file with the embedded QR codes
	cv2.VideoWriter(
		str(output_video_file),
		cv2.VideoWriter_fourcc(*'mkv1'),
		video.get(cv2.CAP_PROP_FPS),
		(video.get(cv2.CAP_PROP_FRAME_WIDTH),
		video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
		True,
		cv2.CAP_WRITE_AUDIO,
		cv2.CAP_WRITE_SUBTITLES).write(video.read()[0])

if __name__ == "__main__":
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
		action = "store_true",
		help = "Display informations messages.")
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

	# Embed the QR codes in the video file
	embed_qr_codes_in_video(video_file, binary_file, output_video_file)

	# Print a message to indicate that the process is complete
	if args.verbose:
		print(f"[INFO] The process is complete. The output video file is '{output_video_file}'.")