from datetime import datetime
from flask import Blueprint, request, g

from esg_lib.audit_logger.models.AuditLog import AuditLog
from esg_lib.audit_logger.utils import get_json_body, get_only_changed_values_and_id, get_action, get_primary_key_value
from esg_lib.constants import IGNORE_PATHS


SUCCESS_STATUS_CODES = [200, 201, 204]
DEFAULT_LOG_METHODS = ["POST", "PUT", "DELETE", "PATCH"]
# DEFAULT_LOG_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]
PRIMARY_KEY_MAPPING = {
    "target_settings": "action",
    "attachments": "filename",
    "bilan_carbon": "campaign_name",
    "bilan_factor": "type_emission.large_name",
    "form_checks": "technical_check",
    "notifications": "content",
    "users": "email",
    "ref_sectors": "label",
    "entity_domaines": "h1"
}
AUDIT_COLLECTION_NAME = "audit"


class AuditBlueprint(Blueprint):
    """
        AuditBlueprint is a blueprint that logs changes to a collection in a MongoDB database.
    """
    def __init__(self, *args, **kwargs):
        self.log_methods = kwargs.pop("log_methods", DEFAULT_LOG_METHODS)
        self.audit_collection = None

        super(AuditBlueprint, self).__init__(*args, **kwargs)
        self.after_request(self.after_data_request)

    def _is_loggable(self, response) -> bool:
        return request.method in self.log_methods and response.status_code in SUCCESS_STATUS_CODES

    def after_data_request(self, response):
        table_name = g.get("table_name")
        endpoint = request.path

        if not table_name or table_name == AUDIT_COLLECTION_NAME or endpoint in IGNORE_PATHS or "swagger" in endpoint:
            return response

        primary_key = PRIMARY_KEY_MAPPING.get(table_name, "name")
        primary_key_splits = primary_key.split(".")

        if self._is_loggable(response):
            old_data = g.get("old_data", None)

            if g.get("new_data"):
                new_data = g.new_data
            else:
                new_data = get_json_body(request)

            if request.method == 'DELETE':
                new_data = new_data or None
                if old_data:
                    if isinstance(old_data, list):
                        old_data = [
                            {
                                "_id": d.get("_id"),
                                "name": get_primary_key_value(primary_key_splits, d)
                            } for d in old_data
                        ]
                    else:
                        _id = old_data.get("_id")
                        primary_value = get_primary_key_value(primary_key_splits, old_data)
                        old_data = {
                            "_id": _id,
                            "name": primary_value
                        }

            elif request.method == 'GET':
                new_data = old_data = None
            else:
                if g.get("new_data") is None:
                    new_data, old_data = get_only_changed_values_and_id(old_data or {}, new_data) if old_data else (new_data, old_data)

                if response.status_code == 201:
                    if isinstance(new_data, list):
                        final_value = [get_primary_key_value(primary_key_splits, d) for d in new_data]
                        new_data = {
                            "name": ",".join(final_value) if final_value else ""
                        }
                    else:
                        primary_value = get_primary_key_value(primary_key_splits, new_data)
                        new_data = {
                            "name": primary_value
                        }


            action = get_action(request.method, response.status_code)
            self.create_log(action, endpoint, new_value=new_data, old_value=old_data)

        return response

    def create_log(self, action: str, endpoint: str, new_value=None, old_value=None):
        user_info = g.auth_user if g.get("auth_user") else {"email": "dummy@email.com", "fullname": "Dummy Name"}

        audit_log = {
            "collection": g.get("table_name"),
            "action": action,
            "endpoint": endpoint,
            "user": user_info,
            "old_value": old_value,
            "new_value": new_value,
            "created_on": datetime.utcnow()
        }
        action = AuditLog(**audit_log)
        action.save()
