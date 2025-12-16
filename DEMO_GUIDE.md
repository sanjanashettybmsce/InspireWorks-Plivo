# IVR System - Quick Demo Guide

## 🎯 System Overview (30 seconds)

This is a **multi-level IVR (Interactive Voice Response) system** built with **Flask, SQLAlchemy, and Plivo Voice API**. It demonstrates intelligent call routing, real-time dashboards, and feedback-driven agent prioritization.

---

## 🏗️ Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLAlchemy (SQLite)
- **Real-time:** Flask-SocketIO (WebSockets)
- **Telephony:** Plivo Voice XML API
- **Frontend:** HTML/CSS/JavaScript
- **Tunnel:** ngrok (expose local server to Plivo)

---

## 📞 How It Works

### **3-Level IVR Flow:**

```
Level 1: Language Selection
├── Press 1 → English
└── Press 2 → Spanish
         ↓
Level 2: Action Menu
├── Press 1 → Play Audio Message
└── Press 2 → Connect to Live Agent
         ↓
Level 3: Feedback (if agent call)
├── 1 = Poor
├── 2 = Fair
├── 3 = Good
└── 4 = Excellent
```

---

## 🧠 Key Intelligence Features

### **1. Heap-Based Agent Routing**
- Maintains **two separate priority heaps** (English & Spanish agents)
- **Priority score** calculated as:
  ```
  score = (recent_calls × 10) + (avg_duration / 60) - (avg_rating × 5)
  ```
- **Lower score = Higher priority** (gets routed next call)

### **2. Feedback-Driven Adaptation**
- Customer rates agent (1-4 stars)
- Rating updates agent's priority score
- **High performers get more calls** automatically
- **Poor performers flagged** for coaching

### **3. Load Balancing**
- Tracks recent call count
- Prevents agent overload
- Distributes calls fairly

---

## 🚀 Quick Start (Demo Flow)

### **Setup (one-time):**
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Plivo credentials
cp .env.example .env
# Add your PLIVO_AUTH_ID and PLIVO_AUTH_TOKEN

# 3. Start Flask server
/Users/sanjana/Desktop/Plivo1/.venv/bin/python app.py

# 4. In another terminal: Start ngrok tunnel
ngrok http 5000
# (Already configured: https://scholarly-introspective-irene.ngrok-free.dev)
```

### **Demo Steps:**

**Step 1: Show the Dashboard**
- Open http://127.0.0.1:5000
- Explain: "This is the customer-facing IVR interface"
- Show: Phone input, agent status, call history

**Step 2: Initiate a Call**
- Enter phone number: `+91 9663471159` (or your test number)
- Click "Start Call"
- Plivo calls the number via ngrok URL

**Step 3: Follow IVR**
- Answer the call
- Press 1 for English / 2 for Spanish
- Press 1 for message or 2 for agent
- If you choose agent, system routes to best available agent

**Step 4: Rate the Call**
- After agent call ends, press 1-4 to rate
- Rating stored in database
- Agent priority recalculated

**Step 5: Show Real-Time Updates**
- Agent status updates live on dashboard
- Call history populates automatically
- WebSocket feeds data in real-time

---

## 📊 Core Components

### **1. Models (Database)**
- **Agent:** Phone, language, availability, performance metrics
- **Customer:** Phone, call history, preferences
- **CallLog:** Call details, duration, status
- **Feedback:** Rating, agent performance tracking

### **2. Services**
- **agent_heap.py:** Intelligent routing with heap priority queues
- **call_manager.py:** Track active call sessions

### **3. Flask Routes**
- `/` → Dashboard UI
- `/call` → Initiate outbound call
- `/ivr/start` → Level 1 (language)
- `/ivr/menu` → Level 2 (actions)
- `/ivr/feedback` → Level 3 (ratings)
- `/plivo/callback` → Call completion & feedback storage

### **4. Frontend**
- Real-time agent dashboard
- Call history tracking
- Responsive black/white design

---

## 🎯 Key Demo Points (Talking Points)

### **Interview Talking Points:**

1. **"Why Heap-Based Routing?"**
   - More efficient than random assignment
   - O(log n) insertion/extraction
   - Automatically adapts based on performance

2. **"How Does Feedback Drive Intelligence?"**
   - Customers rate agents (1-4 stars)
   - Ratings recalculate priority scores
   - **Virtuous cycle:** Good agents get more calls → more experience → better ratings

3. **"Scalability?"**
   - Separate heaps per language
   - Can be extended to skill-based routing
   - Database tracks all metrics for analytics

4. **"Real-Time Updates?"**
   - WebSocket (Socket.IO) feeds live agent status
   - No page refresh needed
   - Shows agent availability, ratings, call counts

5. **"Why This Tech Stack?"**
   - Flask: Lightweight, easy to understand
   - SQLAlchemy: ORM flexibility for scaling
   - Plivo: Industry-standard VoIP provider
   - Socket.IO: Real-time capabilities

---

## 🔑 Test Numbers

- **From Number:** 14692463987 (Plivo outbound caller ID)
- **English Agent:** 14692463990
- **Spanish Agent:** 918031274121

---

## ✅ What You Can Demo

1. ✅ Make an outbound call
2. ✅ Navigate IVR (language + action selection)
3. ✅ Connect to agent (agent routing logic)
4. ✅ Rate the call (feedback collection)
5. ✅ Watch real-time dashboard updates
6. ✅ View call history
7. ✅ Explain heap algorithm
8. ✅ Show database models
9. ✅ Demonstrate feedback impact on routing

---

## 💡 Interview Edge (Agentic Intelligence)

**The "agentic" aspect:**
- System doesn't just route calls randomly
- It **learns** from customer feedback
- **Adapts** priority based on performance
- Creates a **self-optimizing** agent allocation system
- This could scale to ML-based predictions

**Why it matters:**
- Better customer experience (top agents handle more calls)
- Reduced training need (poor performers identified quickly)
- Data-driven insights (QA analytics)

---

## 🎬 Demo Script (2-3 minutes)

**"Let me walk you through this IVR system..."**

1. *Show dashboard:* "This is the customer interface where users input their phone number to start a call."

2. *Enter number:* "When we click Start Call, Plivo initiates an outbound call..."

3. *Simulate call:* "The customer answers and gets the IVR menu - Language selection, then action selection."

4. *Show routing logic:* "Behind the scenes, our system maintains priority heaps for each language. When a customer requests an agent, we use a heap-based algorithm to select the best available agent based on their availability, performance, and call load."

5. *Show real-time updates:* "Notice how the agent status updates in real-time using WebSockets. No page refresh needed."

6. *Explain feedback:* "After the call, the customer rates their experience. This rating recalculates the agent's priority score, so high performers automatically get routed more calls. It's an adaptive, self-optimizing system."

7. *Show database:* "All this data is persisted in SQLAlchemy models - agents, customers, call logs, and feedback - enabling comprehensive analytics."

---

## 🏆 Impressive Points for Interview

✅ **Full-stack implementation** (frontend + backend + database)
✅ **Algorithm knowledge** (heap-based priority queues)
✅ **Real-time capabilities** (WebSocket integration)
✅ **Design patterns** (service layer, models, routes)
✅ **API integration** (Plivo VoIP provider)
✅ **Data persistence** (SQLAlchemy ORM)
✅ **Agentic/intelligent routing** (feedback loop)
✅ **Production considerations** (ngrok tunneling, error handling)

---

## 🚨 Common Demo Issues & Fixes

| Issue | Fix |
|-------|-----|
| "Error: answer_url not valid" | Check ngrok is running and URL is correct |
| "No module named 'plivo'" | Use virtual env: `/Users/sanjana/Desktop/Plivo1/.venv/bin/python` |
| "Agent not connecting" | Verify Plivo credentials in `.env` |
| "Real-time updates not working" | Check browser console for Socket.IO errors |

---

## 📱 Quick Reference Card

```
Dashboard: http://127.0.0.1:5000
Server: /Users/sanjana/Desktop/Plivo1/.venv/bin/python app.py
ngrok: https://scholarly-introspective-irene.ngrok-free.dev

Test Call:
→ Enter: +91 9663471159
→ Press: 1 (English) or 2 (Spanish)
→ Press: 1 (Message) or 2 (Agent)
→ Rate: 1-4 (if agent call)
```

---

## 🎓 Explanation Topics (If Asked)

**"Why did you use heaps?"**
- Priority queue insertion in O(log n)
- Natural fit for "best agent next" problem
- Elegant handling of dynamic priority changes

**"How do you ensure fairness?"**
- Recent call count prevents overload
- Average duration spreads work fairly
- Feedback scores reward quality, not just speed

**"What would you add for production?"**
- PostgreSQL instead of SQLite
- Redis for caching agent status
- ML model to predict agent performance
- Call recording and transcription
- Advanced analytics dashboard

**"How would you scale this?"**
- Horizontal scaling (multiple IVR servers)
- Load balancer in front
- Separate database server
- Queue-based job system (Celery)
- Message broker (RabbitMQ)

---

Good luck with your interview! 🚀
