from functools import wraps
from flask import request, g
from esg_lib.auth.external_auth import ExternalAuth
from esg_lib.constants import IGNORE_PATHS
from esg_lib.auth.azure_ad_auth import AzureADAuth
from esg_lib.auth.auth_helper import AuthHelper
from esg_lib.common import UserRole
from werkzeug.datastructures import ImmutableMultiDict


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.path in IGNORE_PATHS or "swagger" in request.path:
            return f(*args, **kwargs)
        try:
            # To validate external users token
            ext_auth = request.headers.get("X-External-Auth", None)
            if ext_auth == "jwt":
                decoded_token = ExternalAuth.decode_token()

                if not decoded_token:
                    # raise Exception("Invalid Token")
                    return {"status": "fail", "message": "Invalid Token"}, 401

                g.auth_user = {"principal_email": decoded_token["email"]}
                request.args = ImmutableMultiDict(
                    {
                        **dict(request.args),
                        "user_role": UserRole.ESG_EXTERNAL_CONTRIBUTOR.value,
                    }
                )
                return f(*args, **kwargs)

            # Decode token and store it in the request object
            g.decoded_token = AzureADAuth.decode_token()

            # Retrieve logged-in user data
            data, status = AuthHelper.get_logged_in_user()

            if status != 200:
                g.decoded_token = None
                return data, status

            # Check if X-Required-Roles header exists and authorize based on roles
            required_roles = request.headers.get("X-Required-Roles", None)
            if required_roles:
                required_roles = required_roles.split(",")

                # Ensure required_roles is not an empty list
                if required_roles:
                    user_role = data["role"]
                    if not user_role:
                        return {
                            "status": "fail",
                            "message": "User role not found.",
                        }, 403

                    if user_role not in required_roles:
                        return {"status": "fail", "message": "Access denied."}, 403

        except Exception as e:
            return {"status": "fail", "message": str(e)}, 401

        return f(*args, **kwargs)

    return decorated_function
