from flask import Flask, request, jsonify
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.threadpool import ThreadPoolExecutor
import psycopg2
import os

app = Flask(__name__)

# Configure Scheduler
scheduler = BackgroundScheduler({
    'jobstores': {
        'default': MemoryJobStore()
    },
    'executors': {
        'default': ThreadPoolExecutor(20)
    },
    'job_defaults': {
        'coalesce': True,
        'max_instances': 3
    }
})
scheduler.start()

def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    return conn

def send_reminder(phone_number):
    try:
        client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
        message = client.messages.create(
            body="This is a reminder from [Your Shop Name].",
            from_='[Your Twilio Phone Number]',
            to=phone_number
        )
        print(f"Message sent to {phone_number}: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS to {phone_number}: {e}")

@app.route('/add_customer', methods=['POST'])
def add_customer():
    try:
        data = request.get_json()
        name = data['name']
        phone = data['phone']
        email = data['email']
        visit_date = data['visitDate']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO customers (name, phone, email, visit_date) 
            VALUES (%s, %s, %s, %s)
        """, (name, phone, email, visit_date))
        conn.commit()
        cur.close()
        conn.close()

        # Schedule reminder (example: 30 days after visit_date)
        # Calculate next_reminder_date 
        # schedule_reminder_job(phone, next_reminder_date) 

        return jsonify({'message': 'Customer added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper function to schedule reminders
def schedule_reminder_job(phone_number, next_reminder_date):
    scheduler.add_job(
        send_reminder, 
        'date', 
        run_date=next_reminder_date, 
        args=[phone_number]
    )

if __name__ == '__main__':
    app.run(debug=True)
