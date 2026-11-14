from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_session_management_privatbank2026'

# Use /tmp for SQLite on Vercel (the only place we can write)
db_path = os.path.join('/tmp', 'privatbank.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    receiver_bank_account = db.Column(db.String(50), nullable=False)
    receiver_bank_name = db.Column(db.String(100), nullable=False)

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(account_number='10001').first():
            demo_user = User(
                name='Demo Sender',
                account_number='10001',
                balance=10000.00,
                currency='USD'
            )
            db.session.add(demo_user)
            db.session.commit()

# Initialize database when the app starts
init_db()

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/send', methods=['POST'])
def send_money():
    sender_account = request.form.get('sender_account')
    receiver_account = request.form.get('receiver_account')
    amount = float(request.form.get('amount') or 0)
    currency = request.form.get('currency')
    receiver_bank_name = request.form.get('receiver_bank_name')

    if amount <= 0:
        flash('Amount must be positive.', 'error')
        return redirect(url_for('index'))

    sender = User.query.filter_by(account_number=sender_account).first()
    receiver = User.query.filter_by(account_number=receiver_account).first()

    if not sender or not receiver:
        flash('Sender or Receiver account not found.', 'error')
        return redirect(url_for('index'))

    if sender.balance >= amount:
        sender.balance -= amount
        receiver.balance += amount

        transaction = Transaction(
            sender_id=sender.id,
            receiver_id=receiver.id,
            amount=amount,
            currency=currency,
            receiver_bank_account=receiver_account,
            receiver_bank_name=receiver_bank_name
        )

        db.session.add(transaction)
        db.session.commit()
        flash(f'Successfully sent {amount} {currency}.', 'success')
    else:
        flash('Insufficient funds.', 'error')

    return redirect(url_for('index'))
    # This helps Vercel find the app
app = app
