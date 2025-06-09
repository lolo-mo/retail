import datetime

class StockLogManager:
    """
    Manages all business logic related to stock-in operations.
    This includes recording incoming stock and retrieving historical stock-in logs.
    It interacts with the DatabaseManager to store data and the InventoryManager
    to update product stock levels.
    """
    def __init__(self, db_manager, inventory_manager):
        """
        Initializes the StockLogManager with instances of DatabaseManager
        and InventoryManager.
        """
        self.db_manager = db_manager
        self.inventory_manager = inventory_manager

    def log_stock_in(self, item_no, quantity_added, supplier_name="", notes=""):
        """
        Records an incoming stock event and updates the product's current stock.
        Returns a tuple: (True/False, "message")
        """
        # Ensure quantity is a positive integer
        try:
            quantity_added = int(quantity_added)
            if quantity_added <= 0:
                return False, "Quantity added must be a positive number."
        except ValueError:
            return False, "Invalid quantity. Please enter a number."

        # Check if the item exists in inventory
        product = self.inventory_manager.get_product_by_item_no(item_no)
        if not product:
            return False, f"Item with Item No. '{item_no}' not found in inventory. Please add it first."

        current_date = datetime.date.today().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        # 1. Add the stock-in entry to the log table
        log_success = self.db_manager.add_stock_in_log(
            item_no, quantity_added, current_date, current_time, supplier_name, notes
        )

        if not log_success:
            return False, "Failed to record stock-in log entry."

        # 2. Update the product's current stock in the inventory
        stock_update_success = self.inventory_manager.update_stock(item_no, quantity_added)

        if not stock_update_success:
            # This is a critical scenario: log recorded, but stock not updated.
            # In a real-world system, you might want to log this discrepancy or attempt to revert.
            print(f"CRITICAL ERROR: Stock-in logged for {item_no} but inventory update failed.")
            return False, f"Stock-in logged, but failed to update inventory for '{product['item_name']}'. Please check manually."

        return True, f"Stock for '{product['item_name']}' successfully increased by {quantity_added}."

    def get_stock_in_history(self, start_date=None, end_date=None):
        """
        Retrieves historical stock-in logs within a specified date range.
        If no dates are provided, it retrieves logs for the current day.
        Returns a list of dictionaries representing stock-in log entries.
        """
        if start_date is None:
            start_date = datetime.date.today().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.date.today().strftime("%Y-%m-%d")

        # Ensure dates are in YYYY-MM-DD format
        try:
            datetime.datetime.strptime(start_date, "%Y-%m-%d")
            datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid date format. Dates must be YYYY-MM-DD.")
            return []

        logs = self.db_manager.get_stock_in_logs_by_date_range(start_date, end_date)

        # Enhance logs with item name for display purposes
        for log in logs:
            product_info = self.inventory_manager.get_product_by_item_no(log['item_no'])
            log['item_name'] = product_info['item_name'] if product_info else "Unknown Item"
        return logs

