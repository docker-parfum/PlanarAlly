import json
from typing import Any, Dict

from peewee import ForeignKeyField, TextField
from playhouse.shortcuts import model_to_dict

from .base import BaseModel
from .user import User

__all__ = ["Asset"]


class Asset(BaseModel):
    owner = ForeignKeyField(User, backref="assets", on_delete="CASCADE")
    parent = ForeignKeyField("self", backref="children", null=True, on_delete="CASCADE")
    name = TextField()
    file_hash = TextField(null=True)
    options = TextField(null=True)

    def __repr__(self):
        return f"<Asset {self.owner.name} - {self.name}>"

    def get_options(self) -> Dict[str, Any]:
        return dict(json.loads(self.options))

    def set_options(self, options: Dict[str, Any]) -> None:
        self.options = json.dumps([[k, v] for k, v in options.items()])

    def as_dict(self, children=False, recursive=False):
        asset = model_to_dict(self, exclude=[Asset.owner, Asset.parent])
        if children:
            asset["children"] = [
                child.as_dict(children=children and recursive, recursive=recursive)
                for child in Asset.select().where(
                    (Asset.owner == self.owner) & (Asset.parent == self)
                )
            ]
        return asset

    def get_child(self, name: str) -> "Asset":
        return Asset.get(
            (Asset.owner == self.owner) & (Asset.parent == self) & (Asset.name == name)
        )

    @classmethod
    def get_root_folder(cls, user):
        try:
            root = cls.get(name="/", owner=user, parent=None)
        except Asset.DoesNotExist:
            root = cls.create(name="/", owner=user, parent=None)
        return root

    @classmethod
    def get_user_structure(cls, user, parent=None):
        if parent is None:
            parent = cls.get_root_folder(user)
        # ideally we change this to a single query to get all assets and process them as such
        data = {"__files": []}
        for asset in Asset.select().where(
            (Asset.owner == user) & (Asset.parent == parent)
        ):
            if asset.file_hash:
                data["__files"].append(
                    {"id": asset.id, "name": asset.name, "hash": asset.file_hash}
                )
            else:
                data[asset.name] = cls.get_user_structure(user, asset)
        return data
