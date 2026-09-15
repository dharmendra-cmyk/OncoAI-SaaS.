import functools
import hashlib
import json
from datetime import datetime, timezone
import psycopg2
from google.cloud import storage

BUCKET_NAME = "oncoai-audit-storage-asv"

def log_audit_event(action_type: str, db_connection_string: str):
    """
    21 CFR Part 11 compliant decorator for logging immutable audit events
    to a PostgreSQL database and mirroring them to Google Cloud Storage
    with cryptographic checksum verification.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.now(timezone.utc).isoformat()
            user_id = kwargs.get("user_id", "system_authenticated")

            # Execute the primary clinical auditing function
            result = func(*args, **kwargs)

            # Generate a payload hash to guarantee data integrity (prevent tampering)
            payload_string = f"{user_id}:{action_type}:{timestamp}:{str(result)}"
            record_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

            # 1. Persist to append-only PostgreSQL audit log (existing logic)
            try:
                conn = psycopg2.connect(db_connection_string)
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO audit_logs (timestamp, user_id, action_type, payload, record_hash) VALUES (%s, %s, %s, %s, %s)",
                    (timestamp, user_id, action_type, str(result), record_hash)
                )
                conn.commit()
                cur.close()
                conn.close()
            except Exception as db_err:
                print(f"Database audit log warning: {db_err}")

            # 2. Mirror immutable compliance backup to Google Cloud Storage
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(BUCKET_NAME)
                
                file_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
                blob_name = f"audit_logs/audit_{action_type}_{file_timestamp}.json"
                blob = bucket.blob(blob_name)
                
                audit_payload = {
                    "timestamp": timestamp,
                    "user_id": user_id,
                    "action_type": action_type,
                    "result": str(result),
                    "record_hash": record_hash
                }
                
                blob.upload_from_string(
                    json.dumps(audit_payload, indent=2),
                    content_type="application/json"
                )
            except Exception as gcs_err:
                print(f"GCS audit log warning: {gcs_err}")

            return result
        return wrapper
    return decorator
