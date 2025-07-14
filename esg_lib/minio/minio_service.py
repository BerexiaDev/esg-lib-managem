import io
from flask import current_app as app, send_file

from esg_lib.minio.minio_client import MinioClient

def upload_file_minio(full_path, file_buffer):
    try:
        MinioClient.get_instance().put_object(
            app.config['MINIO_BUCKET_NAME'],
            full_path,
            io.BytesIO(file_buffer),
            len(file_buffer)
        )
    except Exception as e:
        raise Exception(str(e))


def download_file_minio(full_path, filename):
    file = MinioClient.get_instance().get_object(app.config['MINIO_BUCKET_NAME'], full_path)
    return send_file(file, mimetype="application/octet-stream", as_attachment=True, attachment_filename=filename)


def remove_file_minio(full_path):
    MinioClient.get_instance().remove_object(app.config['MINIO_BUCKET_NAME'], full_path)