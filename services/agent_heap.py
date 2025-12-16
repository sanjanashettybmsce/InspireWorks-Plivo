import heapq
from threading import Lock
from datetime import datetime, timedelta
from models import Agent, db

class AgentHeapManager:
    """
    Manages two separate heaps for English and Spanish agents.
    Uses priority scoring for intelligent load balancing.
    """
    
    def __init__(self):
        self.english_heap = []
        self.spanish_heap = []
        self.lock = Lock()
        
        # Track agents currently in calls
        self.busy_agents = {}  # {agent_id: call_uuid}
    
    def initialize_heaps(self):
        """Initialize heaps with all available agents from database"""
        with self.lock:
            # Clear existing heaps
            self.english_heap = []
            self.spanish_heap = []
            
            # Get all agents
            agents = Agent.query.all()
            
            for agent in agents:
                if agent.is_available:
                    priority = agent.calculate_priority_score()
                    heap_entry = (priority, agent.id, agent.phone_number)
                    
                    if agent.language == 'english':
                        heapq.heappush(self.english_heap, heap_entry)
                    elif agent.language == 'spanish':
                        heapq.heappush(self.spanish_heap, heap_entry)
    
    def get_best_agent(self, language):
        """
        Get the best available agent for the specified language.
        Returns (agent_id, phone_number) or (None, None) if no agent available.
        """
        with self.lock:
            heap = self.english_heap if language == 'english' else self.spanish_heap
            
            # Find first available agent (not busy)
            while heap:
                priority, agent_id, phone_number = heapq.heappop(heap)
                
                # Check if agent is still available and not busy
                agent = Agent.query.get(agent_id)
                if agent and agent.is_available and agent_id not in self.busy_agents:
                    # Mark as busy
                    agent.is_available = False
                    db.session.commit()
                    
                    return agent_id, phone_number
            
            return None, None
    
    def mark_agent_busy(self, agent_id, call_uuid):
        """Mark an agent as busy with a specific call"""
        with self.lock:
            self.busy_agents[agent_id] = call_uuid
            
            agent = Agent.query.get(agent_id)
            if agent:
                agent.is_available = False
                db.session.commit()
    
    def release_agent(self, agent_id, call_duration):
        """
        Release agent after call completion and reinsert into heap.
        Updates agent metrics and recalculates priority.
        """
        with self.lock:
            # Remove from busy agents
            if agent_id in self.busy_agents:
                del self.busy_agents[agent_id]
            
            # Update agent metrics
            agent = Agent.query.get(agent_id)
            if agent:
                agent.update_metrics(call_duration)
                agent.is_available = True
                db.session.commit()
                
                # Reinsert into appropriate heap with new priority
                priority = agent.calculate_priority_score()
                heap_entry = (priority, agent.id, agent.phone_number)
                
                if agent.language == 'english':
                    heapq.heappush(self.english_heap, heap_entry)
                elif agent.language == 'spanish':
                    heapq.heappush(self.spanish_heap, heap_entry)
    
    def update_agent_feedback(self, agent_id, rating):
        """Update agent feedback score and recalculate priority"""
        agent = Agent.query.get(agent_id)
        if agent:
            agent.total_feedback_score += rating
            agent.feedback_count += 1
            db.session.commit()
    
    def reset_recent_call_counts(self):
        """Reset recent call counts (should be run hourly)"""
        with self.lock:
            agents = Agent.query.all()
            for agent in agents:
                agent.recent_call_count = 0
            db.session.commit()
            
            # Rebuild heaps with new priorities
            self.initialize_heaps()
    
    def get_agent_stats(self):
        """Get current stats for all agents (for dashboard)"""
        english_agents = []
        spanish_agents = []
        
        agents = Agent.query.all()
        for agent in agents:
            avg_rating = 0
            if agent.feedback_count > 0:
                avg_rating = round(agent.total_feedback_score / agent.feedback_count, 2)
            
            agent_info = {
                'id': agent.id,
                'phone': agent.phone_number,
                'language': agent.language,
                'available': agent.is_available,
                'total_calls': agent.total_calls,
                'avg_duration': round(agent.avg_call_duration, 2),
                'avg_rating': avg_rating,
                'priority': round(agent.calculate_priority_score(), 2)
            }
            
            if agent.language == 'english':
                english_agents.append(agent_info)
            elif agent.language == 'spanish':
                spanish_agents.append(agent_info)
        
        return {
            'english': english_agents,
            'spanish': spanish_agents
        }


# Global instance
agent_heap_manager = AgentHeapManager()
