import sqlite3
from datetime import datetime, timedelta
from utils import BASE_DIR

# Connect to the database (or create a new one if it doesn't exist)
conn = sqlite3.connect(f"{BASE_DIR}\\data.db")
big_conn = sqlite3.connect("big_data.db")

# Create a table named 'data' with columns for date (text) and number (real)
conn.execute("""CREATE TABLE IF NOT EXISTS data (
                  date TEXT,
                  number REAL
                )""")


# Create the 'trade' table
conn.execute("""CREATE TABLE IF NOT EXISTS trade (
    date TEXT,
    stake REAL,
    multiplier REAL,
    result TEXT,
    curr_stk_indx,
    next_stk_indx REAL    
)
""")


# Function to insert data into the table
def insert_data(date, number):
  cursor = conn.cursor()
  cursor.execute("INSERT INTO data (date, number) VALUES (?, ?)", (date, number))
  conn.commit()


def insert_trade(date, stake, multiplier, result, curr_stk_indx, next_stk_indx):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trade (date, stake, multiplier, result, curr_stk_indx, next_stk_indx) VALUES (?, ?, ?, ?, ?, ?)", (date, stake, multiplier, result, curr_stk_indx, next_stk_indx))
    conn.commit()


def get_all_numbers(use_big_data =False):
    if(use_big_data ==True):
        cursor = big_conn.cursor()
    else:
        cursor = conn.cursor()
    cursor.execute("SELECT number FROM data")
    rows = cursor.fetchall()
    numbers = [row[0] for row in rows]
    return numbers

def get_all_numbers_and_date(use_big_data =False):
    if(use_big_data ==True):
        cursor = big_conn.cursor()
    else:
        cursor = conn.cursor()
    cursor.execute("SELECT * FROM data")
    rows = cursor.fetchall()
    return rows


def is_there_two_consecutive_losses():
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT result FROM trade ORDER BY ROWID DESC LIMIT 2")
        results = cursor.fetchall()
        if len(results) == 2 and results[0][0] == 'loss' and results[1][0] == 'loss':
            print('There were consecutive losses')
            return True
        else:
            print('')
            return False
    except Exception as e:
        print(f" db error is coming from 2 consecutive losses")
        return False
    
def has_6_consecutive_losses_passed():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT number FROM data ORDER BY ROWID DESC LIMIT 3")
        results = cursor.fetchall()
        values_list = [float(result[0]) for result in results]

        print(f"reuslts of consecutive losses are {results}")
        
        if all(value < 2 for value in values_list):
            print('6 consecutive losses have passed')
            return True
        else:
            print('6 losses havent passed yet')
            return False
            
    except Exception as e:
        print(f" db error is coming from 3 consecutive losses {e}")
        return False

def get_results(use_big_data=False):
    cursor = conn.cursor()

    cursor.execute("SELECT result FROM trade")
    results = cursor.fetchall()
    numbers = [float(row[0]) for row in results ]

    profit = 0
    for i in numbers:
        profit += i
        
    return profit



def get_latest_next_stk_indx():
    cursor = conn.cursor()
    cursor.execute("SELECT next_stk_indx FROM trade ORDER BY ROWID DESC LIMIT 1")
    result = cursor.fetchone()
    if(result == None):
        return 0
    else:
        print(f'Next stake is {result[0]}')
        return int(result[0])


def is_loss_trade_set():
    cursor = conn.cursor()
    cursor.execute("SELECT result, curr_stk_indx FROM trade ORDER BY ROWID DESC LIMIT 2")
    results = cursor.fetchall()

    values_list = [float(result[1]) for result in results]  # Extract next_stk_indx values as floats
    result_list = [float(result[0]) for result in results]  # Extract result values
    
    print(f"values_list is {values_list}")
    print(f"result_list is {result_list}")

    # Check if both results are 'loss' and if sum of next_stk_indx is in [1, 5, 9]
    if (all(float(result) < 0 for result in result_list) and int(sum(values_list)) in [1, 5, 9]):
        return True
    else:
        return False


def is_last_trade_gt_10s():
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM trade")
    try:
        last_date_result = cursor.fetchone()[0].split('.')[0]
    except:
        return True
    last_date = datetime.strptime(last_date_result, "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    time_difference = current_time - last_date

    # Check if the time difference is more than 65 seconds
    if time_difference > timedelta(seconds=10):
        return True
    else:
        return False
    
def get_last_stake_and_result():
    cursor = conn.cursor()
    
    # Execute the query to select the last stake and result based on the date
    cursor.execute("""
        SELECT stake, result
        FROM trade 
        ORDER BY date DESC 
        LIMIT 1
    """)
    
    # Fetch the result
    result = cursor.fetchone()
    print(result)
        
    # Return a dictionary with the stake and result, or None if no result
    if result:
        return {"stake": float(result[0]), "result": float(result[1])}
    else:
        return {"stake": None, "result": None}
        