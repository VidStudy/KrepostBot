import os
from application import db
from application.core import orderservice
from application.core.models import Order, Transaction
from datetime import datetime

STATE_CREATED                  = 1
STATE_COMPLETED                = 2
STATE_CANCELLED                = -1
STATE_CANCELLED_AFTER_COMPLETE = -2

REASON_RECEIVERS_NOT_FOUND         = 1
REASON_PROCESSING_EXECUTION_FAILED = 2
REASON_EXECUTION_FAILED            = 3
REASON_CANCELLED_BY_TIMEOUT        = 4
REASON_FUND_RETURNED               = 5
REASON_UNKNOWN                     = 10


class PaymeException(Exception):

    INTERNAL_SYSTEM         = -32400
    INSUFFICIENT_PRIVILEGE  = -32504
    INVALID_JSON_RPC_OBJECT = -32600
    METHOD_NOT_FOUND        = -32601
    INVALID_AMOUNT          = -31001
    TRANSACTION_NOT_FOUND   = -31003
    INVALID_ACCOUNT         = -31050
    COULD_NOT_CANCEL        = -31007
    COULD_NOT_PERFORM       = -31008

    def __init__(self, input, code):
        self.message = 'PaymeException: error ' + str(code)
        self.input = input
        self.code = code
        super().__init__(self.message)

    def response(self):
        error_names = {value: name for name, value in vars(PaymeException).items() if name.isupper()}

        return {
            'id': self.input['id'],
            'result': None,
            'error': {
                'code': self.code,
                'message': {
                    'ru': error_names[self.code],
                    'en': error_names[self.code],
                    'uz': error_names[self.code]
                },
                'data': None
            }
        }


def check_perform_transaction(input):
    order_id = input['params']['account']['order_id']
    order = Order.query.get(order_id)
    if order is None:
        raise PaymeException(input, PaymeException.INVALID_ACCOUNT)
    if order.confirmed:
        raise PaymeException(input, PaymeException.INVALID_ACCOUNT)
    transaction = Transaction.query.filter(Transaction.order_id == order_id).first()
    if transaction:
        raise PaymeException(input, PaymeException.INVALID_ACCOUNT)
    if int(order.total_amount * 100) != int(input['params']['amount']):
        raise PaymeException(input, PaymeException.INVALID_AMOUNT)
    return { 'allow': True }


def check_transaction(input):
    transaction_id = input['params']['id']
    transaction = Transaction.query.filter(Transaction.system_id == transaction_id).first()
    if transaction is None:
        raise PaymeException(input, PaymeException.TRANSACTION_NOT_FOUND)

    perform_time = 0
    cancel_time = 0
    if transaction.performed_at:
        perform_time = int(transaction.performed_at.timestamp() * 1000)
    if transaction.cancelled_at:
        cancel_time = int(transaction.cancelled_at.timestamp() * 1000)

    return {
        'create_time': int(datetime.timestamp(transaction.created_at) * 1000),
        'perform_time': perform_time,
        'cancel_time': cancel_time,
        'transaction': str(transaction.id),
        'state': transaction.status,
        'reason': transaction.reason
    }


def create_transaction(input):
    transaction_id = input['params']['id']
    transaction = Transaction.query.filter(Transaction.system_id == transaction_id).first()

    if transaction:
        if transaction.status != STATE_CREATED:
            raise PaymeException(input, PaymeException.COULD_NOT_PERFORM)
        elif transaction.status == STATE_CREATED and (datetime.now() - transaction.created_at).total_seconds() > 12 * 3600:
            transaction.cancelled_at = datetime.now()
            if transaction.status == STATE_COMPLETED:
                transaction.status = STATE_CANCELLED_AFTER_COMPLETE
            else:
                transaction.status = STATE_CANCELLED
            transaction.reason = REASON_CANCELLED_BY_TIMEOUT

            db.session.add(transaction)
            db.session.commit()

            raise PaymeException(input, PaymeException.COULD_NOT_PERFORM)
        else:
            return {
                'create_time': int(datetime.timestamp(transaction.created_at) * 1000),
                'transaction': str(transaction.id),
                'state': transaction.status,
                'receivers': None
            }
    else:
        check_perform_transaction(input)

        time = datetime.fromtimestamp(input['params']['time'] / 1000)
        if (datetime.now() - time).total_seconds() > 12 * 3600:
            raise PaymeException(input, PaymeException.INVALID_ACCOUNT)
        
        transaction = Transaction()
        transaction.system = 'payme'
        transaction.system_id = input['params']['id']
        transaction.status = STATE_CREATED
        transaction.amount = input['params']['amount']
        transaction.order_id = input['params']['account']['order_id']
        transaction.created_at = time
        db.session.add(transaction)
        db.session.commit()

        return {
            'create_time': int(datetime.timestamp(transaction.created_at) * 1000),
            'transaction': str(transaction.id),
            'state': transaction.status,
            'receivers': None
        }


def perform_transaction(input):
    transaction_id = input['params']['id']
    transaction = Transaction.query.filter(Transaction.system_id == transaction_id).first()
    if transaction is None:
        raise PaymeException(input, PaymeException.TRANSACTION_NOT_FOUND)
    
    if transaction.status == STATE_CREATED:
        if (datetime.now() - transaction.created_at).total_seconds() > 12 * 3600:
            transaction.cancelled_at = datetime.now()
            if transaction.status == STATE_COMPLETED:
                transaction.status = STATE_CANCELLED_AFTER_COMPLETE
            else:
                transaction.status = STATE_CANCELLED
            transaction.reason = REASON_CANCELLED_BY_TIMEOUT

            db.session.add(transaction)
            db.session.commit()
            
            raise PaymeException(input, PaymeException.COULD_NOT_PERFORM)
        else:
            order = transaction.order
            order.confirmed = True
            order.confirmation_date = datetime.now()
            for item in order.order_items:
                item.dish.quantity -= item.count
                db.session.add(item.dish)
            db.session.add(order)

            transaction.performed_at = datetime.now()
            transaction.status = STATE_COMPLETED
            db.session.add(transaction)
            db.session.commit()

            return {
                'transaction': str(transaction.id),
                'perform_time': int(datetime.timestamp(transaction.performed_at) * 1000),
                'state': transaction.status
            }
    elif transaction.status == STATE_COMPLETED:
        return {
            'transaction': str(transaction.id),
            'perform_time': int(datetime.timestamp(transaction.performed_at) * 1000),
            'state': transaction.status
        }
    else:
        raise PaymeException(input, PaymeException.COULD_NOT_PERFORM)


def cancel_transaction(input):
    transaction_id = input['params']['id']
    transaction = Transaction.query.filter(Transaction.system_id == transaction_id).first()
    if transaction is None:
        raise PaymeException(input, PaymeException.TRANSACTION_NOT_FOUND)

    if transaction.status == STATE_CANCELLED or transaction.status == STATE_CANCELLED_AFTER_COMPLETE:
        return {
            'transaction': str(transaction.id),
            'cancel_time': int(datetime.timestamp(transaction.cancelled_at) * 1000),
            'state': transaction.status
        }
    elif transaction.status == STATE_CREATED or transaction.status == STATE_COMPLETED:
        transaction.reason = input['params']['reason']
        transaction.cancelled_at = datetime.now()
        if transaction.status == STATE_COMPLETED:
            transaction.status = STATE_CANCELLED_AFTER_COMPLETE
        else:
            transaction.status = STATE_CANCELLED
        transaction.order.confirmed = False
        transaction.order.confirmation_date = None
        db.session.add(transaction.order)
        db.session.add(transaction)
        db.session.commit()
        return {
            'transaction': str(transaction.id),
            'cancel_time': int(datetime.timestamp(transaction.cancelled_at) * 1000),
            'state': transaction.status
        }
    elif transaction.status == STATE_COMPLETED:
        raise PaymeException(input, PaymeException.COULD_NOT_CANCEL)


def get_statement(input):
    date_from = datetime.fromtimestamp(input['params']['from'] / 1000)
    date_to = datetime.fromtimestamp(input['params']['to'] / 1000)

    transactions = Transaction.query.filter(Transaction.system == 'payme', Transaction.created_at.between(date_from, date_to)).get()
    result = []
    for transaction in transactions:
        perform_time = 0
        cancel_time = 0
        if transaction.performed_at:
            perform_time = int(transaction.performed_at.timestamp() * 1000)
        if transaction.cancelled_at:
            cancel_time = int(transaction.cancelled_at.timestamp() * 1000)

        result.append({
            'id': transaction.system_id,
            'time': int(datetime.timestamp(transaction.created_at) * 1000),
            'amount': transaction.amount,
            'account': {
                'order_id': transaction.order_id
            },
            'create_time': int(datetime.timestamp(transaction.created_at) * 1000),
            'perform_time': perform_time,
            'cancel_time': cancel_time,
            'transaction': str(transaction.id),
            'state': transaction.status,
            'reason': transaction.reason
        })

    return {
        'transactions': result
    }

import urllib3
import json

def create_check(order):
    try:
        print('create_check')
        http = urllib3.PoolManager()
        req_headers = {
            'Content-Type': 'application/json',
            'X-Auth': os.getenv('PAYME_MERCHANT_ID') + ':' + os.getenv('PAYME_CASHIER'),
        }

        encoded_data = json.dumps({
            'id': 1,
            'method': 'receipts.create',
            'params': {
                'amount': int(order.total_amount * 100),
                'account': {
                    'order_id': order.id
                }
            }
        }).encode('utf-8')

        print(req_headers)
        print(encoded_data)

        #r = http.request('POST', 'https://checkout.paycom.uz/api', headers=req_headers, body=encoded_data)
        #print(r.data.decode('utf-8'))
        #resp_dict = json.loads(r.data.decode('utf-8'))

        #check_id = resp_dict['result']['receipt']['_id']
        check_id = 'check_id'

        phone = order.phone_number
        if phone[0] == '+':
            phone = phone[1:]

        encoded_data = json.dumps({
            'id': 2,
            'method': 'receipts.send',
            'params': {
                'id': check_id,
                'phone': phone
            }
        }).encode('utf-8')

        print(encoded_data)

        #r = http.request('POST', 'https://checkout.paycom.uz/api', headers=req_headers, body=encoded_data)
        #print(r.data.decode('utf-8'))
    except Exception as e:
        print(e)


import base64
from flask import Blueprint, request, jsonify
bp = Blueprint('payme', __name__)

@bp.route('/payme/endpoint', methods=['POST'])
def payme_endpoint():
    try:
        input = request.json
        auth = request.headers.get('Authorization')
        credentials = os.getenv('PAYME_LOGIN') + ':' + os.getenv('PAYME_CASHIER')
        if not auth or base64.b64decode(auth.split()[1]).decode() != credentials:
            raise PaymeException(input, PaymeException.INSUFFICIENT_PRIVILEGE)

        method = input['method']
        result = None

        if method == 'CheckPerformTransaction':
            result = check_perform_transaction(input)
        elif method == 'CheckTransaction':
            result = check_transaction(input)
        elif method == 'CreateTransaction':
            result = create_transaction(input)
        elif method == 'PerformTransaction':
            result = perform_transaction(input)
        elif method == 'CancelTransaction':
            result = cancel_transaction(input)
        elif method == 'GetStatement':
            result = get_statement(input)
        else:
            raise PaymeException(input, PaymeException.METHOD_NOT_FOUND)
        
        return jsonify({
            'jsonrpc': '2.0',
            'id': input['id'],
            'result': result,
            'error': None
        })
        
    except PaymeException as e:
        return jsonify(e.response())
