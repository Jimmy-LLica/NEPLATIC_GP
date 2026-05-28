import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.usuario import Usuario
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("auth")


class AuthController:
    SECRET_KEY = "neplatic-desktop-secret-key"
    ALGORITHM = "HS256"
    TOKEN_EXPIRE_HOURS = 8

    def login(self, username: str, password: str) -> Usuario:
        db = self._get_db()
        try:
            user = db.query(Usuario).filter(Usuario.username == username, Usuario.activo == True).first()
            if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                user.ultimo_acceso = datetime.now()
                user.intentos_fallidos = 0
                db.commit()
                token = self._generate_token(user.id_usuario)
                logger.info(f"Login exitoso: {username}")
                return user
            if user:
                user.intentos_fallidos += 1
                db.commit()
                logger.warning(f"Login fallido: {username}")
            return None
        finally:
            db.close()

    def _generate_token(self, user_id: int) -> str:
        expire = datetime.now() + timedelta(hours=self.TOKEN_EXPIRE_HOURS)
        return jwt.encode({"sub": user_id, "exp": expire}, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def _get_db(self):
        from src.models.database import SessionLocal
        return SessionLocal()

    def verify_token(self, token: str) -> Usuario:
        db = self._get_db()
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return db.query(Usuario).filter(Usuario.id_usuario == payload["sub"]).first()
        except jwt.PyJWTError:
            return None
        finally:
            db.close()