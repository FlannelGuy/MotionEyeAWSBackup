import os
from pathlib import Path, PurePath, PurePosixPath

import pysftp
import datetime
from config import Config
from cryptography.fernet import Fernet

# key = Fernet.generate_key()
# with open('filekey.key','wb') as filekey:
#     filekey.write(key)
