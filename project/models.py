from database import (
    db,
)  # Make sure this import is correctly referencing your initialized SQLAlchemy instance


class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(db.Integer, primary_key=True)
    coordinates = db.Column(db.JSON)
    distance = db.Column(db.Float)

    def __repr__(self):
        return f"<Route {self.id}>"
