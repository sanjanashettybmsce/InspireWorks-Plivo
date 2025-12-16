from datetime import datetime

# Store active call sessions
# Format: {call_uuid: {'customer_phone': str, 'language': str, 'agent_id': int, 'start_time': datetime}}
active_calls = {}

def create_call_session(call_uuid, customer_phone):
    """Create a new call session"""
    active_calls[call_uuid] = {
        'customer_phone': customer_phone,
        'language': None,
        'agent_id': None,
        'start_time': datetime.utcnow()
    }

def update_call_language(call_uuid, language):
    """Update the language selected in IVR"""
    if call_uuid in active_calls:
        active_calls[call_uuid]['language'] = language

def update_call_agent(call_uuid, agent_id):
    """Update the agent assigned to the call"""
    if call_uuid in active_calls:
        active_calls[call_uuid]['agent_id'] = agent_id

def get_call_session(call_uuid):
    """Get call session data"""
    return active_calls.get(call_uuid)

def end_call_session(call_uuid):
    """End and remove call session"""
    if call_uuid in active_calls:
        session = active_calls[call_uuid]
        duration = (datetime.utcnow() - session['start_time']).total_seconds()
        del active_calls[call_uuid]
        return session, duration
    return None, 0
