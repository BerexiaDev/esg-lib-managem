from esg_lib.document import Document


class AuditLog(Document):
    __TABLE__ = "audit"

    _id = None
    collection = None
    action = None
    endpoint = None
    user = None
    old_value = None
    new_value = None
    created_on = None
