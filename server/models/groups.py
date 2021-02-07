from peewee import TextField

from .base import BaseModel


class Group(BaseModel):
    uuid = TextField(primary_key=True)
    character_set = TextField(default="0,1,2,3,4,5,6,7,8,9")
    creation_order = TextField(default="incrementing")
