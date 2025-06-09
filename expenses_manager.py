import datetime

class ExpensesManager:
    """
    Manages all business logic related to expenses.
    This includes recording new expenses and retrieving historical expense records.
    It primarily interacts with the DatabaseManager.
    """
    def __init__(self, db_manager):
        """
        Initializes the ExpensesManager with an instance of DatabaseManager.
        """
        self.db_manager = db_manager

    def add_expense(self, category, description, amount):
        """
        Records a new expense in the database.
        Returns a tuple: (True/False, "message")
        """
        if not category or not amount:
            return False, "Category and amount are required for an expense."
        try:
            amount = float(amount)
            if amount <= 0:
                return False, "Expense amount must be positive."
        except ValueError:
            return False, "Invalid amount. Please enter a number."

        current_date = datetime.date.today().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        success = self.db_manager.add_expense(
            current_date, current_time, category, description, amount
        )

        if success:
            return True, f"Expense for '{category}' (₱ {amount:,.2f}) recorded successfully."
        else:
            return False, "Failed to record expense due to a database error."

    def get_expenses_by_date_range(self, start_date=None, end_date=None):
        """
        Retrieves historical expense logs within a specified date range.
        If no dates are provided, it retrieves logs for the current day.
        Returns a list of dictionaries representing expense log entries.
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

        expenses = self.db_manager.get_expenses_by_date_range(start_date, end_date)
        return expenses

    def format_currency(self, amount):
        """
        Helper method to format a numeric amount as Philippine Peso (₱).
        """
        return f"₱ {amount:,.2f}"
