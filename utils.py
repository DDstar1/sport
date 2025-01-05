from datetime import datetime, timedelta
import json
import os
import traceback
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import time
import aiohttp
import asyncio
import pyautogui

BASE_DIR = r"C:\Users\Administrator\Desktop\sporty-main (080) test"


def login(driver, phone, paswd):
    try:
        mobile_input = driver.find_element(By.CSS_SELECTOR, 'input[type="tel"].m-input-wap')
        password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"].m-input-wap')

        # Perform actions with the element if needed
        mobile_input.send_keys(phone)
        password_input.send_keys(paswd)
        
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[data-op="login-btn"]')
        login_button.click() 

        time.sleep(2)
    except :
        print('couldnt log in')



def make_sure_website_up(driver):
    try: 
        disconnect_message = driver.find_element(By.CSS_SELECTOR, "app-disconnect-message")
        driver.refresh()
        if(disconnect_message):
            driver.refresh()
    except: 
        pass



def get_multipliers(driver):
    multiplier_list = []

    multipliers = driver.find_elements(By.CSS_SELECTOR, "div.payouts-block app-bubble-multiplier")[:3]
    for e in multipliers:
        text_num = e.text.split('x')[0]
        if text_num != "":
            multiplier_list.append(text_num)

    return multiplier_list

def is_multipliers_safe(driver, multiplier_range, threshold):
    multiplier_list = []

    multipliers = driver.find_elements(By.CSS_SELECTOR, "div.payouts-block app-bubble-multiplier")[:multiplier_range]
    for e in multipliers:
        text_num = e.text.split('x')[0]
        if text_num != "":
            multiplier_list.append(float(text_num))  # Convert to float for comparison
    
    # Return True only if all values are greater than the threshold
    return all(multiplier > threshold for multiplier in multiplier_list)



async def send_telegram_msg(msg):
    token = "7383529443:AAHztCuaDFvQ2_KU9Vl7dqsQ82E-6jLsqq4"
    gc_id = '-1002160352322'
    # gc_id = '6966902490'
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={gc_id}&text={msg}&allow_sending_without_reply=True"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
    except Exception as e:
        print(e)


# def send_telegram_msg_2(msg):
#     token = "7383529443:AAHztCuaDFvQ2_KU9Vl7dqsQ82E-6jLsqq4"
#     # gc_id = '6966902490'
#     gc_id = '-1002160352322'
#     url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={gc_id}&text={msg}&allow_sending_without_reply=True"

#     requests.get(url)



def send_telegram_msg_2(msg):
    token = "7383529443:AAHztCuaDFvQ2_KU9Vl7dqsQ82E-6jLsqq4"
    gc_id = '-1002160352322'
    
    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
    pin_url = f"https://api.telegram.org/bot{token}/pinChatMessage"
    
    try:
        # Send the message
        send_response = requests.post(send_url, json={"chat_id": gc_id, "text": msg, "allow_sending_without_reply": True})
        send_response_data = send_response.json()
        message_id = send_response_data['result']['message_id']
        
        # Pin the message
        pin_response = requests.post(pin_url, json={"chat_id": gc_id, "message_id": message_id, "disable_notification": False})
        return pin_response.json()
    except Exception as e:
        print(e)

   



def input_stake(driver, num):
    try:
        # Locate the input field
        stake_input = driver.find_element(By.CSS_SELECTOR, "app-spinner input")
        current_value = stake_input.get_attribute("value")

        # If the current value matches the desired value, return early
        if float(current_value) == float(num):
            print('Stake already correct')
            return
        
        # Otherwise, clear and set the new value
        driver.execute_script("arguments[0].select();", stake_input)
        stake_input.send_keys(f"{num}")
    except Exception as e:
        print(f"error from input_stake, Element not interactable: {e}")





def make_sure_auto_close(driver, sl=2):

    def click_auto_button():
        """
        Ensures the 'Auto' button is clickable and clicks it.
        """
        try:
            # Locate the 'Auto' button
            auto_element_switcher = driver.find_element(By.CSS_SELECTOR, "div.cash-out-switcher div.input-switch")
            try:
                auto_element_switcher.click()
            except Exception as e:
                print("Element click intercepted, attempting to click using JavaScript.")
                driver.execute_script("arguments[0].click();", auto_element_switcher)
            print("'Auto' button clicked successfully.")
        except Exception as e:
            print("Error clicking 'Auto' button:", traceback.format_exc())


    while True:
        try:
            auto_element = driver.find_element(By.XPATH, "//button[contains(text(), 'Auto')]")
            # print('attempting to auto close')
            class_attribute = auto_element.get_attribute("class")

            if "active" not in class_attribute.split():
                # Wait for the 'Auto' button to be clickable
                auto_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Auto')]"))
                )
                auto_element.click()

                auto_element_switcher = driver.find_element(By.CSS_SELECTOR, "div.cash-out-switcher div.input-switch")
                class_atrr = auto_element_switcher.get_attribute("class")

                if "off" in class_atrr.split():
                    click_auto_button()

            # Recheck the switch state
            auto_element_switcher = driver.find_element(By.CSS_SELECTOR, "div.cash-out-switcher div.input-switch")
            class_atrr = auto_element_switcher.get_attribute("class")
            if "off" not in class_atrr.split():
                print("Switch successfully toggled.")

            auto_element_input = driver.find_element(By.CSS_SELECTOR, "div.spinner.small input")
            current_value = auto_element_input.get_attribute("value")

            if float(str(current_value).strip()) != float(sl):
                driver.execute_script("arguments[0].select();", auto_element_input)
                auto_element_input.send_keys(f"{sl}")
                print(f"Stop loss set to {sl}.")
            else:
                print(f"Stop loss is already set to {sl}. No need to change it.")

            current_value = auto_element_input.get_attribute("value")
            class_atrr = auto_element_switcher.get_attribute("class")  # Recheck the switch state
            if float(str(current_value).strip()) == float(sl) and "off" not in class_atrr.split():
                print(f"Stop loss successfully set to {sl}, and switch is in the correct state.")
                break
            else:
                print(f"Current stop loss value: {current_value} or switch not toggled. Retrying in 5 seconds...")
                click_auto_button()
                time.sleep(5)
        except Exception as loop_error:
            print("Error during loop iteration:", traceback.format_exc())
            time.sleep(1)
    
def click_bet_button(driver):
    try:
        while True:
            # Wait for the buttons to be present
            buttons = WebDriverWait(driver, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.btn.btn-success.bet.ng-star-inserted"))
            )
            if len(buttons) == 2:
                # Wait for the first button to be clickable
                try:
                    WebDriverWait(driver, 30).until(EC.element_to_be_clickable(buttons[0])).click()
                except Exception as e:
                    print("Element click intercepted.")
                    # continue
                # time.sleep(10)
                else:
                    pass
                    break
                    
    except Exception as e:
        print(f"Error from click_bet_button: {e}")
       


    
def click_cancel_button(driver):
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn.btn-danger.bet.height-70.ng-star-inserted")
        buttons[0].click()
        return True
    except Exception as e:
        # print(traceback.format_exc())
        print("error from click_cancel_button")
        return False


def check_for_invalid_input_stake(driver, correct_stake):
    try:
        stake_input = driver.find_element(By.CSS_SELECTOR, "app-spinner input")
        print(f"current stake value is {stake_input.get_property('value')}")
        if int(float(stake_input.get_property('value'))) != int(correct_stake):
            click_cancel_button(driver)
    except Exception as e:
        print(f"Error from input_stake: {e}")


def get_bet_history_losses(driver):
    bet_history_element = driver.find_element(By.XPATH, "//button[contains(text(), 'My Bets')]")
    bet_history_element.click()
    
    try:
        betHistory = driver.find_element(By.CSS_SELECTOR, "div.h-100.scroll-y")
        betHistory_text = betHistory.text
        betHistory_text = betHistory_text.replace(" ", "").replace("\n", "")
        # print(betHistory_text)
        # input('text is')
        lastbetElement = driver.find_element(By.CSS_SELECTOR, "app-bet-item")
    except:
        betHistory_text = None
        lastbetElement = None
         
    return betHistory_text, lastbetElement




def is_last_2_bet_history_set(list):
     if(len(list) < 2):
        return False
     else:
        time1 = datetime.strptime(list[0], '%H:%M')
        time2 = datetime.strptime(list[1], '%H:%M')
        time_difference = abs((time2 - time1).total_seconds())
        if time_difference <= 300:
            print("The times are less than 5 minutes apart.")
            return True
        else:
            print("The times are more than 5 minutes apart.")
            return False


def get_money_balance(driver):
    balance = driver.find_element(By.CSS_SELECTOR, "span.amount.font-weight-bold")
    balance_text =balance.text.replace(',', '')
    print(f'balance is {balance_text}')
    return float(balance_text)

                            

# button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-success.bet.ng-star-inserted")
# # class="btn btn-success bet ng-star-inserted"              bet button
# # class="btn btn-warning cashout ng-star-inserted"          cashout button
# # class="btn btn-danger bet height-70 ng-star-inserted"     waiting button 

def get_trade_elements(element, stake_list):
    date_element = element.find_element(By.CLASS_NAME, "date")
    date_text = date_element.text.strip()

    # Extract the bet amount
    bet_amount_element = element.find_element(By.TAG_NAME, "app-bet-amount")
    bet_amount_text = bet_amount_element.text.strip()
    bet_amount_text = float(bet_amount_text.replace(',', ''))

    # Extract the multiplier
    multiplier_element = element.find_element(By.CLASS_NAME, "bubble-multiplier")
    multiplier_text = multiplier_element.text.strip()
    multiplier_text = multiplier_text.split("x")[0]
    multiplier_text = float(multiplier_text)

    # Extract the cash-out amount
    try:
        result = element.find_element(By.CLASS_NAME, "cash-out")
        result = result.text.strip()
        result = float(result.replace(',', ''))
        result = result - bet_amount_text
        
    except Exception as e:
        # print(e)
        # input("Error from get_trade_elements")
        result = f"-{bet_amount_text}"
        result = float(result)

    try:
        curr_stk_indx = stake_list.index(bet_amount_text)
    except:
        curr_stk_indx = 0



    bet_item_data = {
            "date": date_text,
            "bet_amount": bet_amount_text,
            "multiplier": multiplier_text,
            "curr_stk_indx":curr_stk_indx,
            "result": result
        }
    
    return bet_item_data
            

def has_mins_passed(last_bet_time, check_secs):
    if(last_bet_time == False):
        return False
    current_time = datetime.now()
    # Check if the current time is more than 2 minutes ahead of the given time
    if current_time > last_bet_time + timedelta(seconds=check_secs):
        print('seconds passed')
        return True
    else:
        print(' seconds havent passed yet')
        return False



async def screenshot_and_send_to_telegram(driver, msg_id=None ,caption=""):
    try:
        # Take a screenshot of the browser
        screenshot = driver.get_screenshot_as_png()
        screenshot_path = os.path.join(os.getcwd(), "screenshot.png")
        with open(screenshot_path, "wb") as file:
            file.write(screenshot)
        # screenshot = pyautogui.screenshot()
        # screenshot_path = os.path.join(os.getcwd(), "screenshot.png")
        # screenshot.save(screenshot_path)

        print(f"Screenshot saved to: {screenshot_path}")

        # Send the screenshot to Telegram
        token = "7383529443:AAHztCuaDFvQ2_KU9Vl7dqsQ82E-6jLsqq4"
        gc_id = '-1002160352322'
        url = f"https://api.telegram.org/bot{token}/sendPhoto"

        # Asynchronous HTTP request to send the photo
        async with aiohttp.ClientSession() as session:
            with open(screenshot_path, 'rb') as photo:
                payload = {'chat_id': gc_id,
                           'photo': photo,  
                           "caption": caption or "",
                            "allow_sending_without_reply": 'true',}
                if msg_id:
                    payload["reply_to_message_id"] = f"{msg_id}"
               
                async with session.post(url, data=payload ) as response:
                    if response.status == 200:
                        print("Screenshot successfully sent to Telegram!")
                    
                    else:
                        print(f"Failed to send screenshot to Telegram. Error: {await response.text()}")

    except Exception as e:
        print(f"An error occurred while taking a screenshot or sending it to Telegram: {e}")
        await send_telegram_msg(f"Error sending Screenshot to Telegram: {str(e)}")



def is_new_tele_cmd(last_update_id):
    try:
        token = "7383529443:AAHztCuaDFvQ2_KU9Vl7dqsQ82E-6jLsqq4"
        url = f"https://api.telegram.org/bot{token}/getUpdates?limit=50"

        response = requests.get(url, verify=False).text
        PyRes = json.loads(response)


        # sets latest ID into database latestID table if new update is greater
        ResultBody = PyRes["result"][-1]

        print(ResultBody)


        new_updateID = int(ResultBody["update_id"])
        message = ResultBody["message"]["text"]
        message_id = ResultBody["message"]["message_id"]


        if(last_update_id == new_updateID):
            return False
        elif(message in ['/getresults','/getresults@sporty_7_bot']):
            with open("logs\\update_id.txt", "w") as file:
                file.write(str(new_updateID))
            return { 'msg_id':message_id }
    except Exception as e:
        print(f"Error getting latest Id {e}")
        return False

