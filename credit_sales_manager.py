import datetime

class CreditSalesManager:
    """
    Manages all business logic related to credit sales.
    This includes recording new credit sales, processing payments against them,
    and retrieving credit sales records.
    It primarily interacts with the DatabaseManager.
    """
    def __init__(self, db_manager):
        """
        Initializes the CreditSalesManager with an instance of DatabaseManager.
        """
        self.db_manager = db_manager

    def add_credit_sale(self, sale_id, customer_name, original_amount, due_date=None):
        """
        Records a new credit sale in the database.
        Initializes balance to original_amount and status to 'Unpaid'.
        Returns a tuple: (True/False, "message")
        """
        if not customer_name or not original_amount:
            return False, "Customer name and original amount are required for a credit sale."
        if original_amount <= 0:
            return False, "Original amount must be positive for a credit sale."

        # Initial balance is the full amount, status is 'Unpaid'
        balance = original_amount
        status = 'Unpaid'

        success = self.db_manager.add_credit_sale(
            sale_id, customer_name, original_amount, balance, status, due_date
        )

        if success:
            return True, f"Credit sale for '{customer_name}' (₱ {original_amount:,.2f}) recorded successfully."
        else:
            return False, "Failed to record credit sale due to a database error."

    def record_credit_payment(self, credit_id, amount_paid):
        """
        Records a payment towards an existing credit sale, updates the balance and status.
        Returns a tuple: (True/False, "message")
        """
        try:
            amount_paid = float(amount_paid)
            if amount_paid <= 0:
                return False, "Payment amount must be positive."
        except ValueError:
            return False, "Invalid payment amount. Please enter a number."

        # Fetch the current credit sale details first
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM credit_sales WHERE credit_id = ?", (credit_id,))
            credit_sale = cursor.fetchone()
            if not credit_sale:
                return False, "Credit sale not found."
            credit_sale = dict(credit_sale) # Convert Row object to dictionary

            if credit_sale['status'] == 'Paid':
                return False, "This credit sale has already been fully paid."

            new_amount_paid = credit_sale['amount_paid'] + amount_paid
            new_balance = credit_sale['original_amount'] - new_amount_paid

            status = 'Unpaid'
            if new_balance <= 0:
                status = 'Paid'
                new_balance = 0.0 # Ensure balance doesn't go negative
            elif new_amount_paid > 0:
                status = 'Partially Paid'

            # Update the credit sale in the database
            cursor.execute('''
                UPDATE credit_sales
                SET amount_paid = ?, balance = ?, status = ?
                WHERE credit_id = ?
            ''', (new_amount_paid, new_balance, status, credit_id))
            conn.commit()

            return True, f"Payment of ₱ {amount_paid:,.2f} recorded for credit sale ID {credit_id}. New balance: ₱ {new_balance:,.2f}."

        except Exception as e:
            conn.rollback()
            print(f"Error recording credit payment: {e}")
            return False, f"An error occurred while recording payment: {e}"
        finally:
            conn.close()

    def get_all_credit_sales(self):
        """
        Retrieves all credit sales records from the database.
        Returns a list of credit sale dictionaries.
        """
        return self.db_manager.get_all_credit_sales()

    def get_unpaid_credit_sales(self):
        """
        Retrieves all credit sales that are 'Unpaid' or 'Partially Paid'.
        Returns a list of credit sale dictionaries.
        """
        return self.db_manager.get_unpaid_credit_sales()

    def delete_credit_sale(self, credit_id):
        """
        Deletes a credit sale record from the database.
        Use with caution, as this removes historical data.
        Returns a tuple: (True/False, "message")
        """
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM credit_sales WHERE credit_id = ?", (credit_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return True, f"Credit sale ID {credit_id} deleted successfully."
            else:
                return False, f"Credit sale ID {credit_id} not found."
        except Exception as e:
            conn.rollback()
            print(f"Error deleting credit sale: {e}")
            return False, f"An error occurred while deleting credit sale: {e}"
        finally:
            conn.close()

    def format_currency(self, amount):
        """
        Helper method to format a numeric amount as Philippine Peso (₱).
        """
        return f"₱ {amount:,.2f}"

