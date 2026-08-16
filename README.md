🏥 Patient Appointment & 📅Queue Management System
A simple hospital/clinic queue management system for managing patient appointments with priority-based scheduling ⏱️.
Built as a university project with a clear focus on DSA (Data Structures & Algorithms) implemented using Python 🐍.

🚀 Features
🔢 4-Level Priority System: 🟢Normal , 🟡 Accident , 🟠Emergency , 🔴Critical
➜ Served by priority first, then arrival time

👤📊 Patient Dashboard: View appointments , add new , search

👨‍⚕️📋 Doctor Dashboard: View patients, mark complete , reschedule , search

📝🧾 Register Patient: Add appointments (name, date, time, priority, optional doctor)

🧠📐 DSA Implementation: FIFO Queue, 4-Level Priority Queue, Greedy Scheduling (dsa/)

🔐👥 Authentication: Login & Sign up with role-based access


cool!
🛠️ Technology Stack
⚙️ Backend: Python, Flask
🎨 Frontend: HTML, CSS, JavaScript
🗄️ Database: SQLite
🧠 DSA: Queue, Priority Queue, Linked List, Greedy Scheduler
🗂️ Project Structure
project/
├── app.py                 # Flask main app
├── database.db            # SQLite (created on first run)
├── models/
│   ├── patient.py         # Patient Linked List (DSA)
│   └── doctor.py          # Doctor model
├── dsa/
│   ├── queue.py           # Queue & Priority Queue (DSA)
│   └── scheduler.py       # Greedy scheduling algorithm (DSA)
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── register_patient.html
│   ├── patient_dashboard.html
│   └── doctor_dashboard.html
├── static/
│   └── style.css
├── requirements.txt
└── README.md
⚙️ Setup & ▶️ Run
Create a virtual environment (recommended):

python -m venv venv
venv\Scripts\activate   # Windows
Install dependencies:

pip install -r requirements.txt
Run the app:

python app.py
Open http://127.0.0.1:5000 in your browser.

📌 Preloaded Data
👨‍⚕️ Doctor login (for queue dashboard):

Email: fayerakena@doctor.gmail.com
Password: ke123
👤 Patient free-pass login:

Email: tamiratyisakor@gmail.com
Password: patient123
🗃️Sample appointments and 🗃️sample doctors are inserted on first run.

🧠📚 DSA Concepts Used
Concept	Location	Purpose
🔁Queue (FIFO)	dsa/queue.py	Per-priority queues
🚦Priority Queue	dsa/queue.py	4 levels: Critical > Emergency > Accident > Normal
⚡Greedy Scheduling	dsa/scheduler.py	Serve by priority first, then by arrival time
📄Pages
Home🏠 – Public; welcome and links
Login🔐 / Sign up✍️ – Auth
My Appointments📅 (Patient) – Table, add appointment, search
My Patients👨‍⚕️ (Doctor) – List, mark complete, reschedule, search
Register Patient📝 (Receptionist/Doctor) – Add appointments (name, date, time, priority)
📝Notes
Runs locally only; no deployment.
Logic is separated: DSA in models/ and dsa/, UI in Flask + templates.
Code is commented and kept simple for presentations.
ℹ️Troubleshooting
sqlite3.OperationalError: disk I/O error: If the project folder is under OneDrive/Dropbox, the DB file may be locked. The app will automatically use a DB in your system temp folder (%TEMP%\hospital_queue.db) so it still runs. Move the project outside OneDrive to use database.db in the project folder.
Port 5000 in use: Edit app.py and change port=5000 to another port (e.g. 5001).
