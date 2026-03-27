from bson import ObjectId
from bson.errors import InvalidId


def to_object_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError):
        return None


def serialize_document(document):
    if not document:
        return None
    serialized = {**document}
    if "_id" in serialized:
        serialized["id"] = str(serialized.pop("_id"))
    return serialized
