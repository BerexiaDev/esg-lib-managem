from esg_lib.document import Document


class User(Document):
    __TABLE__ = 'users'

    _id = None
    email = None
    role = None
