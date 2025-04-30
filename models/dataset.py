from datetime import datetime
from . import db

class Dataset(db.Model):
    __tablename__ = 'datasets'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.LargeBinary, nullable=True)
    
    # Tambahkan relationship dengan cascade delete
    cryptocurrencies = db.relationship('Cryptocurrency', 
                                      backref='dataset',
                                      cascade='all, delete-orphan',
                                      lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'crypto_count': len(self.cryptocurrencies) if self.cryptocurrencies else 0
        }