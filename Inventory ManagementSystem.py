import mysql.connector
from datetime import datetime, timedelta

# connect to MySQL database
mydb = mysql.connector.connect(
  host="localhost",
  user="username",
  password="password",
  database="canteen_inventory"
)

# create cursor object to execute SQL queries
mycursor = mydb.cursor()

# create table for inventory
mycursor.execute("CREATE TABLE IF NOT EXISTS inventory (id INT AUTO_INCREMENT PRIMARY KEY, item_name VARCHAR(255), quantity INT, price DECIMAL(10, 2))")

# create table for sales
mycursor.execute("CREATE TABLE IF NOT EXISTS sales (id INT AUTO_INCREMENT PRIMARY KEY, item_name VARCHAR(255), quantity INT, price DECIMAL(10, 2), sale_date DATETIME)")

# add initial inventory data
inventory_data = [
    ("paneer kulcha", 50, 2.99),
    ("coffee", 100, 1.99),
    ("sandwich", 75, 3.99)
]
sql = "INSERT INTO inventory (item_name, quantity, price) VALUES (%s, %s, %s)"
mycursor.executemany(sql, inventory_data)
mydb.commit()

# add initial sales data
sale_data = [
    ("paneer kulcha", 10, 2.99, datetime.now()),
    ("coffee", 15, 1.99, datetime.now()),
    ("sandwich", 5, 3.99, datetime.now())
]
sql = "INSERT INTO sales (item_name, quantity, price, sale_date) VALUES (%s, %s, %s, %s)"
mycursor.executemany(sql, sale_data)
mydb.commit()

# define function to calculate forecasted inventory for next 7 days
def calculate_forecasted_inventory():
    # get current inventory data
    sql = "SELECT item_name, quantity, price, date_added FROM inventory"
    mycursor.execute(sql)
    inventory = mycursor.fetchall()

    # calculate average daily sales for each item in inventory
    daily_sales = {}
    for item in inventory:
        item_name = item[0]
        quantity = item[1]
        price = item[2]
        date_added = item[3]
        sql = "SELECT SUM(quantity) FROM sales WHERE item_name = %s AND sale_date >= %s"
        date_7_days_ago = datetime.now() - timedelta(days=7)
        mycursor.execute(sql, (item_name, date_7_days_ago))
        total_sales = mycursor.fetchone()[0] or 0
        average_sales_per_day = total_sales / 7
        daily_sales[item_name] = average_sales_per_day

    # calculate forecasted inventory for next 7 days
    forecasted_inventory = {}
    for item in inventory:
        item_name = item[0]
        quantity = item[1]
        price = item[2]
        date_added = item[3]
        daily_sales_for_item = daily_sales[item_name]
        forecasted_quantity = quantity - (daily_sales_for_item * 7)
        if forecasted_quantity < 0:
            forecasted_quantity = 0
        forecasted_inventory[item_name] = forecasted_quantity

    return forecasted_inventory

# define function to retrieve inventory data
def get_inventory_data():
    # create a cursor object
    mycursor = mydb.cursor()

    # retrieve inventory data from the database
    mycursor.execute("SELECT * FROM inventory")

    # fetch all rows
    rows = mycursor.fetchall()

    # return the rows as a list of dictionaries
    inventory_data = []
    for row in rows:
        inventory_data.append({
            "id": row[0],
            "item_name": row[1],
            "quantity": row[2],
            "price": row[3]
        })

    return inventory_data
def print_report():
    # retrieve inventory data
    inventory_data = get_inventory_data()

    # retrieve total sales for each item in inventory
    sql = "SELECT item_name, SUM(quantity), SUM(price*quantity) FROM sales GROUP BY item_name"
    mycursor.execute(sql)
    sales_data = mycursor.fetchall()
    total_sales = {item[0]: (item[1], item[2]) for item in sales_data}

    # print report header
    print("Inventory Report")
    print("{:<20}{:<10}{:<10}{:<10}".format("Item", "Quantity", "Price", "Total Sales"))
    print("-" * 50)

    # print inventory data and total sales
    for item in inventory_data:
        item_name = item["item_name"]
        quantity = item["quantity"]
        price = item["price"]
        if item_name in total_sales:
            sales_quantity, sales_amount = total_sales[item_name]
        else:
            sales_quantity, sales_amount = 0, 0
        print("{:<20}{:<10}{:<10}{:<10}".format(item_name, quantity, price, sales_amount))

    # print report footer with total sales
    total_sales_amount = sum([item[1][1] for item in total_sales.items()])
    print("-" * 50)
    print("{:<20}{:<10}{:<10}{:<10}".format("Total Sales", "", "", total_sales_amount))
