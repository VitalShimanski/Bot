#!/usr/bin/env python3
import sys
import telebot
from pprint import pprint
from string import Template
import mysql.connector
from mysql.connector import errorcode
import requests
from secretdata import TOKEN
import gettext


try:
    db = mysql.connector.connect(
      host="localhost",
      user="root",
      passwd="root",
      port="3307",
      database="dbcourse"
    )
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Что-то не так с вашим именем пользователя или паролем")
    sys.exit()
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("База данных не существует")
    sys.exit()
  else:
    print(err)
    sys.exit()

cursor = db.cursor()

#cursor.execute("CREATE DATABASE IF NOT EXISTS dbcourse")
#cursor = db.cursor()
#cursor.execute("CREATE TABLE courses (id INT AUTO_INCREMENT PRIMARY KEY, \
#Cur_Abbreviation VARCHAR(255), Cur_Scale VARCHAR(255), Cur_Name VARCHAR(255), Cur_OfficialRate VARCHAR(255))")
root_url = "https://api.telegram.org/bot"
my_token = TOKEN
bot_updates = "/getUpdates"

def get_updates(token):
    updates_url = f"{root_url}{my_token}{bot_updates}"
    res = requests.get(updates_url)
    status = res.status_code

    if status == 200:
        updates = res.json()
        return updates
    else:
        print(f"Request failed whit code {res.status_code}")
updates = get_updates(my_token)



updates = get_updates(my_token)
last_message = updates["result"][-1]
print(last_message)
chat_id = last_message["message"]["chat"]["id"]
print(chat_id)

send_message_endpoint = "/sendMessage"


def send_message(token, chat_id, message_text):
    send_message_url = f"{root_url}{my_token}{send_message_endpoint}"
    res = requests.post(send_message_url, {"chat_id": chat_id, "text": message_text})
    status = res.status_code
    if status == 200:
        return True
    else:
        print(f"Request failed whit code {res.status_code}")


last_message_text = last_message["message"]["text"]
default_answer = "Sorry I haven't answer!!!"

if "/" in last_message_text and 'rate' in last_message_text:
    abbr = last_message_text[-3:]
    print(abbr)
else:
    send_message(my_token, chat_id, default_answer)

requested_keys = ("Date", "Cur_Scale","Cur_Name", "Cur_OfficialRate","Cur_Abbreviation")

def get_today_rates():
    root_url = "https://www.nbrb.by/api/exrates/"
    rates_today = "rates?periodicity=0"
    url = f"{root_url}{rates_today}"
    res = requests.get(url)
    status = res.status_code
    try:
        res = requests.get(url)
    except requests.ConnectionError as e:
        print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
        print(str(e))
    except requests.Timeout as e:
        print("OOPS!! Timeout Error" + {e})
        print(str(e))
    except requests.RequestException as e:
        print("OOPS!! General Error" + {e})
        print(str(e))
    except KeyboardInterrupt as e:
        print("Someone closed the program" + {e})
    else:
        if status == 200:
            rates = res.json()
            return rates
rates = get_today_rates()
print(rates)

itemsCourses = []
for rate in rates:
    itemsCourses.append((
        rate['Cur_Abbreviation'],
        rate['Cur_Scale'],
        rate['Cur_Name'],
        rate['Cur_OfficialRate'],


        ))

q = """INSERT INTO courses (Cur_Abbreviation, Cur_Scale, Cur_Name, Cur_OfficialRate) VALUES (%s, %s, %s, %s) \
ON DUPLICATE KEY UPDATE Cur_Abbreviation = VALUES(Cur_Abbreviation), Cur_Scale = VALUES(Cur_Scale), \
Cur_Name = VALUES(Cur_Name), Cur_OfficialRate = VALUES(Cur_OfficialRate)
"""
try:
    cursor.executemany(q, itemsCourses)
    db.commit()
except:
    db.rollback()

def validate_currency(rates, requested_keys):
	keys = rates.keys()

	for key in requested_keys:
		if key not in keys:
			return False
	return True

def get_currency_by_abbr(courses, abbr):
    for currency in courses:
        res = validate_currency(currency, requested_keys)
        try:
            res = validate_currency(currency, requested_keys)
        except Exception as err:
            print("Enter the correct currency abbreviation" + {err})
        else:
            if res:
                if currency["Cur_Abbreviation"] == abbr:
                    return currency
current_rates = get_today_rates()

def answer():
    updates = get_updates(my_token)
    last_message = updates["result"][-1]
    chat_id = last_message["message"]["chat"]["id"]
    last_message_text = last_message["message"]["text"]
    default_answer = "Sorry I haven't answer!!!"


# logic message

    try:
        current_rates = get_today_rates()
        currency = get_currency_by_abbr(current_rates, abbr)
        if "/" in last_message_text and "rate" in last_message_text and abbr in last_message_text:
            current_rates = get_today_rates()
            currency = get_currency_by_abbr(current_rates, abbr)
    except TypeError as err:
        print("Enter the correct currency abbreviation" + {err})
        send_message(my_token, chat_id, default_answer)
    except UnboundLocalError as err:
        print("Enter the correct currency abbreviation" + {err})
        send_message(my_token, chat_id, default_answer)
    else:
        message = f"Course for today: {currency['Cur_OfficialRate']} BYN for {currency['Cur_Scale']}{abbr}"
        send_message(my_token, chat_id, message)

last_message_number = 0
while True:
    updates = get_updates(my_token)
    message_id = updates["result"][-1]["message"]["message_id"]

    if message_id > last_message_number:
        answer()
        last_message_number = message_id