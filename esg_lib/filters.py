import re
from esg_lib.document import Document

collections = {
    "axe": "axes",
    "engagement": "engagements",
    "objective": "objectives",
    "entity": "entities",
    "entities": "entities",
    "group": "groups",
}


def get_ids_by_name(collection, name_field, id_field, name_value):
    """
    Fetches the ID corresponding to a given name from a MongoDB collection.
    """
    results = collection.find(
        {name_field: {"$regex": f"{name_value.strip()}", "$options": "i"}},
        {id_field: 1},
    )

    if results:
        return [r[id_field] for r in results]


def get_collection(field_code):
    collection_name = collections.get(field_code, field_code)
    return Document.get_collection(collection_name)


def build_filters(filters):
    """
    Converts the filters object into a MongoDB query.

    :param filters: Array containing filter information.
    :return: MongoDB query as a dictionary.
    """
    mongo_query = {}

    for filter_item in filters:
        # Extract filter components
        table_name, field_info = filter_item.get("field", [None, {}])
        field_code = field_info.get("code", None)
        field_type = field_info.get("type", None)
        operator = filter_item.get("operator", None)
        value = filter_item.get("value", None)

        if not table_name:
            raise ValueError("No table name")
        if not field_code:
            raise ValueError("No columns name")
        if not field_type:
            raise ValueError("No field type")
        if not operator:
            raise ValueError("No operator")
        if value != 0 and not value:  # Allow 0 as a valid value
            raise ValueError("No value provided.")

        # Handle cases where the search is done by name, but the ID is stored in the database
        if table_name in [
            "forms",
            "projects",
            "permanent_actions",
            "highlighted_actions",
            "campaigns",
            "carbon_campaigns",
        ] and field_code in [
            "axe",
            "engagement",
            "objective",
            "entity",
            "group",
            "entities",
        ]:
            collection = get_collection(field_code)
            ids_value = get_ids_by_name(collection, "name", "_id", value)
            mongo_query[field_code] = {"$in": ids_value}
            continue

        if table_name == "users" and field_code == "has_backup":
            if table_name == "users" and field_code == "has_backup":
                mongo_query["backup_id"] = {"$ne": None} if value else None
                continue

        # Handle date-specific operators
        if operator in ["BEFORE", "AFTER"]:
            if not isinstance(value, (str)):
                raise ValueError(
                    f"Value for '{operator}' operator must be a date string."
                )

            if operator == "BEFORE":
                mongo_query[field_code] = {"$lt": value}
            elif operator == "AFTER":
                mongo_query[field_code] = {"$gt": value}

        elif operator == "EQUALS":
            mongo_query[field_code] = value
        elif operator == "NOT EQUALS":
            mongo_query[field_code] = {"$ne": value}
        elif operator == "CONTAINS":
            if not isinstance(value, str):
                raise ValueError("Value for 'CONTAINS' operator must be a string.")
            mongo_query[field_code] = {"$regex": value, "$options": "i"}
        elif operator == "IN":
            regex_query = [re.compile(v, re.IGNORECASE) for v in value]
            mongo_query[field_code] = {"$in": regex_query}
        elif operator == "GREATER THAN":
            mongo_query[field_code] = {"$gt": value}
        elif operator == "LESS THAN":
            mongo_query[field_code] = {"$lt": value}
        else:
            raise ValueError(f"Unsupported operator: {operator}")

    return mongo_query
