from passlib.context import CryptContext

pass_content = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pass_content.hash(password)

def verify_password(plain_pass: str, hashed_pass: str) -> bool:
    tuuu = pass_content.verify(plain_pass, hashed_pass)
    return tuuu
