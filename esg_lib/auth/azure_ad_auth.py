import base64
import traceback
import requests
import jwt

from flask import request
from flask import current_app as app, has_app_context
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

class AzureADAuth:
    _instance = None
    client_id = None
    authority = None
    jwks_uri = None
    keys = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureADAuth, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def _initialize(cls):
        if not has_app_context():
            raise RuntimeError("Application context required for AzureADAuth initialization")

        if cls._instance.client_id is None or cls._instance.authority is None:
            cls._instance.client_id = app.config['AZURE_CLIENT_ID']
            cls._instance.authority = app.config['AZURE_AUTHORITY']
            cls._instance.jwks_uri = f"{app.config['AZURE_AUTHORITY']}/discovery/v2.0/keys"
            cls._instance.keys = cls._instance.fetch_public_keys()

    @classmethod
    def create_instance(cls):
        instance = cls.__new__(cls)
        instance._initialize()
    
    def fetch_public_keys(self):
        try:
            response = requests.get(self.jwks_uri)
            if response.status_code != 200:
                raise Exception("Failed to fetch public keys")
            
            return response.json()["keys"]
        except requests.exceptions.RequestException as e:
            traceback.print_exc()
            return None
        except Exception as e:
            traceback.print_exc()
            return None

    def construct_rsa_pem(self, key):
        # Decode base64url encoded n and e components
        n_bytes = base64.urlsafe_b64decode(key["n"] + "==")
        e_bytes = base64.urlsafe_b64decode(key["e"] + "==")

        # Construct RSA key in PEM format
        n = int.from_bytes(n_bytes, byteorder="big")
        e = int.from_bytes(e_bytes, byteorder="big")
        rsa_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
        rsa_key_pem = rsa_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return rsa_key_pem
    
    @classmethod
    def get_rsa_key(cls, token):
        cls.create_instance()

        if not cls._instance.keys:
            raise Exception("RSA keys not available")
        
        headers = jwt.get_unverified_header(token)
        try:
            for key in cls._instance.keys:
                if key["kid"] == headers["kid"]:
                    rsa_key = cls._instance.construct_rsa_pem(key)
                    return rsa_key
            raise Exception("RSA key not found")

        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Failed to get RSA key: {str(e)}")

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
        rsa_key = cls._instance.get_rsa_key(token)
        try:
            decoded_token = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=cls._instance.client_id,  
                issuer=f"{cls._instance.authority}/v2.0"  
            )
            return decoded_token
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError as e:
            raise Exception(f"Invalid token: {str(e)}")
        except Exception as e:
            raise Exception(f"Unable to parse token: {str(e)}")
