from .Callback import Callback
from .Open import Open

import enum

class Types(enum.Enum):
	Callback = "Callback"
	LongPoll = "LongPoll"
	Open = "Open"