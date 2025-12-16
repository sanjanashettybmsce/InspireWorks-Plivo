# MultiLevel IVR System - Plivo


A complete **full-stack IVR (Interactive Voice Response) system** built with **Flask** and **Plivo Voice XML API**, featuring heap-based intelligent agent routing, multi-language support, real-time dashboards, and feedback-driven agent prioritization.

---

## Features

### Core IVR Functionality
- **Multi-level IVR flow** with language selection
- **Level 1:** Language selection (English/Spanish)
- **Level 2:** Action menu (Play audio / Connect to agent)
- **Level 3:** Post-call feedback collection (1-4 rating)
- Graceful handling of invalid inputs and timeouts

### Intelligent Agent Routing
- **Heap-based priority queue** for English and Spanish agents
- **Dynamic load balancing** based on:
  - Agent availability
  - Average call duration
  - Recent call count
  - Feedback scores
- **Agentic intelligence:** Feedback influences future routing decisions

### Real-Time Features
- **WebSocket-based live dashboard** (Flask-SocketIO)
- Real-time agent status updates
- Live call monitoring
- Dynamic call history

### Data Persistence
- **SQLAlchemy models** for:
  - Agents (with performance metrics)
  - Customers (call history & preferences)
  - Call logs
  - Feedback ratings
- Comprehensive analytics and reporting

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.x, Flask |
| **Database** | SQLAlchemy (SQLite) |
| **Real-time** | Flask-SocketIO |
| **Telephony** | Plivo Voice XML API |
| **Frontend** | HTML5, CSS3, JavaScript |
| **WebSockets** | Socket.IO |

---

## Project Structure

```
project-root/
│
├── app.py                      # Main Flask application
├── config.py                   # Configuration & environment variables
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
│
├── models/
│   └── __init__.py            # SQLAlchemy models (Agent, Customer, CallLog, Feedback)
│
├── services/
│   ├── agent_heap.py          # Heap-based agent routing logic
│   └── call_manager.py        # Call session management
│
├── templates/
│   └── index.html             # Dashboard HTML
│
├── static/
│   ├── style.css              # Dashboard styling
│   └── script.js              # Frontend JavaScript + Socket.IO
│
└── README.md                   # This file
```

---

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Plivo account with Voice API credentials
- ngrok (for exposing local server to Plivo webhooks)

### 2. Installation

```bash
# Clone or download the project
cd Plivo1

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your Plivo credentials:

```env
PLIVO_AUTH_ID=your_plivo_auth_id
PLIVO_AUTH_TOKEN=your_plivo_auth_token
PLIVO_FROM_NUMBER=14692463987
```

### 4. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 5. Expose with ngrok

In a separate terminal:

```bash
ngrok http 5000
```

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`) and update the `get_base_url()` function in `app.py`:

```python
def get_base_url():
    return "https://your-ngrok-url.ngrok.io"
```

Restart the Flask app.

### 6. Test the System

1. Open `http://localhost:5000` in your browser
2. Enter a test phone number (e.g., your mobile)
3. Click "Start Call"
4. Follow the IVR prompts:
   - Press **1** for English or **2** for Spanish
   - Press **1** to hear a message or **2** to connect to an agent
   - After agent call, rate your experience (1-4)

---

## IVR Flow Diagram

```
┌─────────────────────────────────────┐
│   Level 1: Language Selection       │
│   Press 1 → English                 │
│   Press 2 → Spanish                 │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Level 2: Action Menu              │
│   Press 1 → Play Audio Message      │
│   Press 2 → Connect to Live Agent   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Agent Routing (if option 2)       │
│   - Fetch best agent from heap      │
│   - Route based on language         │
│   - Update agent status (busy)      │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Level 3: Feedback Collection      │
│   Press 1 → Poor                    │
│   Press 2 → Fair                    │
│   Press 3 → Good                    │
│   Press 4 → Excellent               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│   Post-Call Processing              │
│   - Store feedback in database      │
│   - Update agent metrics            │
│   - Recalculate priority score      │
│   - Release agent to heap           │
└─────────────────────────────────────┘
```

---

## Heap-Based Agent Routing

### How It Works

The system maintains **two separate heaps** (priority queues):
- `english_agents_heap`
- `spanish_agents_heap`

Each agent has a **priority score** calculated dynamically:

```python
priority_score = (
    recent_call_count * 10 +
    avg_call_duration / 60 -
    (avg_rating * 5)
)
```

**Lower score = Higher priority**

### Priority Factors

| Factor | Impact | Purpose |
|--------|--------|---------|
| **Availability** | Unavailable = ∞ | Only route to available agents |
| **Recent Calls** | +10 per call | Prevent overloading |
| **Avg Duration** | +1 per minute | Prefer faster agents |
| **Feedback Score** | -5 per star | Reward highly-rated agents |

### Feedback → Intelligence Loop

1. **Customer rates agent** (1-4 stars)
2. **Feedback stored** in database
3. **Agent's total score updated**
4. **Priority recalculated**
5. **Agent repositioned in heap**
6. **Future calls routed differently**

This creates an **adaptive system** where:
- High-performing agents get more calls
- Overloaded agents get relief
- Poor performers get flagged for coaching

---

## Agentic Use of Feedback

### Immediate Impact
- Agents with **better ratings** get **lower priority scores**
- Lower scores = **higher priority** in the heap
- Result: **Top performers get more calls**

### Analytics & Insights

The system tracks:
- **Agent performance trends** over time
- **Customer satisfaction** by language
- **Call duration patterns**
- **Underperforming agents** (for coaching)

### Future Enhancements

The feedback data enables:
- **ML-based routing** (predictive agent selection)
- **QA dashboards** for supervisors
- **Automated coaching recommendations**
- **Alert system** for performance drops

---

## Database Models

### Agent
```python
- phone_number (unique)
- language (english/spanish)
- is_available (boolean)
- total_calls
- avg_call_duration
- recent_call_count
- total_feedback_score
- feedback_count
```

### Customer
```python
- phone_number (primary key)
- total_calls
- avg_call_duration
- last_agent_connected
- last_feedback_rating
- preferred_language
```

### CallLog
```python
- call_uuid
- customer_phone
- agent_id
- language_selected
- start_time / end_time
- duration
- status
```

### Feedback
```python
- call_log_id
- customer_phone
- agent_id
- rating (1-4)
- call_duration
- timestamp
```

---

## API Endpoints

### HTTP Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/call` | POST | Initiate outbound call |
| `/ivr/start` | GET | Level 1 IVR (language) |
| `/ivr/language` | POST | Process language selection |
| `/ivr/menu` | GET/POST | Level 2 IVR (action menu) |
| `/ivr/action` | POST | Process menu selection |
| `/ivr/feedback` | POST | Level 3 IVR (feedback) |
| `/plivo/callback` | POST | Call completion handler |
| `/api/agent-stats` | GET | Get agent statistics |
| `/api/call-history` | GET | Get recent calls |

### WebSocket Events

| Event | Direction | Data |
|-------|-----------|------|
| `connect` | Client → Server | Connection established |
| `disconnect` | Client → Server | Connection closed |
| `agent_status_update` | Server → Client | Real-time agent stats |

---

## Test Scenarios

### Scenario 1: English Agent Call
```
1. Call initiated
2. Press 1 (English)
3. Press 2 (Connect to agent)
4. Connected to: 14692463990
5. Call ends
6. Press 4 (Excellent)
7. Agent priority improved
```

### Scenario 2: Spanish Agent Call
```
1. Call initiated
2. Press 2 (Spanish)
3. Press 2 (Connect to agent)
4. Connected to: 918031274121
5. Call ends
6. Press 1 (Poor)
7. Agent priority decreased
```

### Scenario 3: Audio Message
```
1. Call initiated
2. Press 1 (English)
3. Press 1 (Play message)
4. Message plays
5. Call ends (no feedback)
```

---

## Troubleshooting

### Issue: Calls not connecting

**Solution:**
- Verify Plivo credentials in `.env`
- Ensure ngrok is running and URL is updated
- Check Plivo account balance
- Verify "From" number is verified in Plivo

### Issue: No agents available

**Solution:**
```bash
# Restart the app to reinitialize agent heaps
python app.py
```

### Issue: Real-time updates not working

**Solution:**
- Check browser console for Socket.IO errors
- Verify Flask-SocketIO is installed
- Ensure no CORS issues (check browser console)

---

## Performance Metrics

The system tracks:
- **Average call duration** per agent
- **Customer satisfaction** (feedback ratings)
- **Agent utilization** (calls per hour)
- **Response time** (time to connect to agent)
- **Call completion rate**

---

## Security Notes

- Credentials loaded from **environment variables**
- No hardcoded secrets in code
- `.env.example` provided for reference
- **Always use HTTPS** (ngrok provides this)
- **Do not commit `.env` to version control**

---

## Deployment Considerations

For production deployment:

1. **Use a production WSGI server** (Gunicorn, uWSGI)
2. **Replace SQLite** with PostgreSQL/MySQL
3. **Deploy on cloud platform** (Heroku, AWS, GCP)
4. **Use managed ngrok alternative** (Plivo's built-in callbacks work better with public IPs)
5. **Add authentication** for dashboard access
6. **Implement rate limiting** on API endpoints
7. **Add logging and monitoring** (Sentry, DataDog)

---

## Learning Outcomes

This project demonstrates:
- Building **scalable IVR systems** with Plivo XML
- Implementing **heap-based algorithms** for routing
- Creating **real-time applications** with WebSockets
- Designing **agentic systems** that learn from feedback
- Building **full-stack applications** with Flask
- Managing **complex state** across multiple call flows

---

## Test Phone Numbers

**DO NOT use these in production. For demo/testing only:**

| Number | Purpose |
|--------|---------|
| `14692463987` | Plivo outbound caller ID |
| `14692463990` | English agent (placeholder) |
| `918031274121` | Spanish agent (placeholder) |

---

## Contributing

This is an assignment project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

This project is for educational purposes as part of a Plivo assignment.

---

## Acknowledgments

- **Plivo** for the Voice XML API
- **Flask** community for excellent documentation
- **Socket.IO** for real-time capabilities

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Plivo documentation: https://www.plivo.com/docs/voice/
3. Check Flask-SocketIO docs: https://flask-socketio.readthedocs.io/

---

## Happy Coding!

Built with love using Flask and Plivo Voice XML API
