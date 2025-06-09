import datetime

class ReportGenerator:
    """
    Generates various financial reports for the grocery store management system.
    It retrieves raw data from the DatabaseManager and performs calculations
    to summarize sales, costs, expenses, and profits over specified periods.
    """
    def __init__(self, db_manager):
        """
        Initializes the ReportGenerator with an instance of DatabaseManager.
        """
        self.db_manager = db_manager

    def _calculate_cogs_for_sales(self, sales_items):
        """
        Internal helper to calculate Cost of Goods Sold (COGS) from a list of sale items.
        """
        cogs = sum(item['quantity_sold'] * item['supplier_price_at_sale'] for item in sales_items)
        return cogs

    def generate_sales_report(self, start_date, end_date):
        """
        Generates a sales report for a specified date range.
        Calculates total revenue, Cost of Goods Sold (COGS), and gross profit.
        Returns a dictionary with sales metrics.
        """
        sales = self.db_manager.get_sales_by_date_range(start_date, end_date)
        all_sale_items = []
        total_revenue = 0.0

        for sale in sales:
            total_revenue += sale['total_amount']
            # Fetch sale items for each sale to calculate COGS
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale['sale_id'],))
            items_for_sale = cursor.fetchall()
            conn.close()
            all_sale_items.extend([dict(row) for row in items_for_sale])

        cogs = self._calculate_cogs_for_sales(all_sale_items)
        gross_profit = total_revenue - cogs

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'cogs': cogs,
            'gross_profit': gross_profit,
            'total_sales_transactions': len(sales),
            'currency_symbol': '₱'
        }

    def generate_expenses_report(self, start_date, end_date):
        """
        Generates an expenses report for a specified date range.
        Calculates the total amount spent on expenses.
        Returns a dictionary with expense metrics.
        """
        expenses = self.db_manager.get_expenses_by_date_range(start_date, end_date)
        total_expenses = sum(expense['amount'] for expense in expenses)

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_expenses': total_expenses,
            'total_expense_transactions': len(expenses),
            'currency_symbol': '₱'
        }

    def generate_financial_summary_report(self, start_date, end_date):
        """
        Generates a comprehensive financial summary report for a specified date range.
        Includes total sales, COGS, gross profit, total expenses, and net income.
        """
        sales_data = self.generate_sales_report(start_date, end_date)
        expenses_data = self.generate_expenses_report(start_date, end_date)

        net_income = sales_data['gross_profit'] - expenses_data['total_expenses']

        report = {
            'period_start': start_date,
            'period_end': end_date,
            'total_revenue': sales_data['total_revenue'],
            'cogs': sales_data['cogs'],
            'gross_profit': sales_data['gross_profit'],
            'total_expenses': expenses_data['total_expenses'],
            'net_income': net_income,
            'currency_symbol': '₱'
        }
        return report

    def get_cogs_per_item_today(self):
        """
        Calculates the Cost of Goods Sold (COGS) for items sold today,
        detailing it per item based on supplier price.
        Returns a list of dictionaries with item_name, quantity_sold, selling_price, supplier_price, total_cogs_item.
        """
        today_date = datetime.date.today().strftime("%Y-%m-%d")
        
        # Get all sales for today
        sales_today = self.db_manager.get_sales_by_date_range(today_date, today_date)
        
        cogs_details = {} # {item_no: {'item_name', 'total_qty_sold', 'total_selling_value', 'total_supplier_value'}}

        for sale in sales_today:
            conn = self.db_manager._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale['sale_id'],))
            items_for_sale = cursor.fetchall()
            conn.close()

            for item in items_for_sale:
                item_no = item['item_no']
                quantity_sold = item['quantity_sold']
                selling_price_at_sale = item['selling_price_at_sale']
                supplier_price_at_sale = item['supplier_price_at_sale']

                if item_no not in cogs_details:
                    # Get item name from products table for display
                    product_info = self.db_manager.get_product_by_item_no(item_no)
                    item_name = product_info['item_name'] if product_info else "Unknown Item"
                    cogs_details[item_no] = {
                        'item_name': item_name,
                        'quantity_sold': 0,
                        'total_selling_value': 0.0,
                        'total_supplier_value': 0.0 # This is the COGS for this item
                    }
                
                cogs_details[item_no]['quantity_sold'] += quantity_sold
                cogs_details[item_no]['total_selling_value'] += (quantity_sold * selling_price_at_sale)
                cogs_details[item_no]['total_supplier_value'] += (quantity_sold * supplier_price_at_sale)

        # Convert to a list of formatted dictionaries
        formatted_cogs_list = []
        for item_no, details in cogs_details.items():
            formatted_cogs_list.append({
                'item_no': item_no,
                'item_name': details['item_name'],
                'quantity_sold': details['quantity_sold'],
                'total_selling_value': details['total_selling_value'],
                'total_cogs_item': details['total_supplier_value']
            })
        return formatted_cogs_list

    def format_currency(self, amount):
        """
        Helper method to format a numeric amount as Philippine Peso (₱).
        """
        return f"₱ {amount:,.2f}"

