from datetime import date
from sqlalchemy.orm import Session
from src.models.usuario import Usuario
from src.models.deuda import RutaNotificacion, RutaDetalle, Notificacion
from src.models.database import SessionLocal
from src.utils.logger import setup_logger

logger = setup_logger("ruta")


class RutaController:
    def __init__(self, user: Usuario):
        self.user = user
        self.db = SessionLocal()

    def listar_rutas_usuario(self):
        return self.db.query(RutaNotificacion).filter(
            RutaNotificacion.id_usuario == self.user.id_usuario,
            RutaNotificacion.fecha_ruta >= date.today()
        ).order_by(RutaNotificacion.fecha_ruta.desc()).all()

    def listar_deudas_asignadas(self):
        from src.models.contribuyente import Lote
        query = self.db.query(
            RutaDetalle.id_deuda,
            Lote.codigo.label("codigo_lote"),
            RutaDetalle.orden_visita,
            RutaDetalle.visitado
        ).join(RutaNotificacion).join(Lote, RutaDetalle.id_deuda == Lote.id_lote).filter(
            RutaNotificacion.id_usuario == self.user.id_usuario,
            RutaNotificacion.activa == True
        )
        return query.all()

    def registrar_notificacion(self, id_deuda: int, direccion: str, persona: str, parentesco: str, id_estado: int):
        notif = Notificacion(
            id_deuda=id_deuda,
            id_usuario=self.user.id_usuario,
            id_estado_notif=id_estado,
            direccion_visitada=direccion,
            persona_contactada=persona,
            parentesco=parentesco
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        logger.info(f"Notificacion registrada: deuda {id_deuda}, estado {id_estado}")
        return notif

    def close(self):
        self.db.close()