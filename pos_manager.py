import datetime

class POSManager:
    """
    Manages all business logic related to Point of Sale operations.
    Handles adding items to a sale, processing transactions, and interacting
    with inventory and sales records.
    """
    def __init__(self, db_manager, inventory_manager, credit_sales_manager):
        """
        Initializes the POSManager with instances of DatabaseManager,
        InventoryManager, and CreditSalesManager.
        """
        self.db_manager = db_manager
        self.inventory_manager = inventory_manager
        self.credit_sales_manager = credit_sales_manager
        self.current_transaction_items = {}  # {item_no: {'product_data': {}, 'quantity': int, 'subtotal': float}}

    def add_item_to_transaction(self, item_no, quantity):
        """
        Adds or updates an item in the current transaction.
        Checks for stock availability and if the item is active.

        Args:
            item_no (str): The item number of the product.
            quantity (int): The quantity to add.

        Returns:
            tuple: (bool, str) - Success status and a message.
        """
        product = self.inventory_manager.get_product_by_item_no(item_no)

        if not product:
            return False, "Item not found."
        
        # Check if the product is active
        if product.get('is_active', 1) == 0: # Default to active if column somehow missing
            return False, f"Item '{product['item_name']}' is discontinued and cannot be sold."

        current_stock = product.get('current_stock', 0)
        
        # Calculate current quantity in transaction, including previously added quantities
        existing_qty_in_transaction = 0
        if item_no in self.current_transaction_items:
            existing_qty_in_transaction = self.current_transaction_items[item_no]['quantity']
        
        total_requested_qty = existing_qty_in_transaction + quantity

        if total_requested_qty <= 0: # Prevent adding 0 or negative quantities initially
             if item_no in self.current_transaction_items:
                # If quantity becomes 0 or less, remove item from transaction
                del self.current_transaction_items[item_no]
                return True, f"Quantity for '{product['item_name']}' adjusted. Item removed if quantity is zero or less."
             return False, "Quantity must be positive to add a new item."

        if current_stock < total_requested_qty:
            return False, f"Insufficient stock for '{product['item_name']}'. Available: {current_stock}, Requested: {total_requested_qty}."

        selling_price = product.get('selling_price', 0.0)
        subtotal = quantity * selling_price

        if item_no in self.current_transaction_items:
            # Update existing item quantity and subtotal
            self.current_transaction_items[item_no]['quantity'] = total_requested_qty
            self.current_transaction_items[item_no]['subtotal'] = total_requested_qty * selling_price
            return True, f"Quantity for '{product['item_name']}' updated to {total_requested_qty}."
        else:
            # Add new item to transaction
            self.current_transaction_items[item_no] = {
                'product_data': product,
                'quantity': quantity,
                'subtotal': subtotal
            }
            return True, f"'{product['item_name']}' added to transaction."

    def remove_item_from_transaction(self, item_no):
        """
        Removes an item completely from the current transaction.
        """
        if item_no in self.current_transaction_items:
            item_name = self.current_transaction_items[item_no]['product_data']['item_name']
            del self.current_transaction_items[item_no]
            return True, f"'{item_name}' removed from transaction."
        return False, "Item not found in current transaction."

    def get_current_transaction_items(self):
        """
        Returns a list of items currently in the transaction for display.
        Each item includes relevant product details, quantity, and subtotal.
        """
        display_items = []
        for item_no, data in self.current_transaction_items.items():
            product = data['product_data']
            display_items.append({
                'item_no': product.get('item_no', ''),
                'item_name': product.get('item_name', ''),
                'unit': product.get('unit', ''),
                'selling_price': product.get('selling_price', 0.0),
                'quantity': data['quantity'],
                'subtotal': data['subtotal']
            })
        return display_items

    def calculate_transaction_total(self):
        """
        Calculates the total amount of the current transaction.
        """
        total = sum(item_data['subtotal'] for item_data in self.current_transaction_items.values())
        return total

    def clear_transaction(self):
        """
        Clears all items from the current transaction.
        """
        self.current_transaction_items = {}
        return True, "Transaction cleared."

    def process_sale(self, payment_type, customer_name=None, notes=None):
        """
        Processes the current transaction as a sale.
        Deducts stock, records the sale, and handles credit sales.
        """
        if not self.current_transaction_items:
            return False, "No items in transaction to process sale."

        total_amount = self.calculate_transaction_total()
        current_date = datetime.date.today().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        sale_data = {
            'sale_date': current_date,
            'sale_time': current_time,
            'total_amount': total_amount,
            'payment_type': payment_type,
            'customer_name': customer_name,
            'notes': notes
        }
        sale_items_for_db = []

        # Prepare sale items and deduct stock
        for item_no, data in self.current_transaction_items.items():
            product = data['product_data']
            quantity_sold = data['quantity']

            # Deduct stock from inventory
            stock_deducted = self.inventory_manager.update_stock(item_no, -quantity_sold)
            if not stock_deducted:
                # This is a critical error, stock update failed but sale might proceed
                # Consider rolling back if multiple items involved, or alert user.
                # For simplicity, we just print and continue for now.
                print(f"Warning: Failed to deduct stock for {product['item_name']} (Item No: {item_no}).")
                # Decide how to handle: rollback transaction, log error, etc.
                # For now, we'll let the sale proceed but note the stock issue.

            sale_items_for_db.append({
                'item_no': item_no,
                'quantity_sold': quantity_sold,
                'selling_price_at_sale': product.get('selling_price', 0.0),
                'supplier_price_at_sale': product.get('supplier_price', 0.0)
            })

        # Record the sale in the database
        sale_id = self.db_manager.add_sale(sale_data, sale_items_for_db)

        if sale_id is None:
            return False, "Failed to record sale in the database. Please try again."

        # Handle credit sales
        if payment_type == 'Credit':
            if not customer_name:
                # This should ideally be caught by UI validation before calling process_sale
                return False, "Customer name is required for credit sales."
            
            # For a new credit sale, the initial balance is the total amount
            self.credit_sales_manager.add_credit_sale(
                sale_id=sale_id,
                customer_name=customer_name,
                original_amount=total_amount,
                balance=total_amount,
                status='Unpaid' # Initial status for new credit sales
            )
            # You might want to get the credit_id and return it too if needed for immediate display

        self.clear_transaction() # Clear transaction after successful processing
        return True, "Sale processed successfully!"
