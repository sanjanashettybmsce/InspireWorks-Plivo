from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    language = db.Column(db.String(10), nullable=False)  # 'english' or 'spanish'
    is_available = db.Column(db.Boolean, default=True)
    total_calls = db.Column(db.Integer, default=0)
    avg_call_duration = db.Column(db.Float, default=0.0)  # in seconds
    recent_call_count = db.Column(db.Integer, default=0)  # calls in last hour
    last_call_time = db.Column(db.DateTime)
    total_feedback_score = db.Column(db.Float, default=0.0)
    feedback_count = db.Column(db.Integer, default=0)
    
    # Relationships
    call_logs = db.relationship('CallLog', backref='agent', lazy=True)
    feedbacks = db.relationship('Feedback', backref='agent', lazy=True)
    
    def __repr__(self):
        return f'<Agent {self.phone_number} - {self.language}>'
    
    def calculate_priority_score(self):
        """
        Calculate priority score for heap-based routing.
        Lower score = higher priority
        """
        score = 0
        
        # Availability (most important)
        if not self.is_available:
            return float('inf')  # Not available = lowest priority
        
        # Recent call count penalty (avoid overloading)
        score += self.recent_call_count * 10
        
        # Average call duration (prefer faster agents)
        score += self.avg_call_duration / 60  # convert to minutes
        
        # Feedback score bonus (better feedback = lower score)
        if self.feedback_count > 0:
            avg_rating = self.total_feedback_score / self.feedback_count
            score -= avg_rating * 5  # reward good ratings
        
        return score
    
    def update_metrics(self, call_duration):
        """Update agent metrics after call completion"""
        # Update average call duration
        total_duration = self.avg_call_duration * self.total_calls
        self.total_calls += 1
        self.avg_call_duration = (total_duration + call_duration) / self.total_calls
        
        # Update recent call count
        self.recent_call_count += 1
        self.last_call_time = datetime.utcnow()


class Customer(db.Model):
    __tablename__ = 'customers'
    
    phone_number = db.Column(db.String(20), primary_key=True)
    total_calls = db.Column(db.Integer, default=0)
    last_call_time = db.Column(db.DateTime)
    avg_call_duration = db.Column(db.Float, default=0.0)  # in seconds
    last_agent_connected = db.Column(db.String(20))
    last_feedback_rating = db.Column(db.Integer)
    preferred_language = db.Column(db.String(10))
    
    # Relationships
    call_logs = db.relationship('CallLog', backref='customer', lazy=True)
    feedbacks = db.relationship('Feedback', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.phone_number}>'
    
    def update_metrics(self, call_duration):
        """Update customer metrics after call completion"""
        total_duration = self.avg_call_duration * self.total_calls
        self.total_calls += 1
        self.avg_call_duration = (total_duration + call_duration) / self.total_calls
        self.last_call_time = datetime.utcnow()


class CallLog(db.Model):
    __tablename__ = 'call_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    call_uuid = db.Column(db.String(100), unique=True, nullable=False)
    customer_phone = db.Column(db.String(20), db.ForeignKey('customers.phone_number'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'))
    language_selected = db.Column(db.String(10))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # in seconds
    status = db.Column(db.String(20))  # 'completed', 'failed', 'no-answer', etc.
    
    def __repr__(self):
        return f'<CallLog {self.call_uuid}>'


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    
    id = db.Column(db.Integer, primary_key=True)
    call_log_id = db.Column(db.Integer, db.ForeignKey('call_logs.id'), nullable=False)
    customer_phone = db.Column(db.String(20), db.ForeignKey('customers.phone_number'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1=Poor, 2=Fair, 3=Good, 4=Excellent
    call_duration = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    call_log = db.relationship('CallLog', backref='feedback', uselist=False)
    
    def __repr__(self):
        return f'<Feedback {self.rating} for Agent {self.agent_id}>'
