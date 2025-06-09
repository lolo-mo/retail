import csv
import os
import datetime

class InventoryManager:
    """
    Manages all business logic related to inventory.
    It interacts with the DatabaseManager to perform data operations
    and handles calculations related to inventory valuation, re-order, etc.
    """
    def __init__(self, db_manager):
        """
        Initializes the InventoryManager with an instance of DatabaseManager.
        This allows it to interact with the database.
        """
        self.db_manager = db_manager
        # Default reorder level, changed from 5 to 4 as per request
        self.reorder_default_level = 4
        # Default markup percentage for suggested selling price
        self.default_markup_percentage = 30 # 30% markup

    def add_product(self, item_no, item_name, description, unit, supplier_price, selling_price, current_stock, reorder_qty):
        """
        Adds a new product to the inventory.
        Automatically sets reorder_alert based on current_stock and the reorder_default_level.
        """
        # Re-order alert is decided by the app: 'Yes' if stock < reorder_level, 'No' otherwise
        reorder_alert = 1 if current_stock < self.reorder_default_level else 0
        # Call db_manager's add_product, which now returns (success_bool, message_string)
        return self.db_manager.add_product(
            item_no, item_name, description, unit, supplier_price, selling_price,
            current_stock, reorder_alert, reorder_qty
        )

    def get_all_products(self):
        """
        Retrieves all products from the database.
        Returns a list of product dictionaries.
        """
        return self.db_manager.get_all_products()

    def get_product_by_item_no(self, item_no):
        """
        Retrieves a single product by its item number.
        Returns a product dictionary or None if not found.
        """
        return self.db_manager.get_product_by_item_no(item_no)

    def search_products(self, query):
        """
        Searches for products by item name or item number.
        This performs a case-insensitive partial match on item_name and exact match on item_no.
        """
        products = self.db_manager.get_all_products()
        if not query:
            return products # Return all if query is empty

        query = query.lower()
        results = []
        for product in products:
            if (query in product['item_name'].lower() or
                query == product['item_no'].lower()):
                results.append(product)
        return results

    def update_product(self, original_item_no, new_item_data):
        """
        Updates an existing product's details.
        `new_item_data` is a dictionary containing all product fields.
        Automatically recalculates reorder_alert.
        """
        conn = self.db_manager._get_connection() # Access private method for a direct update
        cursor = conn.cursor()
        try:
            # Recalculate reorder_alert based on potentially new current_stock
            new_item_data['reorder_alert'] = 1 if new_item_data['current_stock'] < self.reorder_default_level else 0

            # For now, let's assume original_item_no is the key to update.
            # If item_no itself is changing, it's more complex (delete old, add new)
            cursor.execute('''
                UPDATE products SET
                    item_no = ?, item_name = ?, description = ?, unit = ?,
                    supplier_price = ?, selling_price = ?, current_stock = ?,
                    reorder_alert = ?, reorder_qty = ?
                WHERE item_no = ?
            ''', (
                new_item_data['item_no'], new_item_data['item_name'], new_item_data['description'],
                new_item_data['unit'], new_item_data['supplier_price'], new_item_data['selling_price'],
                new_item_data['current_stock'], new_item_data['reorder_alert'], new_item_data['reorder_qty'],
                original_item_no # Use the original item_no for WHERE clause
            ))
            conn.commit()
            return True, f"Product '{new_item_data['item_name']}' updated successfully."
        except Exception as e:
            print(f"An error occurred while updating product {original_item_no}: {e}")
            return False, f"Failed to update product: {e}"
        finally:
            conn.close()


    def delete_product(self, item_no):
        """Deletes a product from the database."""
        # The db_manager.delete_product returns a boolean, we adapt it to (bool, msg)
        success = self.db_manager.delete_product(item_no)
        if success:
            return True, f"Product '{item_no}' deleted successfully."
        else:
            return False, f"Failed to delete product '{item_no}'."

    def clear_all_inventory(self):
        """
        Clears all inventory data from the database.
        Returns a tuple: (True/False, "message")
        """
        return self.db_manager.clear_all_products()

    def update_stock(self, item_no, quantity_change):
        """
        Updates the stock level of a product.
        quantity_change can be positive (stock in) or negative (stock out).
        Also updates the reorder_alert status based on the new stock level.
        Returns True/False based on success.
        """
        success = self.db_manager.update_product_stock(item_no, quantity_change)
        if success:
            # After updating stock, get the latest product info to recalculate reorder_alert
            updated_product = self.db_manager.get_product_by_item_no(item_no)
            if updated_product:
                new_reorder_alert = 1 if updated_product['current_stock'] < self.reorder_default_level else 0
                if new_reorder_alert != updated_product['reorder_alert']:
                    conn = self.db_manager._get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute("UPDATE products SET reorder_alert = ? WHERE item_no = ?",
                                       (new_reorder_alert, item_no))
                        conn.commit()
                    except Exception as e:
                        print(f"Error updating reorder alert for {item_no}: {e}")
                    finally:
                        conn.close()
            return True # Stock update was successful
        return False # Stock update failed

    def get_reorder_alerts(self):
        """
        Retrieves a list of products that are below their reorder level.
        Returns a list of product dictionaries where 'reorder_alert' is 1.
        """
        conn = self.db_manager._get_connection()
        cursor = conn.cursor()
        # Fetch items where 'reorder_alert' is explicitly set to 1 by the app logic
        cursor.execute("SELECT * FROM products WHERE reorder_alert = 1")
        products = cursor.fetchall()
        conn.close()
        return [dict(row) for row in products]

    def calculate_inventory_valuation(self):
        """
        Calculates the total inventory value based on selling price and supplier price.
        Returns a dictionary with 'selling_value' and 'supplier_value'.
        """
        products = self.db_manager.get_all_products()
        total_selling_value = 0.0
        total_supplier_value = 0.0

        for product in products:
            stock = product['current_stock']
            selling_price = product['selling_price'] if product['selling_price'] is not None else 0.0
            supplier_price = product['supplier_price'] if product['supplier_price'] is not None else 0.0

            total_selling_value += stock * selling_price
            total_supplier_value += stock * supplier_price

        return {
            'selling_value': total_selling_value,
            'supplier_value': total_supplier_value
        }

    def calculate_projected_profit(self):
        """
        Calculates the potential profit from current inventory if all items are sold at selling price.
        """
        valuation = self.calculate_inventory_valuation()
        return valuation['selling_value'] - valuation['supplier_value']

    def calculate_reorder_cost(self):
        """
        Calculates the total cost needed to reorder items that are below their reorder level.
        """
        reorder_items = self.get_reorder_alerts()
        total_reorder_cost = 0.0
        for item in reorder_items:
            # Calculate how much needs to be ordered to reach at least reorder_qty (if not already met)
            qty_needed_to_reorder = item['reorder_qty'] - item['current_stock']
            if qty_needed_to_reorder > 0: # Only calculate if stock is actually below reorder_qty
                total_reorder_cost += qty_needed_to_reorder * (item['supplier_price'] if item['supplier_price'] is not None else 0.0)
        return total_reorder_cost

    def suggest_selling_price(self, supplier_price):
        """
        Suggests a selling price based on supplier price and a default markup percentage.
        """
        if supplier_price is None:
            return 0.0 # Cannot suggest if no supplier price
        return supplier_price * (1 + self.default_markup_percentage / 100)

    def import_inventory_from_csv(self, file_path):
        """
        Imports inventory data from a CSV file.
        Updates existing items based on 'Item No.' or adds new ones.
        The 'Re-Order (Yes or No)' column in CSV is ignored; the app calculates it.
        Provides detailed feedback on import status.
        Expected columns: 'Item No.', 'Item Name', 'Description', 'Unit',
                          'Supplier Price (Per Unit)', 'Selling Price',
                          'Current Stock', 'Re-Order QTY' (Note: 'Re-Order (Yes or No)' is optional/ignored)
        """
        success_count = 0
        update_count = 0
        fail_count = 0
        errors = []

        if not os.path.exists(file_path):
            return 0, 0, 0, ["File not found."]

        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Define required headers that MUST be present, excluding the 'Re-Order (Yes or No)'
            # as it's derived by the app.
            required_headers = ['Item No.', 'Item Name', 'Description', 'Unit',
                                'Supplier Price (Per Unit)', 'Selling Price',
                                'Current Stock', 'Re-Order QTY']
            
            # Check if all required headers are present.
            # It's okay if 'Re-Order (Yes or No)' is in the CSV, but it won't be used.
            if not all(header in reader.fieldnames for header in required_headers):
                missing_headers = [header for header in required_headers if header not in reader.fieldnames]
                return 0, 0, 0, [f"CSV file is missing one or more required headers: {', '.join(missing_headers)}"]

            for row_num, row in enumerate(reader, start=2): # Start from 2 for row number in file
                item_no = row.get('Item No.', '').strip()
                item_name = row.get('Item Name', '').strip()

                # Basic validation for essential fields
                if not item_no or not item_name:
                    errors.append(f"Row {row_num}: 'Item No.' or 'Item Name' is missing/empty. Skipping.")
                    fail_count += 1
                    continue

                try:
                    # Convert types, handle potential errors
                    # Use .get() with default values to prevent KeyError if column is missing
                    supplier_price = float(row.get('Supplier Price (Per Unit)', 0.0) or 0.0)
                    selling_price = float(row.get('Selling Price', 0.0) or 0.0)
                    current_stock = int(row.get('Current Stock', 0) or 0)
                    reorder_qty = int(row.get('Re-Order QTY', self.reorder_default_level) or self.reorder_default_level)
                    
                    # The 'Re-Order (Yes or No)' column from CSV is *ignored* for the alert status,
                    # as the app now derives it. We only care about reorder_qty for the database.
                    # reorder_alert is calculated by add_product/update_product based on current_stock vs reorder_default_level

                    # Check if item exists to decide between add or update
                    existing_product = self.db_manager.get_product_by_item_no(item_no)

                    if existing_product:
                        # Update existing product
                        new_item_data = {
                            'item_no': item_no,
                            'item_name': item_name,
                            'description': row.get('Description', ''),
                            'unit': row.get('Unit', ''),
                            'supplier_price': supplier_price,
                            'selling_price': selling_price,
                            'current_stock': current_stock,
                            # reorder_alert is recalculated in update_product
                            'reorder_qty': reorder_qty
                        }
                        success_update, msg = self.update_product(item_no, new_item_data)
                        if success_update:
                            update_count += 1
                        else:
                            errors.append(f"Row {row_num}: Failed to update item '{item_name}' ({item_no}). Error: {msg}")
                            fail_count += 1
                    else:
                        # Add new product
                        # Now expect a tuple (success_bool, message_string) from self.add_product
                        success_add, msg = self.add_product(item_no, item_name, row.get('Description', ''), row.get('Unit', ''),
                                            supplier_price, selling_price, current_stock, reorder_qty)
                        if success_add:
                            success_count += 1
                        else:
                            errors.append(f"Row {row_num}: Failed to add new item '{item_name}' ({item_no}). Error: {msg}")
                            fail_count += 1

                except ValueError as ve:
                    errors.append(f"Row {row_num}: Data type error for '{item_name}' ({item_no}) - {ve}. Skipping.")
                    fail_count += 1
                except Exception as ex:
                    errors.append(f"Row {row_num}: An unexpected error occurred for '{item_name}' ({item_no}) - {ex}. Skipping.")
                    fail_count += 1
        return success_count, update_count, fail_count, errors

    def export_inventory_to_csv(self, file_path):
        """
        Exports all inventory data to a CSV file.
        The 'Re-Order (Yes or No)' column is generated based on the app's internal logic.
        """
        products = self.get_all_products()
        if not products:
            return False, "No inventory data to export."

        # Define the headers in the desired order
        headers = ['Item No.', 'Item Name', 'Description', 'Unit',
                   'Supplier Price (Per Unit)', 'Selling Price', 'Current Stock',
                   'Re-Order (Yes or No)', 'Re-Order QTY']

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()

                for product in products:
                    row_data = {
                        'Item No.': product.get('item_no', ''),
                        'Item Name': product.get('item_name', ''),
                        'Description': product.get('description', ''),
                        'Unit': product.get('unit', ''),
                        'Supplier Price (Per Unit)': product.get('supplier_price', 0.0),
                        'Selling Price': product.get('selling_price', 0.0),
                        'Current Stock': product.get('current_stock', 0),
                        # Generate 'Re-Order (Yes or No)' based on product's reorder_alert status
                        'Re-Order (Yes or No)': 'Yes' if product.get('reorder_alert') == 1 else 'No',
                        'Re-Order QTY': product.get('reorder_qty', self.reorder_default_level)
                    }
                    writer.writerow(row_data)
            return True, "Inventory exported successfully."
        except IOError as e:
            return False, f"File I/O error: {e}"
        except Exception as e:
            return False, f"An unexpected error occurred during export: {e}"

