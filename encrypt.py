import argparse
import tempfile
import pathlib
import cv2
import qrcode
import base64
import numpy
import subprocess
from tqdm import tqdm
from PIL import Image, ImageEnhance

def encode_binary_in_base64(binary_file) -> bytes:
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

def embed_qr_code_in_frame(
	frame: numpy.ndarray,
	qr_code: qrcode.main.QRCode
) -> numpy.ndarray:
	"""Embeds a QR code in a video frame.

	Parameters
	----------
	frame : numpy.ndarray
		The video frame to embed the QR code in.
	qr_code : qrcode.main.QRCode
		The bytes of the QR code to embed in the video frame.

	Returns
	-------
	numpy.ndarray
		The frame to add to the output video.
	"""

	# Convert the QR code bytes to a QR code image
	qr_code_image = qr_code.make_image(
		fill_color = "black",
		back_color = "white"
	)

	# Create the QR code to hide in the frame
	qr_code_image_pil = qr_code_image.convert("RGBA")

	# Set the alpha channel of the QR code to 25%
	qr_code_image_pil.putalpha(32)

	# Get the dimensions of the frame
	frame_height, frame_width, _ = frame.shape

	# Resize the QR code to fit the frame
	if frame_width > frame_height:
		qr_code_image_pil = qr_code_image_pil.resize((frame_height, frame_height), Image.Resampling.LANCZOS)
	else:
		qr_code_image_pil = qr_code_image_pil.resize((frame_width, frame_width), Image.Resampling.LANCZOS)

	# Calculate the center of the frame
	center = (frame_width // 2 - qr_code_image_pil.width // 2, frame_height // 2 - qr_code_image_pil.height // 2)

	# Convert the frame to a PIL image
	frame_pil = Image.fromarray(frame)

	# Paste the QR code image in the middle of the frame image
	frame_pil.paste(qr_code_image_pil, center, qr_code_image_pil)

	return numpy.array(frame_pil)

def copy_audio_and_metadata_to_output(
	video_file: pathlib.Path,
	temp_video_file: pathlib.Path,
	output_video_file: pathlib.Path,
	verbose: bool = True
):
	"""Copy the audio tracks, subtitles, and metadata from a video file to the Matroska output video.

	Parameters
	----------
	video_file : pathlib.Path
		The path to the video file to use for embedding QR codes.
	temp_video_file : pathlib.Path
		The path to the temporary video file.
	output_video_file : pathlib.Path
		The path to the output video file where to save the encrypted version.
	verbose : bool
		Display informations messages.
	"""

	# Create the FFmpeg command
	if verbose:
		print("[INFO] Create the FFmpeg command…")
	command = [
		"ffmpeg",
		"-i", str(video_file),
		"-i", str(temp_video_file),
		"-c", "copy",
		"-map", "1:v",
		"-map", "0:a",
		"-map_metadata", "0",
		"-y",
		str(output_video_file)
	]

	# Start the FFmpeg subprocess
	try:
		if verbose:
			print("[INFO] Start the FFmpeg subprocess…")
		subprocess.run(command, check = True)
		if verbose:
			print("[INFO] The FFmpeg subprocess was successful.")
	except subprocess.CalledProcessError as e:
		print(f"[ERROR] FFmpeg error: {e.stderr()}")
		raise ErrorFFmpeg("[ERROR] The FFmpeg subprocess failed!")

	# Remove the temporary video
	if verbose:
		print("[INFO] Remove the temporary video…")
	temp_video_file.unlink()

def embed_qr_codes_in_video(
	video_file: pathlib.Path,
	binary_file: pathlib.Path,
	output_video_file: pathlib.Path,
	verbose: bool = True
):
	"""Embeds QR codes in a video file.

	Parameters
	----------
	video_file : pathlib.Path
		The path to the video file to use for embedding QR codes.
	binary_file : pathlib.Path
		The binary file to encrypt in the video file.
	output_video_file : pathlib.Path
		The path to the output video file where to save the encrypted version.
	verbose : bool
		Display informations messages.
	"""

	# Open the source video file
	if verbose:
		print("[INFO] Open the source video file…")
	video_cap = cv2.VideoCapture(str(video_file))
	frame_width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
	frame_height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
	fps = int(video_cap.get(cv2.CAP_PROP_FPS))

	# Get the number of frames in the video
	if verbose:
		print("[INFO] Get the number of frames in the video…")
	num_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
	if args.verbose:
		print(f"[INFO] There is {num_frames} frames in the video.")

	# Encode the binary file into Base 64
	if verbose:
		print("[INFO] Encode the binary file into Base 64…")
	base64_file = encode_binary_in_base64(binary_file)

	# Set up the QR code size and error correction level
	if verbose:
		print("[INFO] Set up the QR code size and error correction level…")

	qr_version = 40
	qr_error_correction = qrcode.constants.ERROR_CORRECT_M

	# Maximum of characters for QR code of the version
	chunk_size = qrcode.make(
		"Test",
		version = qr_version,
		border = 0,
		error_correction = qr_error_correction
	).size[0] - 1

	if verbose:
		print(f"[INFO] They can be {chunk_size} ASCII characters by QR code.")

	# Convert the binary data into a list of QR codes
	if verbose:
		print("[INFO] Convert the binary data into a list of QR codes…")

	# Create a list to store the QR codes
	qr_codes = []

	for i in tqdm(range(0, len(base64_file), chunk_size)):
		chunk = base64_file[i:i + chunk_size]
		qr_code = qrcode.QRCode(
			version = qr_version,
			error_correction = qr_error_correction,
			border = 0
		)
		qr_code.add_data(chunk)
		qr_code.make(fit = True)
		qr_codes.append(qr_code)

	# Check if there is enought frames in the video for all the QR codes
	if len(qr_codes) > num_frames:
		raise ErrorNumFrames("[ERROR] There is not enought frames in the video for all the file!")

	# Create the codec to save the video in the same format as the original
	if verbose:
		print("[INFO] Create the codec to save the video in the same format as the original…")
	fourcc = int(video_cap.get(cv2.CAP_PROP_FOURCC))

	# Create a temporary file with a specific extension
	if verbose:
		print("[INFO] Create a temporary file with a specific extension…")
	temp_output = tempfile.NamedTemporaryFile(
		suffix = ".mp4",
		delete = False
	)

	# Get the path to the temporary file
	if verbose:
		print("[INFO] Get the path to the temporary file…")
	temp_output_path = pathlib.Path(temp_output.name)

	if verbose:
		print(f"[INFO] The path to the temporary file is: '{temp_output_path}'.")

	# Create the temporary output video
	video_out = cv2.VideoWriter(
		str(temp_output_path),
		fourcc,
		fps,
		(frame_width, frame_height),
		True
	)

	# Embed the QR codes in the video frames
	if verbose:
		print("[INFO] Embed the QR codes in the video frames…")

	for i in tqdm(range(num_frames)):
		# Read in the next frame of the video
		success, frame = video_cap.read()
		if not success:
			break

		if i < len(qr_codes):
			modified_frame = embed_qr_code_in_frame(frame, qr_codes[i])
			video_out.write(modified_frame)
		else:
			video_out.write(frame)

	# Close the video files
	if verbose:
		print("[INFO] Close the video files…")

	video_cap.release()
	video_out.release()

	# Copy the rest of the source video to the output video
	copy_audio_and_metadata_to_output(
		video_file,
		temp_output_path,
		output_video_file,
		verbose
	)

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
	embed_qr_codes_in_video(
		video_file,
		binary_file,
		output_video_file,
		args.verbose
	)

	# Print a message to indicate that the process is complete
	if args.verbose:
		print(f"[INFO] The process is complete. The output video file is '{output_video_file}'.")