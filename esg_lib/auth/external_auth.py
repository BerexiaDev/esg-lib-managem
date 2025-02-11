import jwt

from flask import request
from flask import current_app as app, has_app_context

class ExternalAuth:
    _instance = None
    secret_key = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExternalAuth, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def _initialize(cls):
        if not has_app_context():
            raise RuntimeError("Application context required for ExternalAuth initialization")

        if cls._instance.secret_key is None:
            cls._instance.secret_key = app.config['SECRET_KEY']

    @classmethod
    def create_instance(cls):
        instance = cls.__new__(cls)
        instance._initialize()
    
    def get_token_auth_header(self):
        auth = request.headers.get("Authorization", None)
        if not auth:
            raise Exception("Authorization header is expected")

        parts = auth.split()

        if parts[0].lower() != "bearer":
            raise Exception("Authorization header must start with Bearer")

        elif len(parts) == 1:
            raise Exception("Token not found")

        elif len(parts) > 2:
            raise Exception("Authorization header must be Bearer token")

        token = parts[1]
        return token

    @classmethod
    def decode_token(cls):
        cls.create_instance()

        token = cls._instance.get_token_auth_header()
        try:
            decoded_token = jwt.decode(token, cls._instance.secret_key, algorithms=['HS256'])
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise Exception(f"Unable to parse token: {str(e)}")
