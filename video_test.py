import cv2

from filedialog import FileDialog

import tui

import ansi

import asyncio

import numpy as np

import math

def image_to_ascii(img: np.ndarray) -> str:
	columns, rows = tui.get_terminal_size()

	width = img.shape[1]

	height = img.shape[0]

	tui.print(tui.ljust(f"{width, height}", columns))

async def main() -> None:
	file = await FileDialog("Choice some video file", dir="/mnt/SSD/Projects/Future/dataset/Grand Theft Auto V", multiple=False, gui=False).choice_file(filters=[".mp4", ".avi"])

	if not file:
		tui.print("File not selected")

		return
	
	video = cv2.VideoCapture(file)

	ret, frame = video.read()

	tui.print(frame.shape)

	orig_height, orig_width, _ = frame.shape

	delta = orig_height / orig_width

	width = 240

	height = int(width * delta)

	size_gcd = math.gcd(orig_width, orig_height)

	width_ratio = orig_width / size_gcd

	height_ratio = orig_height / size_gcd

	tui.print(f"aspect ratio: {tui.parse_print_int(width_ratio)}/{tui.parse_print_int(height_ratio)}")

	while ret:
		tui.set_cursor_pos(0, 0)

		frame = cv2.resize(frame, (width, height), interpolation=0)

		frame = cv2.resize(frame, (1600, int(1600 * delta)), interpolation=0)

		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		tui.print(image_to_ascii(frame))

		cv2.imshow("Frame", frame)

		if cv2.waitKey(16) == ord('q'):
			break

		ret, frame = video.read()

	video.release()

	cv2.destroyAllWindows()

settings = tui.switch_to_raw()

print(ansi.invisible_cursor, end='')

try:
	asyncio.run(main())	
finally:
	print(ansi.visible_cursor, end='')

	tui.switch_to_default(settings)

#vid = cv2.VideoCapture("")