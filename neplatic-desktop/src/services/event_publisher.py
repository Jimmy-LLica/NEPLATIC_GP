import json
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.database import SessionLocal
from src.models.deuda import OutboxEvento
from src.utils.logger import setup_logger

logger = setup_logger("events")


class EventPublisher:
    def __init__(self):
        self.db = SessionLocal()

    def publish(self, aggregate_type: str, aggregate_id: str, event_type: str, payload: dict):
        evento = OutboxEvento(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=json.dumps(payload)
        )
        self.db.add(evento)
        self.db.commit()
        logger.info(f"Evento publicado: {event_type} para {aggregate_type}/{aggregate_id}")
        return evento

    def get_pending_events(self, limit: int = 100):
        return self.db.query(OutboxEvento).filter(OutboxEvento.publicado == False).limit(limit).all()

    def mark_as_published(self, event_id: int):
        evento = self.db.query(OutboxEvento).filter(OutboxEvento.id_outbox == event_id).first()
        if evento:
            evento.publicado = True
            evento.fecha_publicacion = datetime.now()
            self.db.commit()
        return evento

    def close(self):
        self.db.close()