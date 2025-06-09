A simple python tkinter for grocery store management system.
Features:
1. Dashboard:
a. Real-time Metrics: Displays current date (Day, DD-MMM-YYYY) and time (AM/PM).
b. Inventory Valuation: Shows total inventory value based on both selling price and supplier price (cost).
c. Projected Profit: Calculates potential profit from current inventory.
d. Re-Order Cost: Shows the total cost needed to reorder items that are below their reorder level.
e. Sales Statistics: Provides daily, weekly, and monthly sales figures (collected revenue) and net profit.
f. Items Sold (COGS): Shows the Cost of Goods Sold based on selling price and supplier price per unit for items sold today.
2. Inventory Management:
a. Item Listing: Shows all your inventory items in a table with details like stock levels, prices, and re-order status.
b. Re-Order Alerts: Automatically flags items that are below their re-order level (default is 5) and suggests a re-order quantity.
c. Product Name or Item No. Search bar
d. import/export item list (.csv or .json)
e. 'Item No.', 'Item Name', 'Description', 'Unit', 'Supplier Price (Per Unit)', 'Selling Price', 'Current Stock', 'Re-Order' (Yes or No), 'Re-Order QTY'
3. POS
a. Easy & Faster Billing
b. Payment (Cash, Credit)
c. Product Name or Item No. Search bar
d. Currency: Philippine Peso (₱)
4. Stock In Log:
a. Records incoming stock (e.g., from suppliers).
b. Maintains a historical log of all stock-in transactions.
c. Add/Update/Delete Items: Allows you to manage individual product entries and automatically updates the main inventory.
d. Calculates the profit per item and suggests a selling price based on your cost.
5. Stock Out Log:
a. Records sales transactions (items moving out of stock) and automatically updates the main inventory.
b. Calculates the amount for each sale, including optional additional charges.
c. Keeps a detailed log of all sales.
6. Credit Sales:
a. Manages sales made on credit to customers (add, edit, delete)
b. Allows recording of deposits and tracking of paid/unpaid status.
c. Links credit sales to stock-out events.
7. Expenses:
a. Tracks daily expenses.
b. Provides a financial summary showing total expenses
c. profit from sales, daily, weekly and monthly
d. net income (profit minus expenses)
8. Reports:
a. Financial Reports: Generates daily, weekly, and monthly financial reports summarizing sales, COGS, gross profit, expenses, and net income.
b. Show profit from sales, daily, weekly and monthly
c. Net income (profit minus expenses)
