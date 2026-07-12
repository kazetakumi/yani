"""Icon — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import WEIGHT_DESC


IconName = Literal[
    "accountCircle", "add", "arrowBack", "arrowForward", "attachFile",
    "calendarToday", "call", "camera", "check", "close",
    "delete", "download", "edit", "event", "error",
    "fastForward", "favorite", "favoriteOff", "folder", "help",
    "home", "info", "locationOn", "lock", "lockOpen",
    "mail", "menu", "moreVert", "moreHoriz", "notificationsOff",
    "notifications", "pause", "payment", "person", "phone",
    "photo", "play", "print", "refresh", "rewind",
    "search", "send", "settings", "share", "shoppingCart",
    "skipNext", "skipPrevious", "star", "starHalf", "starOff",
    "stop", "upload", "visibility", "visibilityOff",
    "volumeDown", "volumeMute", "volumeOff", "volumeUp", "warning",
]


class IconProps(BaseModel):
    name: IconName = Field(description="icon name from the fixed set")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class IconComponent(BaseModel):
    id: str
    component: Literal["Icon"]
    props: IconProps
