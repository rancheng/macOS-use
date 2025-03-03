from typing import Literal, Optional

from pydantic import BaseModel

# mlx-use actions 


class DoneAction(BaseModel):
	text: str

class InputTextAction(BaseModel):
	index: int
	text: str
	submit: bool

class ClickElementAction(BaseModel):
	index: int
	action: str

class RightClickElementAction(BaseModel):
	index: int

class OpenAppAction(BaseModel):
	app_name: str

class AppleScriptAction(BaseModel):
	script: str

class ScrollElementAction(BaseModel):
	index: int
	direction: Literal['up', 'down', 'left', 'right']

# # Action Input Models
# class SearchGoogleAction(BaseModel):
# 	query: str


# class GoToUrlAction(BaseModel):
# 	url: str


# class ClickElementAction(BaseModel):
# 	index: int
# 	xpath: Optional[str] = None


# class InputTextAction(BaseModel):
# 	index: int
# 	text: str
# 	xpath: Optional[str] = None




# class SwitchTabAction(BaseModel):
# 	page_id: int


# class OpenTabAction(BaseModel):
# 	url: str


# class ExtractPageContentAction(BaseModel):
# 	include_links: bool


# class ScrollAction(BaseModel):
# 	amount: Optional[int] = None  # The number of pixels to scroll. If None, scroll down/up one page


# class SendKeysAction(BaseModel):
# 	keys: str
