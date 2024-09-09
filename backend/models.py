from database import db

class RainfallData(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	time = db.Column(db.DateTime, nullable=False)
	RG_A = db.Column(db.Float, nullable=False)

	def __init__(self, time, RG_A):
		self.time = time
		self.RG_A = RG_A

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}