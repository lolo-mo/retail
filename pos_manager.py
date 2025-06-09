import datetime

class POSManager:
    """
    Manages all business logic related to the Point of Sale (POS) system.
    This includes handling the customer's cart, processing sales transactions,
    and interacting with inventory and credit sales managers.
    """
    def __init__(self, db_manager, inventory_manager, credit_sales_manager):
        """
        Initializes the POSManager with instances of DatabaseManager,
        InventoryManager, and CreditSalesManager to facilitate inter-module communication.
        """
        self.db_manager = db_manager
        self.inventory_manager = inventory_manager
        self.credit_sales_manager = credit_sales_manager
        self.cart = {}  # In-memory dictionary to hold items currently in the cart
                        # Format: {item_no: {'product_data': {...}, 'quantity': int, 'subtotal': float}}

    def add_item_to_cart(self, item_no, quantity):
        """
        Adds an item to the in-memory cart.
        Checks for item existence and sufficient stock before adding.
        Returns a tuple: (True/False, "message")
        """
        product = self.inventory_manager.get_product_by_item_no(item_no)

        if not product:
            return False, f"Item with Item No. '{item_no}' not found."

        # Ensure quantity is a positive integer
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return False, "Quantity must be a positive number."
        except ValueError:
            return False, "Invalid quantity. Please enter a number."

        # Get current stock
        current_stock = product['current_stock']

        # Determine existing quantity in cart for this item
        cart_quantity = self.cart.get(item_no, {}).get('quantity', 0)

        # Check if total quantity (in cart + new addition) exceeds available stock
        if (cart_quantity + quantity) > current_stock:
            return False, f"Insufficient stock for '{product['item_name']}'. Available: {current_stock - cart_quantity}."

        # If item already in cart, update quantity
        if item_no in self.cart:
            self.cart[item_no]['quantity'] += quantity
            self.cart[item_no]['subtotal'] = self.cart[item_no]['quantity'] * product['selling_price']
        else:
            # Add new item to cart
            self.cart[item_no] = {
                'product_data': product,
                'quantity': quantity,
                'subtotal': quantity * product['selling_price']
            }
        return True, f"'{product['item_name']}' x{quantity} added to cart."

    def remove_item_from_cart(self, item_no):
        """
        Removes an item completely from the cart.
        Returns True if removed, False if not found.
        """
        if item_no in self.cart:
            del self.cart[item_no]
            return True
        return False

    def update_cart_item_quantity(self, item_no, new_quantity):
        """
        Updates the quantity of a specific item in the cart.
        Checks for stock availability.
        Returns a tuple: (True/False, "message")
        """
        if item_no not in self.cart:
            return False, "Item not in cart."

        product = self.inventory_manager.get_product_by_item_no(item_no)
        if not product:
            return False, "Product data not found for item in cart." # Should not happen if data is consistent

        try:
            new_quantity = int(new_quantity)
            if new_quantity < 0:
                return False, "Quantity cannot be negative."
        except ValueError:
            return False, "Invalid quantity. Please enter a number."

        current_stock = product['current_stock']

        if new_quantity > current_stock:
            return False, f"Not enough stock. Available: {current_stock}."

        if new_quantity == 0:
            return self.remove_item_from_cart(item_no), f"'{product['item_name']}' removed from cart."
        else:
            self.cart[item_no]['quantity'] = new_quantity
            self.cart[item_no]['subtotal'] = new_quantity * product['selling_price']
            return True, f"Quantity for '{product['item_name']}' updated to {new_quantity}."

    def clear_cart(self):
        """Clears all items from the current cart."""
        self.cart = {}

    def get_cart_items(self):
        """Returns the current items in the cart as a list of dictionaries."""
        # Convert the dictionary format to a list of dicts for easier display/iteration
        return list(self.cart.values())

    def calculate_cart_total(self, additional_charges=0.0, discount_amount=0.0):
        """
        Calculates the total amount for all items in the cart,
        applying any additional charges or discounts.
        Returns a dictionary with 'subtotal', 'discount', 'charges', 'grand_total'.
        """
        subtotal = sum(item['subtotal'] for item in self.cart.values())

        # Ensure discount and charges are numeric and non-negative
        try:
            discount_amount = float(discount_amount)
            if discount_amount < 0: discount_amount = 0.0
        except ValueError: discount_amount = 0.0

        try:
            additional_charges = float(additional_charges)
            if additional_charges < 0: additional_charges = 0.0
        except ValueError: additional_charges = 0.0


        gross_total = subtotal + additional_charges
        final_total = gross_total - discount_amount
        if final_total < 0: final_total = 0 # Ensure total doesn't go negative

        return {
            'subtotal': subtotal,
            'discount': discount_amount,
            'charges': additional_charges,
            'grand_total': final_total
        }

    def process_sale(self, payment_type, customer_name="", additional_charges=0.0, discount_amount=0.0, notes=""):
        """
        Processes the sale: records the transaction, updates stock,
        and handles credit sales if applicable.
        Returns a tuple: (True/False, "message", sale_id)
        """
        if not self.cart:
            return False, "Cart is empty. No sale to process.", None

        # Calculate final total
        totals = self.calculate_cart_total(additional_charges, discount_amount)
        grand_total = totals['grand_total']

        if grand_total <= 0 and payment_type != 'Credit':
            return False, "Cannot process sale with zero or negative total for non-credit payment.", None


        current_date = datetime.date.today().strftime("%Y-%m-%d")
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        # Prepare sale data for the 'sales' table
        sale_data = {
            'sale_date': current_date,
            'sale_time': current_time,
            'total_amount': grand_total,
            'payment_type': payment_type,
            'customer_name': customer_name if customer_name else None,
            'notes': notes if notes else None
        }

        # Prepare item data for the 'sale_items' table and stock update
        sale_items_data = []
        for item_no, cart_item in self.cart.items():
            product_data = cart_item['product_data']
            quantity = cart_item['quantity']

            # Check if stock is still sufficient before processing (race condition prevention)
            current_product_info = self.inventory_manager.get_product_by_item_no(item_no)
            if not current_product_info or current_product_info['current_stock'] < quantity:
                # This is a critical error, stock became insufficient after item was added to cart
                return False, f"Stock insufficient for '{product_data['item_name']}'. Sale aborted.", None

            sale_items_data.append({
                'item_no': item_no,
                'quantity_sold': quantity,
                'selling_price_at_sale': product_data['selling_price'],
                'supplier_price_at_sale': product_data['supplier_price']
            })

        # --- Transaction Start ---
        # Begin a database transaction to ensure atomicity of sale processing
        # (either all steps succeed or all fail)
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        try:
            # 1. Insert into sales table
            cursor.execute('''
                INSERT INTO sales (sale_date, sale_time, total_amount, payment_type, customer_name, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sale_data['sale_date'], sale_data['sale_time'], sale_data['total_amount'],
                  sale_data['payment_type'], sale_data['customer_name'], sale_data['notes']))
            sale_id = cursor.lastrowid # Get the ID of the newly inserted sale

            # 2. Insert into sale_items table and update product stock
            for item in sale_items_data:
                # Insert sale item
                cursor.execute('''
                    INSERT INTO sale_items (sale_id, item_no, quantity_sold, selling_price_at_sale, supplier_price_at_sale)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sale_id, item['item_no'], item['quantity_sold'], item['selling_price_at_sale'], item['supplier_price_at_sale']))

                # Update stock directly using cursor for transaction control
                cursor.execute("UPDATE products SET current_stock = current_stock - ? WHERE item_no = ?",
                               (item['quantity_sold'], item['item_no']))

                # Also update reorder_alert for consistency (optional, could be done by InventoryManager after transaction)
                # Let's re-fetch and update reorder_alert using InventoryManager's method for simplicity and consistency
                # This will execute a separate query after the transaction, which is fine.
                self.inventory_manager.update_stock(item['item_no'], 0) # Trigger alert update, quantity change already handled

            # 3. Handle Credit Sales
            if payment_type == 'Credit':
                if not customer_name:
                    conn.rollback() # Rollback if credit sale without customer name
                    return False, "Customer name is required for credit sales.", None
                # Add credit sale via credit_sales_manager
                credit_success = self.credit_sales_manager.add_credit_sale(
                    sale_id, customer_name, grand_total, grand_total, 'Unpaid'
                )
                if not credit_success:
                    conn.rollback() # Rollback if credit sale addition fails
                    return False, "Failed to record credit sale.", None

            conn.commit() # Commit all changes if successful
            self.clear_cart() # Clear the cart after successful sale
            return True, "Sale processed successfully!", sale_id

        except Exception as e:
            conn.rollback() # Rollback all changes if any error occurs
            print(f"Error processing sale: {e}")
            return False, f"An error occurred during sale processing: {e}", None
        finally:
            conn.close()


    def format_currency(self, amount):
        """
        Helper method to format a numeric amount as Philippine Peso (₱).
        """
        return f"₱ {amount:,.2f}"

