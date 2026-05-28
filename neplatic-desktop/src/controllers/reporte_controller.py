from sqlalchemy import text
from src.models.database import SessionLocal
from src.utils.logger import setup_logger

logger = setup_logger("reportes")


class ReporteController:
    def __init__(self):
        self.db = SessionLocal()

    def dashboard_gerencial(self) -> dict:
        result = self.db.execute(text("SELECT * FROM neplatic.v_dashboard_gerencial")).first()
        if result:
            return dict(result._mapping)
        return {}

    def morosidad_por_sector(self):
        return self.db.execute(text("SELECT * FROM neplatic.v_morosidad_sector")).fetchall()

    def morosidad_por_manzana(self, id_sector: int = None):
        query = "SELECT * FROM neplatic.v_morosidad_manzana"
        if id_sector:
            query += f" WHERE codigo_sector = (SELECT codigo FROM neplatic.sector WHERE id_sector = {id_sector})"
        return self.db.execute(text(query)).fetchall()

    def top_deudores(self, limit: int = 10):
        return self.db.execute(text(f"SELECT * FROM neplatic.v_top_deudores LIMIT {limit}")).fetchall()

    def evolucion_mensual(self):
        return self.db.execute(text("SELECT * FROM neplatic.v_evolucion_morosidad")).fetchall()

    def close(self):
        self.db.close()