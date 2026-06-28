import tui, utils

from audioplayer import AudioPlayer

from mutagen import id3

from PIL import Image
import io

import numpy as np

from pathlib import Path

if __name__ == "__main__":
	path = Path("/run/media/rdev/SSD/Downloads/Песни/Любимые песни/")

	

	# path = "/run/media/rdev/SSD/Downloads/Песни/Любимые песни/Sergejj_Lazarev_-_JEto_vse_ona_63026289.mp3"
	# # path = "10AGE_-_Netu_interesa_72834647.mp3"

	# img_path = "/home/rdev/Загрузки/Сергей Лазарев -- Это всё она.jpg"

	# _bytes = io.BytesIO()

	# img = Image.open(img_path)

	# img = img.convert("RGB")

	# img.save(_bytes, format="JPEG")

	# img.close()

	# _bytes = _bytes.getvalue()

	# id = id3.Open(path)

	# for i, item in enumerate(id.items()):
	# 	if "APIC" in item[0]:
	# 		id.delall(item[0])

	# apic = id3.APIC()

	# apic.encoding = id3.Encoding.LATIN1
	# apic.mime = "image/jpeg"
	# apic.type = id3.PictureType.OTHER
	# apic.desc = "jpeg"
	# apic.data = _bytes

	# id.add(apic)

	# # print(str(id)[:10000])

	# id.save(path)

