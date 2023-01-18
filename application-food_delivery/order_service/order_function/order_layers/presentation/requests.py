# """Domainとは関係ない、WebからのRequest Parameter
# """
# import dataclasses
#
#
# @dataclasses.dataclass(frozen=True)
# class MenuItemIdAndQuantity:
#     menu_id: str
#     quantity: int
#
#     @classmethod
#     def from_dict(cls, body_dict):
#         return cls(**body_dict)
