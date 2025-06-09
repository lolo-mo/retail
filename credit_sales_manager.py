import datetime

class CreditSalesManager:
    """
    Manages all business logic related to credit sales, including
    recording new credit sales, managing payments, and retrieving credit accounts.
    """
    def __init__(self, db_manager):
        """
        Initializes the CreditSalesManager with an instance of DatabaseManager.
        """
        self.db_manager = db_manager

    def add_credit_sale(self, sale_id, customer_name, original_amount, balance, status, due_date=None):
        """
        Adds a new credit sale record to the database.

        Args:
            sale_id (int): The ID of the associated sales transaction.
            customer_name (str): The name of the customer who bought on credit.
            original_amount (float): The total amount of the sale at the time of credit.
            balance (float): The initial outstanding balance (usually same as original_amount for new sales).
            status (str): Initial status, e.g., 'Unpaid'.
            due_date (str, optional): The due date for the credit (YYYY-MM-DD). Defaults to None.

        Returns:
            tuple: (bool, str) - Success status and a message.
        """
        if not customer_name:
            return False, "Customer name cannot be empty for credit sales."
        if original_amount <= 0:
            return False, "Original amount must be positive for credit sales."
        
        # Ensure balance is consistent with original_amount for new credit sales
        # Or you can let the caller define balance if partial credit is allowed
        # For now, we assume balance is always the original_amount on creation
        # The database already handles this for new credit sales, so we just pass it.

        success = self.db_manager.add_credit_sale(
            sale_id, customer_name, original_amount, balance, status, due_date
        )
        if success:
            return True, "Credit sale recorded successfully."
        else:
            return False, "Failed to record credit sale."

    def record_credit_payment(self, credit_id, amount_paid):
        """
        Records a payment towards a credit sale and updates the balance and status.

        Args:
            credit_id (int): The ID of the credit sale to update.
            amount_paid (float): The amount of payment received.

        Returns:
            tuple: (bool, str) - Success status and a message.
        """
        if amount_paid <= 0:
            return False, "Payment amount must be positive."

        success = self.db_manager.update_credit_sale_payment(credit_id, amount_paid)
        if success:
            return True, "Payment recorded and credit balance updated."
        else:
            return False, "Failed to record payment or update credit sale."

    def get_all_credit_sales(self):
        """
        Retrieves all credit sales records from the database.
        Returns a list of dictionaries.
        """
        return self.db_manager.get_all_credit_sales()

    def get_unpaid_credit_sales(self):
        """
        Retrieves all credit sales that are 'Unpaid' or 'Partially Paid'.
        Returns a list of dictionaries.
        """
        return self.db_manager.get_unpaid_credit_sales()

    def get_credit_sales_by_customer(self, customer_name):
        """
        Retrieves credit sales for a specific customer.
        Returns a list of dictionaries.
        """
        return self.db_manager.get_unpaid_credit_sales(customer_name=customer_name)
