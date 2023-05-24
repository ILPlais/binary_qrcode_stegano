import pytest
import subprocess

subprocess.call([
	"python3",
	"encrypt.py",
	"--video", "test/La vérité sur notre société-Mr Robot [tJaLHsPDuQ4].mp4",
	"--binary", "test/free-software-song.ogg",
	"--output", "test/output.mp4", "--verbose"])