import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
    )
    key = kdf.derive(master_password.encode())
    return base64.urlsafe_b64encode(key)

def generate_salt() -> bytes:
    return os.urandom(32)

def hash_master_password(password: str) -> str:
    return ph.hash(password)

def verify_master_password(stored_hash: str, password: str) -> bool:
    try:
        ph.verify(stored_hash, password)
        return True
    except VerifyMismatchError:
        return False

def encrypt_data(data: str, key: bytes) -> str:
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted: str, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted.encode()).decode()

def generate_password(length=16, use_upper=True, use_digits=True,
                       use_special=True, exclude_similar=False):
    import random
    import string
    
    chars = string.ascii_lowercase
    if use_upper:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    if use_special:
        chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    if exclude_similar:
        for c in 'il1Lo0O':
            chars = chars.replace(c, '')
    
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def check_password_strength(password: str) -> dict:
    score = 0
    issues = []
    
    if len(password) >= 8:
        score += 1
    else:
        issues.append("Too short (min 8 chars)")
    
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    if any(c.isupper() for c in password):
        score += 1
    else:
        issues.append("No uppercase letters")
    
    if any(c.islower() for c in password):
        score += 1
    else:
        issues.append("No lowercase letters")
    
    if any(c.isdigit() for c in password):
        score += 1
    else:
        issues.append("No digits")
    
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        score += 2
    else:
        issues.append("No special characters")
    
    if score <= 3:
        strength = "weak"
    elif score <= 5:
        strength = "fair"
    elif score <= 7:
        strength = "good"
    else:
        strength = "strong"
    
    return {
        "score": score,
        "strength": strength,
        "issues": issues,
        "percentage": min(100, int(score / 8 * 100))
    }
