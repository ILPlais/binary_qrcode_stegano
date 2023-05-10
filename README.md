# binary_qrcode_stegano
Uses QR codes to steganograph binary data in a video.

**⚠️ This project is more a proof of concept than a program who can be really use to hide a lot of data in a video.**

## Installation
For Debian likes distributions you have to install the package `python3-opencv` to use the videos manipulation library.
And install the packages `libzbar0` and `libzbar-dev` for decoding the DR codes.
Then you have to install the requirements with the command:
`$ pip3 install -r requirements.txt`

## Using the scripts
### Encryption
```
usage: encrypt.py [-h] -v VIDEO -b BINARY -o OUTPUT [--verbose]

Uses QR codes to steganograph binary data in a video file.

options:
  -h, --help            show this help message and exit
  -v VIDEO, --video VIDEO
                        Video to use for the encryption.
  -b BINARY, --binary BINARY
                        Binary to encrypt in the video file.
  -o OUTPUT, --output OUTPUT
                        Video file where to save the encrypted version.
  --verbose             Display informations messages.
```

### Decryption
```
usage: decrypt.py [-h] -v VIDEO -o OUTPUT [--verbose]

Uses QR codes to steganograph binary data in a video file.

options:
  -h, --help            show this help message and exit
  -v VIDEO, --video VIDEO
                        Video containing the encrypted binary file.
  -o OUTPUT, --output OUTPUT
                        Path to extract the binary file.
  --verbose             Display informations messages.
```
