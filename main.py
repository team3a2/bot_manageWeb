import requests, threading, telebot, time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# Telegram Bot Token và chat_id
API_TOKEN = '6996993496:AAFJwET1MnlWoViuCHb4__Ze_Z-5YOkWJgc'


# from flask import Flask,render_template
# from threading import Thread
# app = Flask(__name__)
# @app.route('/')
# def index():
#     return "Alive"
# def run():
#   app.run(host='0.0.0.0',port=8080)
# def keep_alive():  
#     t = Thread(target=run)
#     t.start()

# keep_alive()
# Tạo bot
bot = telebot.TeleBot(API_TOKEN)

users_money_order = {}
_id_users_money_order_was_sent_to_ADMIN = []
ipAddress_and_userAgent_received_promotion = []

CHAT_ID_ADMIN = 5042050264
print("-"*30)
class WebAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None  # Initialize token

    def get(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        if self.token:
            headers = headers or {}
            headers['Authorization'] = f"Bearer {self.token}"
        response = self.session.get(url, params=params, headers=headers)
        return response
      
    def post(self, endpoint, json=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        if self.token:
            headers = headers or {}
            headers['Authorization'] = f"Bearer {self.token}"
        response = self.session.post(url, json=json, headers=headers)
        return response
    def put(self, endpoint, json=None, params=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        if self.token:
            headers = headers or {}
            headers['Authorization'] = f"Bearer {self.token}"
        response = self.session.put(url, json=json, params=params,  headers=headers)
        return response
    def login(self, email, password):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Origin': 'https://billapp-neon.vercel.app',
        }
        login_endpoint = 'api/auth/login' 
        data = {
            'email': email,
            'password': password
        }

        response = self.post(login_endpoint, json=data, headers=headers)
        try:
            response.raise_for_status()
        except requests.HTTPError:
            print(f"__Đăng nhập thất bại [{response.content}]")
            return None

        print("__Đăng nhập thành công")
        
        # Assuming the token is returned in JSON response
        json_response = response.json()
        self.token = json_response.get('token')  # Adjust the key according to API's response
        if not self.token:
            print("__Token not found in response.")
        else:
            print(f"__Token: {self.token}")
        return response

api = WebAPI(base_url="https://billapp.onrender.com/")

# Đăng nhập
login_response = api.login(email="admin@gmail.com", password="123123")


def get_ip_and_useragent_from_all_orders():
    try:
        response = api.get('api/deposit')
        response.raise_for_status()
    except Exception as er:
        print(f"Lỗi get api: check_deposit_form_new func [{er}]")
        return None
    data = response.json()
    for i in range(len(data)):
        data_detail = data[i]
        for item in data_detail['user']['sessions']:
            ipAddress_and_userAgent_received_promotion.append(item['ipAddress'])
            ipAddress_and_userAgent_received_promotion.append(item['userAgent'])
    print("__Đẫ lưu IpAddress và UserAgent của những ip đã từng nạp")
get_ip_and_useragent_from_all_orders()

def get_money_order_status_is_pending():
    global users_money_order, ipAddress_and_userAgent_received_promotion
    try:
        response = api.get('api/deposit')
        response.raise_for_status()
    except Exception as er:
        print(f"Lỗi get api: check_deposit_form_new func [{er}]")
        return None
    
    data = response.json()

    for i in range(len(data)):
        data_detail = data[i]
        if data_detail["status"] == 'pending':
            if data_detail['_id'] in users_money_order:
                return
            users_money_order[data_detail['_id']] = {
                "amount": data_detail["amount"],
                "username": data_detail['user']['username'],
                "email": data_detail['user']['email'],
                "sessions" :  data_detail['user']['sessions']
            }
            # users_money_order = dict(sorted(users_money_order.items(), reverse=True))
            for item in data_detail['user']['sessions']:
                if item['ipAddress'] not in ipAddress_and_userAgent_received_promotion:
                    ipAddress_and_userAgent_received_promotion.append(item['ipAddress'])
                if item['userAgent'] not in ipAddress_and_userAgent_received_promotion:
                    ipAddress_and_userAgent_received_promotion.append(item['userAgent'])

        continue


def action_accept_or_reject_order_money(action , _id):
    
    endpoint = ''
    if action == 'accept':
        endpoint = f'api/deposit/confirm/{_id}'
    elif action =='reject':
        endpoint = f'api/deposit/reject/{_id}'
    response = api.put(endpoint)
    return response
def send_money_order_to_ADMIN():
    if len(users_money_order):
        for _id, data_detail in users_money_order.items():
            if _id in _id_users_money_order_was_sent_to_ADMIN:
                continue

            _amount = data_detail['amount']
            _username = data_detail['username']
            _email = data_detail['email']
            _sessions = data_detail['sessions']
            _notification = ''


      
            for item in _sessions:
                if item['ipAddress'] in ipAddress_and_userAgent_received_promotion:
                    _notification = '⚠️ Không được nhận khuyến mãi 500k'
                    continue
                _notification = '✅Được nhận khuyến mãi 500k'


            context = f"""
<b> Yêu cầu NẠP TIỀN: </b>
    <i>
    _Số tiền: {_amount} k 
    _Tên tài khoản: {_username}
    _email: {_email}

    {_notification}
    </i>
"""     
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("Chấp nhận", callback_data=f"accept {_id}"),
                InlineKeyboardButton("Từ chối", callback_data=f"reject {_id}"),
            )
            try:
                bot.send_message(CHAT_ID_ADMIN, context, parse_mode="html", reply_markup=markup)
            except telebot.apihelper.ApiTelegramException:
                print(f'__không tìm thấy chatID_ADMIN: {CHAT_ID_ADMIN}')
            _id_users_money_order_was_sent_to_ADMIN.append(_id)
def auto_handle():
    while True:
        time.sleep(3)
        get_money_order_status_is_pending()
        send_money_order_to_ADMIN()


thread = threading.Thread(target=auto_handle)
thread.setDaemon(True)

thread.start()




@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Chào mừng! Bạn có thể gửi tin nhắn để kiểm tra đơn đặt hàng.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global CHAT_ID_ADMIN
    if message.text.lower() == 'id': return bot.reply_to(message, message.chat.id) 
    if message.text.startswith('/changeid'):
        new_id = message.text.split()[1]
        try:
            CHAT_ID_ADMIN = new_id
            bot.reply_to(message, "Đã thay ID chat thành công!")
        except ValueError:
            bot.reply_to(message, "ID chat phải là một số!")


# Khởi chạy bot

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    
    if "accept" in call.data:
        _id_deposit = call.data.split()[1]
        response = action_accept_or_reject_order_money("accept", _id_deposit)
        if response.ok:
            bot.answer_callback_query(call.id, "Đã cộng tiền")

        bot.answer_callback_query(call.id, f"Lỗi [status code: {response.status_code}] [function: action_accept_or_reject_order_money]")
        
            # bot.send_message(call.message.chat.id, "Bạn đã chấp nhận yêu cầu.")
    elif "reject" in call.data:
        _id_deposit = call.data.split()[1]
        response = action_accept_or_reject_order_money("reject", _id_deposit)
        if response.ok:
            bot.answer_callback_query(call.id, "Đã từ chối")

        bot.answer_callback_query(call.id, f"Lỗi [status code: {response.status_code}] [function: action_accept_or_reject_order_money]")
        
        # bot.send_message(call.message.chat.id, "Bạn đã từ chối yêu cầu.")
    bot.delete_message(call.message.chat.id, call.message.message_id)

bot.infinity_polling(timeout=10, long_polling_timeout = 5)