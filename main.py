from datetime import datetime, timedelta
import json
import os
import random
import time
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import db
from utils import BASE_DIR, is_new_tele_cmd, login, check_for_invalid_input_stake, screenshot_and_send_to_telegram, click_bet_button, click_cancel_button, get_bet_history_losses, get_multipliers, has_mins_passed, input_stake, get_trade_elements, make_sure_auto_close, make_sure_website_up, send_telegram_msg, get_money_balance,is_multipliers_safe, send_telegram_msg_2


import asyncio
import aiohttp

from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC




# Open the website
with open(f'{BASE_DIR}/demo_url.txt', 'r', encoding='utf-8') as file:
    sporty_demo_url = file.read()



def random_60_to_300():
    return random.randint(60, 120)

def get_current_stakes(starting_balance,curr_stake, threshold):
    num_increments = int(starting_balance // threshold)
    if(num_increments > 1):
        adjusted_stakes = [s * num_increments for s in curr_stake]
        return adjusted_stakes
    else: 
        return curr_stake
        
def execute_trade(driver, stake_amount):
    input_stake(driver, num=stake_amount)
    make_sure_auto_close(driver)
    click_bet_button(driver)
    # print("Pausing for 20 seconds")
    # time.sleep(20)


def log_bet_history(betHistory_text, lastbetElement):
    # Convert None values to "null" for logging purposes
    log_betHistory_text = betHistory_text if betHistory_text is not None else "null"
    log_lastbetElement_text = lastbetElement.text if lastbetElement is not None else "null"

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append to log.txt
    with open("logs\\bet_history_log.txt", "a") as log_file:
        log_file.write(f"Timestamp: {timestamp}\n")
        log_file.write(f"Bet History: {log_betHistory_text}\n")
        log_file.write(f"Last Bet Element: {log_lastbetElement_text}\n")
        log_file.write("\n")  # Optional: Add a new line for readability


def log_list_of_dicts_to_file(filename, dict_list):
    with open(filename, "a") as file:
        # Combine all dictionaries into a single formatted string for one line
        formatted_line = "      ".join([
            f"{key}: {value.strftime('%H:%M:%S') if isinstance(value, datetime) else value}"
            for dictionary in dict_list
            for key, value in dictionary.items()
        ])
        file.write(formatted_line + "\n")




# with open('main_page.html', 'w', encoding='utf-8') as file:
#     file.write(driver.page_source)

async def main_loop():
    # global frame_switched,skip_until, stale_element_counter, old_multipliers, old_bet_his_text, can_trade, get_next_mutiplier, wait_for_6_losses_to_pass, stake_index, old_last_element_date, old_balance, last_inserted_trade,last_loss_time

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # To run Chrome in headless mode (no GUI)

    driver = webdriver.Chrome(options=chrome_options)
    # Get the screen width and height
    screen_width = driver.execute_script("return window.screen.width;")
    screen_height = driver.execute_script("return window.screen.height;")
    # Calculate the desired window width (70% of the screen width)
    desired_width = int(screen_width * 0.9)
    # Set the browser window to 70% of the screen's width and full height
    driver.set_window_size(desired_width, screen_height)


 
    driver.get(sporty_demo_url)

    # input("login now ?")
    time.sleep(3)
    login(driver, 8151725194, 'spcapmarvel7S')
    # login(driver, 7052109432, 'spcapmarvel7S')
    





    SCRIPT_STARTED = datetime.now()
    Send_update_time= datetime.now()

    skip_until = None
    old_multipliers = []
    old_bet_his_text = None
    can_trade = True


    # initial_stake = [10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240]
    initial_stake = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 22,  23, 24, 25]


    # stakes = [10,10]
    # stakes = [10, 15, 30, 60, 120, 240, 480, 960, 1200 ]
    # stakes = [10, 20, 30, 40, 60, 90, 140, 210, 310, 470, 700 ]

    # stakes = [10, 12, 25, 53,112,240]

    last_loss_time =datetime.now()
    last_win_time =datetime.now()
    last_get_history_time = 0 # datetime.now()
    frame_switched = False
    aux_can_trade = ' '
    next_stk_indx = 0
    stale_element_counter = 0

    # send_telegram_msg_2("Server is almost expired, going back to test mode")


    await send_telegram_msg('Server has started')


    # input(f'\nAwaiting Admin Confirmation\n')

    while True:
        try:
            try:
                if(frame_switched != True):
                    driver.switch_to.default_content()

                    first_iframe = driver.find_element(By.CSS_SELECTOR, "iframe#turbo-games\/aviator")
                    driver.switch_to.frame(first_iframe)

                    second_iframe = driver.find_element(By.CSS_SELECTOR, "iframe.turbo-games-iframe")
                    driver.switch_to.frame(second_iframe)

                    print(f'iframe is {second_iframe}')
                    frame_switched = True
                    
            except Exception as e:
                print('no frame')
                print(traceback.format_exc())
                continue

        
            try:
                print(f'my money balance is {get_money_balance(driver)}')
                print(f"The next index is {next_stk_indx}")
            except Exception as e:
                # await send_telegram_msg('Server should be restarted')
                # time.sleep(600)
                if datetime.now() - SCRIPT_STARTED > timedelta(hours=1):
                    await send_telegram_msg('Restarting Script')
                    # os.system('shutdown /r /t 1 /c "System maintenance required"')
                    driver.quit()
                    break

            # stakes = get_current_stakes(get_money_balance(driver), initial_stake, 500)
            stakes = initial_stake


            print('---------------------1-------------------')
            print(f"The next index is {next_stk_indx}")


            if old_multipliers == []:
                old_multipliers = get_multipliers(driver)

            try:
                new_multipliers = get_multipliers(driver)              
                
                if new_multipliers[:2] != old_multipliers[:2]:
                    old_multipliers = new_multipliers
                    if len(old_multipliers) > 5:
                        old_multipliers.pop()
                    db.insert_data(date=datetime.now(), number=new_multipliers[0])
                    # await send_telegram_msg('Still inserting in db')
            except:
                print("stale multiplier elements")
                stale_element_counter += 1
                if(stale_element_counter >= 5):
                    stale_element_counter = 0
                    driver.refresh()
                pass




            print('---------------------2-------------------')
            print(f"The next index is {next_stk_indx}")



            new_bet_his_text, last_element_history = get_bet_history_losses(driver)
            if last_get_history_time >= 2:
                print("last_get_history_time has passed 2")
            else:
                print(f"last_get_history_time hasnt passed 2 yet still, {last_get_history_time}")
                last_get_history_time += 1
                last_element_history = None
                new_bet_his_text = None
                continue
           

            if last_element_history is not None and (old_bet_his_text != new_bet_his_text)  :

                elements = get_trade_elements(last_element_history, stake_list=stakes)
                log_bet_history(new_bet_his_text, last_element_history)

                print(f"old_bet_his_text == new_bet_his_text ({old_bet_his_text == new_bet_his_text})")
                print(f"last result is {float(elements['result'])}, and greater checker is ({float(elements['result']) > 0}) ")
                print(f"next index in 2,1 is {next_stk_indx}")

                old_bet_his_text , last_element_history = get_bet_history_losses(driver)

                                    
                if(float(elements['result']) <= 0): 
                    next_stk_indx = int(elements["curr_stk_indx"]) + 1
                    if(next_stk_indx > len(stakes)-1):
                        next_stk_indx = 0
                        exit()

                    last_win_time = False
                    last_loss_time = datetime.now()
                    aux_can_trade = True
                    print(f'There was a loss here going to index{next_stk_indx}')

                    
                    with open("logs\\update_id.txt", "r") as file:
                        update_id = int(file.read().strip()) # Read and convert to integer
                        # tele_result = is_new_tele_cmd(update_id)
                        # if(tele_result != False):
                        print('sending pic to gc')
                        highest_stake_index, count = db.get_highest_curr_stk_indx_and_count()
                        await send_telegram_msg(f"Balance = {get_money_balance(driver)}     Profit = {float(get_money_balance(driver)) - float(18300)}")
                        await screenshot_and_send_to_telegram(driver, None, f"Highest stake so far is {initial_stake[highest_stake_index]} \nHappened {count} times")

              
                    

                else:
                    next_stk_indx = 0
                    execute_trade(driver, initial_stake[next_stk_indx])
                    print('Original button clicked')
                    skip_until = None
                    last_win_time  = datetime.now()
                    aux_can_trade = False

                
                print(f"next index in 2,2 is {next_stk_indx}")

                db.insert_trade(date=datetime.now(), stake=elements["bet_amount"], multiplier=elements["multiplier"], result=elements['result'], curr_stk_indx=elements['curr_stk_indx'],next_stk_indx=next_stk_indx)
                
                log_data = [
                        {"date": datetime.now()},
                        {"last_loss_time": last_loss_time},
                        {"last_win_time": last_win_time},
                        {"stake": elements["bet_amount"]},
                        {"multiplier": elements["multiplier"]},
                        {"result": elements["result"]},
                        {"curr_stk_indx": elements["curr_stk_indx"]},
                        {"next_stk_indx": next_stk_indx},
                        {"aux_can_trade": aux_can_trade},
                    ]
                log_list_of_dicts_to_file("logs\\Trade_log.txt", log_data)

                last_get_history_time = 0
                
                


            print('---------------------3-------------------')
            print(f"The next index is {next_stk_indx}")




            latest_multiplier = get_multipliers(driver)

            # if (has_mins_passed(last_loss_time,300)==False):
            # # if float(latest_multiplier) < 2 and skip_until != None:
            #     print(f'skipping trade cause 2mins havent passed yet')
            #     continue


# and float(latest_multiplier[0]) >
            if((aux_can_trade == True) and (has_mins_passed(last_loss_time,60)==True) and (float(latest_multiplier[0]) > 2) ):
                # execute_trade(driver, initial_stake[next_stk_indx])
                click_bet_button(driver)
                last_loss_time = datetime.now()
                print('Auxilliary button clicked')
            
            elif(aux_can_trade == False and (has_mins_passed(last_win_time,30)==True)):
                # execute_trade(driver, initial_stake[next_stk_indx])
                click_bet_button(driver)
                last_win_time = datetime.now()
                print('Auxilliary button clicked from staying too long')

            else:
                input_stake(driver, num=initial_stake[next_stk_indx])
                make_sure_auto_close(driver)

        

            print('---------------------4-------------------')
        except Exception as e:
            print(f"Error from main.py \n")
            print(traceback.format_exc())
            error_message = str(type(e).__name__)
            await send_telegram_msg(f"Bot Error \n\n {error_message}")


           
        

# Run the main loop
while True:
    asyncio.run(main_loop())
