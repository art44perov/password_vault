from flask import session
from datetime import datetime, timedelta
import time

SESSION_KEY = 'vault_key'
SESSION_TIME = 'vault_time'
SESSION_TIMEOUT = 'vault_timeout'

def set_session_key(key: bytes, timeout_minutes: int = 15):
    import base64
    session[SESSION_KEY] = base64.b64encode(key).decode()
    session[SESSION_TIME] = time.time()
    session[SESSION_TIMEOUT] = timeout_minutes
    session.permanent = True

def get_session_key() -> bytes | None:
    import base64
    if SESSION_KEY not in session:
        return None
    
    last_time = session.get(SESSION_TIME, 0)
    timeout = session.get(SESSION_TIMEOUT, 15)
    
    if time.time() - last_time > timeout * 60:
        clear_session()
        return None
    
    session[SESSION_TIME] = time.time()
    return base64.b64decode(session[SESSION_KEY].encode())

def clear_session():
    session.pop(SESSION_KEY, None)
    session.pop(SESSION_TIME, None)
    session.pop(SESSION_TIMEOUT, None)

def is_authenticated() -> bool:
    return get_session_key() is not None
