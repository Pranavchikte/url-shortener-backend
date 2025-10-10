import random
import string
from sqlalchemy.orm import Session

from . import crud

def create_unique_short_code(db: Session) -> str:
    chars = string.ascii_letters + string.digits
    
    for _ in range(5):
        short_code = "".join(random.choices(chars, k=6))
        if not crud.get_db_url_by_short_code(db, short_code):
            return short_code
        
    raise Exception("Could not generate a unique short code")