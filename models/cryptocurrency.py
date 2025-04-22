from datetime import datetime
from . import db

class Cryptocurrency(db.Model):
    __tablename__ = 'cryptocurrencies'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(20, 8), nullable=False)
    price_change_24h = db.Column(db.Numeric(20, 8))
    percent_change_24h = db.Column(db.Numeric(10, 4))
    market_cap = db.Column(db.Numeric(30, 2))
    volume_24h = db.Column(db.Numeric(30, 2))
    circulating_supply = db.Column(db.Numeric(30, 2))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'price': self.price,
            'price_change_24h': self.price_change_24h,
            'percent_change_24h': self.percent_change_24h,
            'market_cap': self.market_cap,
            'volume_24h': self.volume_24h,
            'circulating_supply': self.circulating_supply,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
