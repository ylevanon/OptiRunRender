from project.database import db


class Route(db.Model):
    __tablename__ = "routes"

    id = db.Column(db.Integer, primary_key=True)
    coordinates = db.Column(db.JSON)
    distance = db.Column(db.Float)
    address = db.Column(db.String)  # Assuming address is a string

    def __repr__(self):
        return f"<Route {self.id}>"
