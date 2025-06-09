import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime

class POSFrame(ttk.Frame):
    """
    Tkinter Frame for the Point of Sale (POS) section.
    Allows users to add items to a transaction, adjust quantities, process sales
    (cash or credit), and clear the transaction.
    """
    def __init__(self, parent, controller):
        """
        Initializes the POSFrame.

        Args:
            parent: The parent widget (ttk.Notebook).
            controller: The MainApplication instance, providing access to managers.
        """
        super().__init__(parent, padding="15 15 15 15")
        self.controller = controller
        self.columnconfigure(0, weight=2) # Left panel for item input/search
        self.columnconfigure(1, weight=3) # Right panel for transaction items
        self.rowconfigure(0, weight=1) # Main content area

        # --- Left Panel: Item Input and Search ---
        left_panel = ttk.Frame(self, padding="10")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.columnconfigure(0, weight=1) # For item search entry

        ttk.Label(left_panel, text="Add Item to Transaction:", font=('Inter', 12, 'bold')).grid(row=0, column=0, sticky="w", pady=(0,10))

        # Item Search
        ttk.Label(left_panel, text="Item No. / Name:", font=('Inter', 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.item_search_entry = ttk.Entry(left_panel, font=('Inter', 12))
        self.item_search_entry.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.item_search_entry.bind("<Return>", self._search_and_add_item) # Bind Enter key

        ttk.Button(left_panel, text="Add Item (by Item No./Name)", command=self._search_and_add_item, style='Accent.TButton').grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # --- Product Search Results Listbox (for visual selection) ---
        ttk.Label(left_panel, text="Search Results:", font=('Inter', 10)).grid(row=4, column=0, sticky="w", pady=5)
        self.search_results_listbox = tk.Listbox(left_panel, height=10, font=('Inter', 10))
        self.search_results_listbox.grid(row=5, column=0, sticky="nsew", pady=(0, 10))
        self.search_results_listbox.bind("<<ListboxSelect>>", self._on_result_select)
        left_panel.rowconfigure(5, weight=1) # Make listbox expandable

        # Quantity Adjustment for Selected Item in Search Results
        qty_frame = ttk.Frame(left_panel)
        qty_frame.grid(row=6, column=0, sticky="ew", pady=10)
        qty_frame.columnconfigure(0, weight=1)
        qty_frame.columnconfigure(1, weight=1)
        qty_frame.columnconfigure(2, weight=1)

        ttk.Label(qty_frame, text="Quantity:", font=('Inter', 10)).grid(row=0, column=0, sticky="w", padx=5)
        self.quantity_entry = ttk.Entry(qty_frame, font=('Inter', 12), width=5)
        self.quantity_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.quantity_entry.insert(0, "1") # Default quantity
        self.quantity_entry.bind("<Return>", self._add_selected_to_transaction)

        ttk.Button(qty_frame, text="Add Selected", command=self._add_selected_to_transaction).grid(row=0, column=2, sticky="ew", padx=5)
        
        # --- Right Panel: Current Transaction Details ---
        right_panel = ttk.Frame(self, padding="10", relief="groove", borderwidth=2)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1) # Treeview for transaction items

        ttk.Label(right_panel, text="Current Transaction:", font=('Inter', 12, 'bold')).grid(row=0, column=0, sticky="w", pady=(0,10))

        # Transaction Items Treeview
        trans_columns = ("Item No.", "Item Name", "Unit", "Price (₱)", "Qty", "Subtotal (₱)")
        self.transaction_tree = ttk.Treeview(right_panel, columns=trans_columns, show='headings', height=10)

        for col in trans_columns:
            self.transaction_tree.heading(col, text=col, anchor="center")
            self.transaction_tree.column(col, anchor="center")
        self.transaction_tree.column("Item Name", anchor="w", width=150)
        self.transaction_tree.column("Item No.", width=80)
        self.transaction_tree.column("Price (₱)", width=80, anchor="e")
        self.transaction_tree.column("Qty", width=50)
        self.transaction_tree.column("Subtotal (₱)", width=100, anchor="e")

        self.transaction_tree.grid(row=1, column=0, sticky="nsew")

        trans_scrollbar_y = ttk.Scrollbar(right_panel, orient="vertical", command=self.transaction_tree.yview)
        trans_scrollbar_y.grid(row=1, column=1, sticky="ns")
        self.transaction_tree.configure(yscrollcommand=trans_scrollbar_y.set)

        self.transaction_tree.bind("<Delete>", self._on_delete_key_remove_item) # Bind Delete key

        # Total Display
        total_frame = ttk.Frame(right_panel)
        total_frame.grid(row=2, column=0, sticky="ew", pady=(10,0))
        total_frame.columnconfigure(0, weight=1)
        total_frame.columnconfigure(1, weight=1)

        ttk.Label(total_frame, text="TOTAL:", font=('Inter', 16, 'bold')).grid(row=0, column=0, sticky="w")
        self.total_amount_label = ttk.Label(total_frame, text="₱ 0.00", font=('Inter', 18, 'bold'), foreground='#007bff')
        self.total_amount_label.grid(row=0, column=1, sticky="e")

        # Payment Buttons and Options
        payment_frame = ttk.Frame(right_panel, padding="10 0 0 0")
        payment_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        payment_frame.columnconfigure(0, weight=1) # Cash/Credit Button column
        payment_frame.columnconfigure(1, weight=1) # Process Sale Button column

        self.payment_type_var = tk.StringVar(value="Cash") # Default payment type
        ttk.Radiobutton(payment_frame, text="Cash Sale", variable=self.payment_type_var, value="Cash").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(payment_frame, text="Credit Sale", variable=self.payment_type_var, value="Credit").grid(row=1, column=0, sticky="w")

        self.process_sale_button = ttk.Button(payment_frame, text="Process Sale", command=self._process_sale_dialog, style='Success.TButton')
        self.process_sale_button.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(10,0))

        ttk.Button(right_panel, text="Clear Transaction", command=self._clear_current_transaction).grid(row=4, column=0, sticky="ew", pady=(10,0))

        self.refresh_data() # Initial load

    def _clear_search_results(self):
        """Clears the search results listbox."""
        self.search_results_listbox.delete(0, tk.END)

    def _clear_transaction_treeview(self):
        """Clears all items from the transaction treeview."""
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)

    def _update_transaction_display(self):
        """Updates the transaction treeview and total amount label."""
        self._clear_transaction_treeview()
        items = self.controller.pos_manager.get_current_transaction_items()
        for item in items:
            self.transaction_tree.insert("", "end", iid=item['item_no'], values=(
                item['item_no'],
                item['item_name'],
                item['unit'],
                self.controller.report_generator.format_currency(item['selling_price']),
                item['quantity'],
                self.controller.report_generator.format_currency(item['subtotal'])
            ))
        total = self.controller.pos_manager.calculate_transaction_total()
        self.total_amount_label.config(text=self.controller.report_generator.format_currency(total))

    def _search_and_add_item(self, event=None):
        """
        Searches for products based on entry, displays results, or adds directly if exact match.
        """
        query = self.item_search_entry.get().strip()
        self._clear_search_results() # Clear previous search results

        if not query:
            # If search is empty, just clear results and do nothing
            return

        # Perform search, including inactive items for comprehensive search results (though not for sale)
        # However, for POS, we should ONLY search for active items.
        # Modified to only search for active items for POS
        products = self.controller.inventory_manager.search_products(query, include_inactive=False)

        if not products:
            self.search_results_listbox.insert(tk.END, "No active items found.")
            return

        exact_match = None
        if len(products) == 1 and (products[0]['item_no'] == query or products[0]['item_name'].lower() == query.lower()):
            exact_match = products[0]
        
        if exact_match:
            # If exact match, directly add to transaction
            self._add_item_to_transaction_logic(exact_match['item_no'], 1) # Add 1 by default
            self.item_search_entry.delete(0, tk.END) # Clear entry after adding
            self._clear_search_results() # Clear search results after direct add
        else:
            # Populate listbox with search results
            for product in products:
                self.search_results_listbox.insert(tk.END, f"{product['item_no']} - {product['item_name']} (Stock: {product['current_stock']})")
                self.search_results_listbox.item_product_data = product # Store product data with item
            # Automatically select the first item if there are results
            if products:
                self.search_results_listbox.selection_set(0)
                self.search_results_listbox.focus_set()


    def _on_result_select(self, event):
        """Handles selection in the search results listbox."""
        selected_indices = self.search_results_listbox.curselection()
        if not selected_indices:
            return
        
        # You can retrieve the associated product data here if stored, or fetch it again
        # For now, we rely on the logic in _add_selected_to_transaction to get data by item_no
        # if you stored product objects with each listbox item, you could get it like:
        # selected_product = self.search_results_listbox.item_product_data[selected_indices[0]]
        pass


    def _add_selected_to_transaction(self, event=None):
        """Adds the selected item from the search results to the transaction."""
        selected_indices = self.search_results_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Item Selected", "Please select an item from the search results to add.")
            return

        selected_item_text = self.search_results_listbox.get(selected_indices[0])
        # Extract item_no from the selected text (e.g., "1001 - Apple (Stock: 50)")
        try:
            item_no = selected_item_text.split(' ')[0]
        except IndexError:
            messagebox.showerror("Error", "Could not parse item number from selection.")
            return

        try:
            quantity = int(self.quantity_entry.get())
            if quantity <= 0:
                messagebox.showwarning("Invalid Quantity", "Quantity must be a positive integer.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Quantity", "Please enter a valid number for quantity.")
            return
        
        self._add_item_to_transaction_logic(item_no, quantity)

    def _add_item_to_transaction_logic(self, item_no, quantity):
        """Encapsulates the logic for adding an item to the transaction."""
        success, message = self.controller.pos_manager.add_item_to_transaction(item_no, quantity)
        if success:
            self._update_transaction_display()
            # Clear quantity and search entry for next item
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, "1")
            self.item_search_entry.delete(0, tk.END)
            self._clear_search_results() # Clear search results after adding
            self.item_search_entry.focus_set() # Set focus back to search entry
        else:
            messagebox.showerror("Error Adding Item", message)

    def _on_delete_key_remove_item(self, event):
        """Removes the selected item from the transaction when Delete key is pressed."""
        selected_item_id = self.transaction_tree.focus()
        if not selected_item_id:
            return # No item selected

        item_no = selected_item_id # The iid is the item_no
        success, message = self.controller.pos_manager.remove_item_from_transaction(item_no)
        if success:
            self.transaction_tree.delete(selected_item_id)
            self._update_transaction_display()
        else:
            messagebox.showerror("Error Removing Item", message)


    def _clear_current_transaction(self):
        """Clears the current transaction."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the current transaction?"):
            success, message = self.controller.pos_manager.clear_transaction()
            if success:
                self._update_transaction_display()
                messagebox.showinfo("Transaction Cleared", message)
                self.item_search_entry.focus_set()
            else:
                messagebox.showerror("Error", message)

    def _process_sale_dialog(self):
        """Opens a dialog to finalize the sale."""
        total_amount = self.controller.pos_manager.calculate_transaction_total()
        if total_amount <= 0:
            messagebox.showwarning("No Items", "Please add items to the transaction before processing a sale.")
            return

        payment_type = self.payment_type_var.get()
        customer_name = None

        if payment_type == "Credit":
            # Prompt for customer name for credit sales
            customer_name_dialog = tk.simpledialog.askstring("Credit Sale", "Enter Customer Name:")
            if customer_name_dialog:
                customer_name = customer_name_dialog.strip()
                if not customer_name:
                    messagebox.showwarning("Input Required", "Customer Name is required for Credit Sales.")
                    return
            else:
                # User cancelled customer name entry
                return

        # Simple confirmation before processing
        if messagebox.askyesno("Confirm Sale", f"Process sale for {self.controller.report_generator.format_currency(total_amount)} as {payment_type}?"):
            success, message = self.controller.pos_manager.process_sale(payment_type, customer_name)
            if success:
                messagebox.showinfo("Sale Complete", message)
                self._update_transaction_display() # Clear and refresh POS UI
                self.controller.dashboard_frame.update_metrics() # Update dashboard after sale
            else:
                messagebox.showerror("Sale Failed", message)


    def refresh_data(self):
        """
        Refreshes the data displayed in the POS frame.
        Clears the current transaction display.
        """
        self._clear_search_results()
        self.item_search_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.quantity_entry.insert(0, "1")
        self.controller.pos_manager.clear_transaction() # Ensure manager's transaction is also cleared
        self._update_transaction_display() # Refresh display to show empty transaction
        self.item_search_entry.focus_set() # Set initial focus
