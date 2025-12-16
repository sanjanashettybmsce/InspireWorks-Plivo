import plivo
from flask import Flask, request, jsonify, render_template, url_for
from flask_socketio import SocketIO, emit
from datetime import datetime
import os

from config import Config
from models import db, Agent, Customer, CallLog, Feedback
from services.agent_heap import agent_heap_manager
from services.call_manager import (
    create_call_session, update_call_language, update_call_agent,
    get_call_session, end_call_session
)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Plivo client
plivo_client = None
if app.config['PLIVO_AUTH_ID'] and app.config['PLIVO_AUTH_TOKEN']:
    plivo_client = plivo.RestClient(
        auth_id=app.config['PLIVO_AUTH_ID'],
        auth_token=app.config['PLIVO_AUTH_TOKEN']
    )


def get_base_url():
    """Get base URL for callbacks (use ngrok URL in production)"""
    # Replace with your actual ngrok URL when testing
    # Example: return "https://abc123.ngrok.io"
    ngrok_url = "https://scholarly-introspective-irene.ngrok-free.dev"
    return ngrok_url


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize database and create sample agents"""
    with app.app_context():
        db.create_all()
        
        # Check if agents already exist
        if Agent.query.count() == 0:
            # Create English agent
            english_agent = Agent(
                phone_number=app.config['ENGLISH_AGENT_NUMBER'],
                language='english',
                is_available=True
            )
            
            # Create Spanish agent
            spanish_agent = Agent(
                phone_number=app.config['SPANISH_AGENT_NUMBER'],
                language='spanish',
                is_available=True
            )
            
            db.session.add(english_agent)
            db.session.add(spanish_agent)
            db.session.commit()
            
            print("✅ Sample agents created")
        
        # Initialize agent heaps
        agent_heap_manager.initialize_heaps()
        print("✅ Agent heaps initialized")


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Render main dashboard"""
    return render_template('index.html')


@app.route('/call', methods=['POST'])
def initiate_call():
    """Initiate outbound call using Plivo API"""
    data = request.json
    to_number = data.get('to_number')
    
    if not to_number:
        return jsonify({'error': 'Phone number required'}), 400
    
    if not plivo_client:
        return jsonify({'error': 'Plivo credentials not configured'}), 500
    
    try:
        base_url = get_base_url()
        
        # Make call using Plivo
        response = plivo_client.calls.create(
            from_=app.config['PLIVO_FROM_NUMBER'],
            to_=to_number,
            answer_url=f'{base_url}/ivr/start',
            answer_method='GET'
        )
        
        return jsonify({
            'success': True,
            'call_uuid': response.request_uuid,
            'message': f'Call initiated to {to_number}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ivr/start', methods=['GET', 'POST'])
def ivr_start():
    """Level 1 IVR - Language Selection"""
    call_uuid = request.values.get('CallUUID')
    from_number = request.values.get('From')
    
    # Check if call already exists (Plivo may retry this endpoint)
    existing_call = CallLog.query.filter_by(call_uuid=call_uuid).first()
    if not existing_call:
        # Create call session
        create_call_session(call_uuid, from_number)
        
        # Create or get customer
        customer = Customer.query.get(from_number)
        if not customer:
            customer = Customer(phone_number=from_number)
            db.session.add(customer)
            db.session.commit()
        
        # Create call log
        call_log = CallLog(
            call_uuid=call_uuid,
            customer_phone=from_number,
            status='in-progress'
        )
        db.session.add(call_log)
        db.session.commit()
    
    base_url = get_base_url()
    
    # Generate Plivo XML
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Welcome to our IVR system.</Speak>
    <GetDigits action="{base_url}/ivr/language" method="POST" numDigits="1" timeout="10" retries="2">
        <Speak>Press 1 for English. Press 2 for Spanish.</Speak>
    </GetDigits>
    <Speak>We did not receive your input. Goodbye.</Speak>
    <Hangup/>
</Response>'''
    
    return xml_response, 200, {'Content-Type': 'text/xml'}


@app.route('/ivr/language', methods=['POST'])
def ivr_language():
    """Process language selection"""
    call_uuid = request.values.get('CallUUID')
    digit = request.values.get('Digits')
    
    base_url = get_base_url()
    
    # Map digit to language
    language_map = {'1': 'english', '2': 'spanish'}
    language = language_map.get(digit)
    
    if not language:
        # Invalid input
        xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Invalid selection.</Speak>
    <Redirect>{base_url}/ivr/start</Redirect>
</Response>'''
        return xml_response, 200, {'Content-Type': 'text/xml'}
    
    # Update call session
    update_call_language(call_uuid, language)
    
    # Update call log
    call_log = CallLog.query.filter_by(call_uuid=call_uuid).first()
    if call_log:
        call_log.language_selected = language
        db.session.commit()
    
    # Redirect to menu
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect>{base_url}/ivr/menu</Redirect>
</Response>'''
    
    return xml_response, 200, {'Content-Type': 'text/xml'}


@app.route('/ivr/menu', methods=['GET', 'POST'])
def ivr_menu():
    """Level 2 IVR - Action Menu (language-specific)"""
    call_uuid = request.values.get('CallUUID')
    session = get_call_session(call_uuid)
    
    if not session or not session['language']:
        # Fallback to start
        base_url = get_base_url()
        xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect>{base_url}/ivr/start</Redirect>
</Response>'''
        return xml_response, 200, {'Content-Type': 'text/xml'}
    
    language = session['language']
    base_url = get_base_url()
    
    # Language-specific prompts
    if language == 'english':
        prompt = "Press 1 to play a message. Press 2 to connect to a live agent."
    else:
        prompt = "Presione 1 para reproducir un mensaje. Presione 2 para conectarse con un agente en vivo."
    
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits action="{base_url}/ivr/action" method="POST" numDigits="1" timeout="10" retries="2">
        <Speak>{prompt}</Speak>
    </GetDigits>
    <Speak>No input received. Goodbye.</Speak>
    <Hangup/>
</Response>'''
    
    return xml_response, 200, {'Content-Type': 'text/xml'}


@app.route('/ivr/action', methods=['POST'])
def ivr_action():
    """Process menu action"""
    call_uuid = request.values.get('CallUUID')
    digit = request.values.get('Digits')
    session = get_call_session(call_uuid)
    
    if not session:
        xml_response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Session error. Goodbye.</Speak>
    <Hangup/>
</Response>'''
        return xml_response, 200, {'Content-Type': 'text/xml'}
    
    language = session['language']
    base_url = get_base_url()
    
    if digit == '1':
        # Play audio message
        if language == 'english':
            message = "Thank you for calling. This is a demo message. You will now be disconnected."
        else:
            message = "Gracias por llamar. Este es un mensaje de demostración. Ahora se desconectará."
        
        xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>{message}</Speak>
    <Hangup/>
</Response>'''
        
        return xml_response, 200, {'Content-Type': 'text/xml'}
    
    elif digit == '2':
        # Connect to agent
        agent_id, agent_phone = agent_heap_manager.get_best_agent(language)
        
        if not agent_id:
            # No agent available
            if language == 'english':
                message = "Sorry, all agents are currently busy. Please try again later."
            else:
                message = "Lo sentimos, todos los agentes están ocupados. Por favor, inténtelo más tarde."
            
            xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>{message}</Speak>
    <Hangup/>
</Response>'''
            
            return xml_response, 200, {'Content-Type': 'text/xml'}
        
        # Mark agent as busy
        agent_heap_manager.mark_agent_busy(agent_id, call_uuid)
        update_call_agent(call_uuid, agent_id)
        
        # Update call log
        call_log = CallLog.query.filter_by(call_uuid=call_uuid).first()
        if call_log:
            call_log.agent_id = agent_id
            db.session.commit()
        
        # Emit real-time update
        socketio.emit('agent_status_update', agent_heap_manager.get_agent_stats())
        
        # For demo: Simulate agent connection with hold music, then feedback
        # In production, replace with real Dial to agent_phone
        if language == 'english':
            agent_msg = "You have been connected to an agent. Thank you for calling."
        else:
            agent_msg = "Ha sido conectado con un agente. Gracias por llamar."
        
        xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Connecting you to an agent. Please hold.</Speak>
    <Wait length="2"/>
    <Speak>{agent_msg}</Speak>
    <Redirect>{base_url}/ivr/feedback</Redirect>
</Response>'''
        
        return xml_response, 200, {'Content-Type': 'text/xml'}
    
    else:
        # Invalid input
        xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Invalid selection.</Speak>
    <Redirect>{base_url}/ivr/menu</Redirect>
</Response>'''
        
        return xml_response, 200, {'Content-Type': 'text/xml'}


@app.route('/ivr/feedback', methods=['GET', 'POST'])
def ivr_feedback():
    """Level 3 IVR - Collect Feedback after simulated agent call"""
    call_uuid = request.values.get('CallUUID')
    dial_status = request.values.get('DialStatus')
    session = get_call_session(call_uuid)
    
    # For simulated calls, dial_status will be None, so treat as success
    dial_status = dial_status or 'completed'
    
    language = 'english'
    if session:
        language = session.get('language', 'english')
    
    base_url = get_base_url()
    
    # If agent call failed (only for real Dial operations)
    if dial_status != 'completed' and session and session.get('agent_id'):
        # Release agent since call failed
        agent_heap_manager.release_agent(session['agent_id'], 0)
        socketio.emit('agent_status_update', agent_heap_manager.get_agent_stats())
        
        if language == 'english':
            prompt = "The agent connection failed. Thank you for calling. Goodbye."
        else:
            prompt = "La conexión del agente falló. Gracias por llamar. Adiós."
        
        xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>{prompt}</Speak>
    <Hangup/>
</Response>'''
        
        return xml_response, 200, {'Content-Type': 'text/xml'}
    
    # Agent call was successful - collect feedback
    if language == 'english':
        prompt = "Please rate your experience. Press 1 for Poor, 2 for Fair, 3 for Good, or 4 for Excellent."
    else:
        prompt = "Por favor califique su experiencia. Presione 1 para Pobre, 2 para Regular, 3 para Bueno o 4 para Excelente."
    
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <GetDigits action="{base_url}/plivo/callback" method="POST" numDigits="1" timeout="10" retries="1">
        <Speak>{prompt}</Speak>
    </GetDigits>
    <Speak>Thank you. Goodbye.</Speak>
    <Hangup/>
</Response>'''
    
    return xml_response, 200, {'Content-Type': 'text/xml'}


@app.route('/plivo/callback', methods=['POST'])
def plivo_callback():
    """Handle call completion and feedback"""
    call_uuid = request.values.get('CallUUID')
    feedback_digit = request.values.get('Digits')
    
    session, duration = end_call_session(call_uuid)
    
    if session:
        customer_phone = session['customer_phone']
        agent_id = session['agent_id']
        
        # Update call log
        call_log = CallLog.query.filter_by(call_uuid=call_uuid).first()
        if call_log:
            call_log.end_time = datetime.utcnow()
            call_log.duration = duration
            call_log.status = 'completed'
            db.session.commit()
        
        # Update customer
        customer = Customer.query.get(customer_phone)
        if customer:
            customer.update_metrics(duration)
            if agent_id:
                customer.last_agent_connected = Agent.query.get(agent_id).phone_number
            db.session.commit()
        
        # Process feedback
        if feedback_digit and feedback_digit in ['1', '2', '3', '4']:
            rating = int(feedback_digit)
            
            # Save feedback
            if call_log and agent_id:
                feedback = Feedback(
                    call_log_id=call_log.id,
                    customer_phone=customer_phone,
                    agent_id=agent_id,
                    rating=rating,
                    call_duration=duration
                )
                db.session.add(feedback)
                
                # Update customer
                if customer:
                    customer.last_feedback_rating = rating
                
                db.session.commit()
                
                # Update agent feedback score
                agent_heap_manager.update_agent_feedback(agent_id, rating)
        
        # Release agent
        if agent_id:
            agent_heap_manager.release_agent(agent_id, duration)
            
            # Emit real-time update
            socketio.emit('agent_status_update', agent_heap_manager.get_agent_stats())
    
    xml_response = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak>Thank you for your feedback. Goodbye.</Speak>
    <Hangup/>
</Response>'''
    
    return xml_response, 200, {'Content-Type': 'text/xml'}


# ==================== API ENDPOINTS ====================

@app.route('/api/agent-stats', methods=['GET'])
def get_agent_stats():
    """Get current agent statistics"""
    stats = agent_heap_manager.get_agent_stats()
    return jsonify(stats)


@app.route('/api/reset-agents', methods=['POST'])
def reset_agents():
    """Reset all agents to available state (for testing)"""
    try:
        agents = Agent.query.all()
        for agent in agents:
            agent.is_available = True
        db.session.commit()
        
        # Reinitialize heaps
        agent_heap_manager.initialize_heaps()
        
        # Emit update
        socketio.emit('agent_status_update', agent_heap_manager.get_agent_stats())
        
        return jsonify({'success': True, 'message': 'All agents reset to available'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/call-history', methods=['GET'])
def get_call_history():
    """Get recent call history"""
    calls = CallLog.query.order_by(CallLog.start_time.desc()).limit(50).all()
    
    history = []
    for call in calls:
        history.append({
            'call_uuid': call.call_uuid,
            'customer': call.customer_phone,
            'agent_id': call.agent_id,
            'language': call.language_selected,
            'duration': call.duration,
            'status': call.status,
            'start_time': call.start_time.isoformat() if call.start_time else None
        })
    
    return jsonify(history)


# ==================== SOCKETIO EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    # Send initial agent stats
    emit('agent_status_update', agent_heap_manager.get_agent_stats())


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


# ==================== MAIN ====================

if __name__ == '__main__':
    init_db()
    print("🚀 Server starting...")
    print(f"📞 Plivo From Number: {app.config['PLIVO_FROM_NUMBER']}")
    print(f"👥 English Agent: {app.config['ENGLISH_AGENT_NUMBER']}")
    print(f"👥 Spanish Agent: {app.config['SPANISH_AGENT_NUMBER']}")
    
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)
