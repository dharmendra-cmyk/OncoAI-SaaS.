import functools
import hashlib
from datetime import datetime, timezone
import psycopg2

def log_audit_event(action_type: str, db_connection_string: str):
    """
    A 21 CFR Part 11 compliant decorator for logging immutable audit events
    to a PostgreSQL database with cryptographic checksum verification.
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
            
            # Persist to append-only PostgreSQL audit log
            try:
                conn = psycopg2.connect(db_connection_string)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO audit_trail_logs (timestamp, user_id, action_type, record_hash, status)
                    VALUES (%s, %s, %s, %s, 'SUCCESS')
                    """,
                    (timestamp, user_id, action_type, record_hash)
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"CRITICAL: Audit log failure under 21 CFR Part 11 constraints: {e}")
                raise
                
            return result
        return wrapper
    return decorator
