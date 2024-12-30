import random
import traceback
import db
from datetime import datetime, timedelta

from strategy_func import analyze_number_list, highest_in_sets_of_three, max_consecutive_below_threshold, process_numbers

use_big_data = True

# stakes = [30, 360, 4020]
# stakes = [30, 210, 1320 ,8000]
# stakes = [16, 64, 224, 736, 2336, 7264]
# stakes = [20, 80, 280, 920, 2920, 9080]
# stakes = [50, 200, 700, 2300, 7300, 22700]
# stakes = [30, 210, 1320]
# stakes = [10, 14, 34, 82, 201]
# stakes = [30, 210, 1320]
# stakes = [16, 86, 400]
# stakes = [20, 15, 23, 34, 51, 77, 115, 178, 262, 393, 589]
# stakes = [20, 30, 60]
# stakes = [20, 21, 42]
stakes = [10,11,13,18,24,32,42,57,76,101,135,180,240,320,426,568,758,1010,1347,1796,2395,3193,4257,5676,7569,10092,13455,17940]
stakes = [10,110,1110]
# stakes = [10,200,2100,23200,255200]
# stakes = [10,11,15,23,34,51,77,115,173,259,389,583,875,1312,1968,2957,4436,6654] #,9981,14971, 22457, 33685, 50528
# stakes = [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200,210,220,230,240,250,260,270,280,290,300,310,320,330]
# stakes = [10,20,30,40,60,80,100,120]
# stakes = [10,30,50,70,90,110,130,150,170],
# stakes = [10, 11, 12, 13, 14, 15, 16, 17]
# stakes = [30, 14, 18, 24, 32, 40, 56, 72, 99,132,176,235,313, 417]
# stakes = [40,10, 13, 16, 20, 25, 31, 39, 49, 61, 76, 95, 119, 149, 186, 233, 291, 363, 454]
# stakes = [10, 15, 30, 60, 120]
# stakes = [20, 15, 23, 34, 51, 77, 115, 178, 262, 393, 589]
# stakes = [20, 20, 30, 48, 72, 110, 170]


# stakes = [10, 70 ]
# rows = db.get_all_numbers_and_date(use_big_data)1010

# multiplier_cash_out = 1.1
# multiplier_cash_out = 1.2

# Convert the string date to datetime object

losses = []
max_consecutive_times = []
skipped = 0
broke =0

def random_60_to_300():
    return random.randint(50, 100)

def skip_num():
    num = random.randint(1, 2)
    if(num==1):
        return True
    else:
        return False

# db_list = [ 'qq_data.db', 'aa_data.db']
# db_list = ['data.db', 'dd_data.db', 'md22data.db', 'dataff.db','databb.db','datacc.db','datazz.db']
db_list = ['data_1.db','data_0.db','data2.db','big_data.db',]
# db_list = ['big_data.db','data2.db','data.db', 'dd_data.db', 'md22data.db', 'dataff.db','databb.db','datacc.db','datazz.db','qq_data.db', 'aa_data.db']
# db_list = ['data2.db']
# db_list = ['big_data.db']
db_list = [
    'qq_data.db', 'aa_data.db', 
    'data.db', 'dd_data.db', 'md22data.db', 'dataff.db', 'databb.db', 'datacc.db', 'datazz.db', 
    'data_1.db', 'data_0.db', 'data2.db', 'big_data.db'
]

Balances = []
for j in range(0,200,3000):
    print(j)
    died = False
    for name in db_list:
        Balance = float(2000)
        # broke =0
        stake_index=0
        total_trade = 0
        skip_until = None
        loss_count = 0
        consecutive_loss = 0 
        multiplier_cash_out = 1.1
        wait_for_2= False

        rows = db.get_all_numbers_and_date_2(name)
        rows = [(datetime.strptime(g[0], '%Y-%m-%d %H:%M:%S.%f'), float(g[1])) for g in rows]
        multiplier_list = [i for _, i in rows]
        # print(multiplier_list)


        for index, (date, i) in enumerate(rows):
            # if(skip_num()==True):
            #     skipped +=1
            #     continue
            # else: 
            #     skipped -=1

            try:
                    # Skip iterations if we're still within the skip period
                if skip_until  and date < skip_until:
                    continue
                # if(wait_for_2==True):
                #     if(i>1.5 and multiplier_list[index-1]>1.5):
                #         # print(index, i,multiplier_list[index-1])
                #         wait_for_2 = False
                #     else:
                #         continue
        

                elif( i < multiplier_cash_out):
                    Balance -= stakes[stake_index]

                    stake_index += 1
                    total_trade +=1
                    # print(stake_index)

                    skip_until = date + timedelta(seconds=200)  # Skip next 5 minutes

                    consecutive_loss += 1
                    wait_for_2 = True

                    losses.append(stakes[stake_index])

                elif(i >= multiplier_cash_out):
                    Balance += (stakes[stake_index] * (multiplier_cash_out-1))
                    # Balance += (stakes[stake_index] * (multiplier_cash_out))
                    consecutive_loss = 0
                    stake_index = 0
                    total_trade +=1
                    skip_until = False

             

                if Balance < 100:
                    print(f"Balance dead at index {index}")
                    died = True
                    print(stake_index)
                    print(name)
                    # input('died here')

                    break
            
                if(stake_index > len(stakes)-1):
                    broke+=1
                    stake_index = 0
                
                
            except Exception as e:
                print(Balance)
                input("broke for db")
                print(f"Exception at index {index}: {e}")
                # input('dd')
                print(e)
                print(stake_index)
                # input('broke here')
                stake_index = 0
                broke +=1

        # print(f'Results for {name} ')
        # print(f"Balance is {Balance}")
        Balances.append(Balance)
        # print(db.get_results())
        #  print(total_trade)
        # if(broke>=1):
        #     print(f'Results for {name} ')
        #     print(f'broke {broke} times')
        max_streak = max_consecutive_below_threshold(multiplier_list, multiplier_cash_out)
        max_consecutive_times.append(max_streak[0])
        # print(f"The maximum consecutive times it was less than {multiplier_cash_out}: {max_streak[0]} at index {max_streak[1]}")
    if(died==True):
        # input("died here")
        pass

        

        # process_numbers(multiplier_list, threshold=100)

        # print(f'max consecutive times is {max_consecutive_below_threshold(multiplier_list, 2)} \n\n')
Balances.sort(reverse=True) 


print(Balances)

print(f'max Balance is {max(Balances)} \n min Balance is {min(Balances)}')
print(f"Max Loss is {max(losses)}")
print(f"Total Skip count is {skipped}")
print(f"The maximum consecutive times it was less than {multiplier_cash_out}:{max_consecutive_times}")

if(broke>=1):
    print(f'broke {broke} times')




# rows =db.get_all_numbers_and_date_2(db_list[0])
# rows = [(datetime.strptime(g[0], '%Y-%m-%d %H:%M:%S.%f'), float(g[1])) for g in rows]
# multiplier_list = [i for _, i in rows]




# print(db.get_results())

# max_set_result = highest_in_sets_of_three(prices)
# analyse = analyze_number_list(max_set_result)

# print(max_set_result, len(max_set_result), len(prices))  # Output: [7, 9, 8]




# def number_distribution(numbers):
#     above_1_1 = 0
#     less = 0
#     for i in numbers:
#         if i > 1.1:
#             above_1_1 += 1
#         else:
#             less += 1


#     return  above_1_1, less
    
# above_1_1, less = number_distribution(prices)
    
# print(f'above 1.1 == {above_1_1} \n less == {less}')


# def find_consecutive_sets(values):
#     consecutive_sets = []
#     count = 0
    
#     for i in range(len(values) - 1):
#         if values[i] < multiplier_cash_out and values[i+1] < multiplier_cash_out:
#             if count == 0:
#                 start_index = i
#             count += 1
#         else:
#             if count > 0:
#                 consecutive_sets.append((start_index, count + 1))
#                 count = 0
    
#     # Check if the last set reaches the end of the list
#     if count > 0:
#         consecutive_sets.append((start_index, count + 1))
    
#     total_sets = len(consecutive_sets)
#     return consecutive_sets, total_sets


# result, total_count = find_consecutive_sets(prices)

# print("Consecutive Sets:", result)
# print("Total Number of Sets:", total_count)
