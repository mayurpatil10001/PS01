# AI Chatbot - Quick Start Guide

## 🎯 What is the AI Chatbot?

The AI Chatbot is an intelligent assistant built into BioGuard AI that helps health officers quickly access information about:
- 🚨 Critical disease alerts
- 🦠 Disease prevention measures
- 🗺️ Village risk status
- 💧 Water quality monitoring
- 📊 System statistics and impact

---

## 🚀 How to Access the Chatbot

### Step 1: Login to BioGuard AI
1. Open your browser and go to the BioGuard AI dashboard
2. Login with your analyzer credentials:
   - Username: `analyzer`
   - Password: `analyzer123`

### Step 2: Find the Chatbot Button
Look for the **floating cyan button** in the **bottom-right corner** of the dashboard.

```
┌─────────────────────────────────────────┐
│                                         │
│         BioGuard AI Dashboard           │
│                                         │
│   [Villages]  [Alerts]  [Sensors]       │
│                                         │
│                                         │
│                                    ┌────┐
│                                    │ 💬 │ ← Chatbot Button
│                                    └────┘
└─────────────────────────────────────────┘
```

### Step 3: Click to Open
Click the button to open the chat window. You'll see:
- Welcome message
- Suggested questions
- Input field to type your question

---

## 💬 Example Questions to Ask

### Critical Alerts
- "Show me critical alerts"
- "What are the urgent issues?"
- "Any emergency situations?"

### Disease Information
- "Tell me about cholera prevention"
- "What causes typhoid?"
- "How to prevent dysentery?"

### Village Monitoring
- "Which villages need attention?"
- "Show me Dharangaon status"
- "What's the risk in Yawal?"

### Water Quality
- "What water parameters do you monitor?"
- "Show me sensor readings"
- "What if pH is too low?"

### Actions & Interventions
- "What actions should I take?"
- "Show me resource requirements"
- "How to handle critical alerts?"

### System Status
- "What's the overall system status?"
- "Show me statistics"
- "How many cases were prevented?"

---

## 🎨 Chatbot Interface

```
┌─────────────────────────────────────────┐
│ ✨ AI Assistant          [Always here] │ ← Header
├─────────────────────────────────────────┤
│                                         │
│  👋 Hello! I'm your BioGuard AI...     │ ← AI Message
│  12:30 PM                               │
│                                         │
│                    Show me alerts 💬    │ ← User Message
│                             12:31 PM    │
│                                         │
│  🚨 CRITICAL ALERTS ACTIVE              │ ← AI Response
│  We currently have 2 critical...        │
│  12:31 PM                               │
│                                         │
├─────────────────────────────────────────┤
│ Suggested questions:                    │ ← Suggestions
│ [What actions?] [Resources?] [Prevent?] │
├─────────────────────────────────────────┤
│ Ask me anything...          [Send →]    │ ← Input
└─────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🎯 Smart Responses
The chatbot understands natural language and provides relevant information based on:
- Real-time alert data
- Current village risk scores
- Sensor readings
- Disease predictions

### 💡 Contextual Suggestions
After each response, the chatbot suggests relevant follow-up questions to help you dig deeper.

### 📊 Data-Driven
All responses are based on actual system data, not generic information.

### 🔒 Secure
Only authenticated analyzer users can access the chatbot.

---

## 🔧 Testing the Chatbot

### Option 1: Manual Testing (Web Interface)
1. Start the backend: `cd backend && python main.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Open browser to `http://localhost:3000`
4. Login and click the chatbot button
5. Try asking questions!

### Option 2: Automated Testing (API)
Run the test script to verify all endpoints:

```bash
cd backend
python test_chatbot.py
```

This will test:
- ✅ Authentication
- ✅ Suggested questions
- ✅ Critical alerts query
- ✅ Disease information query
- ✅ Water quality query
- ✅ Village status query
- ✅ Action/intervention query
- ✅ System status query
- ✅ General help query

---

## 📱 User Experience

### Opening the Chat
1. Click the floating button
2. Chat window slides in from bottom-right
3. Welcome message appears
4. Suggested questions displayed

### Asking Questions
1. Type your question in the input field
2. Press Enter or click Send button
3. See "AI is thinking..." indicator
4. Response appears in chat
5. New suggestions appear below

### Using Suggestions
1. Click any suggestion chip
2. Question is automatically sent
3. Response appears immediately

### Closing the Chat
1. Click the X button in the header
2. Chat window slides out
3. Floating button reappears

---

## 🎓 Tips for Best Results

### ✅ DO:
- Ask specific questions
- Use keywords like "critical", "cholera", "water quality"
- Click suggestions for quick access
- Ask follow-up questions for more details

### ❌ DON'T:
- Ask questions outside the system's scope (e.g., "What's the weather?")
- Expect responses about data not in the system
- Use very long, complex sentences

---

## 🐛 Troubleshooting

### Problem: Chatbot button not visible
**Solution**: 
- Check if you're on the dashboard page
- Refresh the page
- Clear browser cache

### Problem: "Unauthorized" error
**Solution**:
- Make sure you're logged in
- Check if your session expired
- Login again

### Problem: No response from chatbot
**Solution**:
- Check if backend is running (port 8001)
- Check browser console for errors
- Verify network connection

### Problem: Slow responses
**Solution**:
- Check backend server performance
- Verify database connection
- Check network latency

---

## 📈 What the Chatbot Can Tell You

### Real-Time Alerts
- Number of critical/high/medium alerts
- Village names with active alerts
- Disease types and risk scores
- Trigger reasons (sensor anomalies, etc.)

### Recommended Actions
- Immediate interventions needed
- Resource requirements (medical supplies, personnel)
- Timeline for actions
- Cost estimates

### Disease Information
- Prevention measures for specific diseases
- Symptoms and causes
- Treatment protocols
- Historical case data

### Village Status
- Risk scores for all villages
- Alert distribution by level
- Top high-risk villages
- Population at risk

### Water Quality
- Parameters monitored (pH, turbidity, TDS)
- Safe ranges for each parameter
- Current sensor status
- Real-time readings

### System Health
- ML model accuracy
- IoT sensor status
- WebSocket connection status
- Impact metrics (cases prevented, cost saved)

---

## 🎯 Success Metrics

The chatbot helps you:
- ⚡ **Save Time**: Get answers in seconds vs. navigating multiple pages
- 🎯 **Make Better Decisions**: Access all relevant data in one place
- 📚 **Learn Faster**: New users can understand the system quickly
- 🚀 **Respond Faster**: Quick access to critical information during emergencies

---

## 📞 Support

If you encounter any issues or have suggestions for improvement:
1. Check the troubleshooting section above
2. Review the full documentation: `AI_CHATBOT_DOCUMENTATION.md`
3. Contact the development team

---

**Happy Chatting! 💬✨**

The AI Chatbot is here to make your job easier and help you protect communities from water-borne diseases more effectively.
