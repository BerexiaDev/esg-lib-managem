from minio import Minio
from flask import current_app

class MinioClient:
    _client_instance = None

    @classmethod
    def get_instance(cls):
        if cls._client_instance is None:
            config = current_app.config
            cls._client_instance = Minio(
                config["MINIO_ENDPOINT"],
                access_key=config["MINIO_ACCESS_KEY"],
                secret_key=config["MINIO_SECRET_KEY"],
                secure=True,
                region=config['MINIO_REGION']
                )
        return cls._client_instance
