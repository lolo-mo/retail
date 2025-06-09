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
        # Bind <KeyRelease> for live search, <Return> for direct add
        self.item_search_entry.bind("<KeyRelease>", self._perform_live_search)
        self.item_search_entry.bind("<Return>", self._try_add_from_search_entry)

        # Removed the explicit "Add Item (by Item No./Name)" button as it's now handled by live search and Enter key.

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
        self.quantity_entry.bind("<Return>", self._add_selected_to_transaction) # Bind Enter key to add selected

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

    def _perform_live_search(self, event=None):
        """
        Performs a live search for products based on the item search entry
        and populates the search results listbox.
        """
        query = self.item_search_entry.get().strip()
        self._clear_search_results()

        if not query:
            return

        products = self.controller.inventory_manager.search_products(query, include_inactive=False)

        if not products:
            self.search_results_listbox.insert(tk.END, "No active items found.")
            return

        for product in products:
            self.search_results_listbox.insert(tk.END, f"{product['item_no']} - {product['item_name']} (Stock: {product['current_stock']})")

        # Automatically select the first item if there are results
        if products:
            self.search_results_listbox.selection_set(0)
            # Do NOT focus here, keep focus on the entry for continued typing.
            # self.search_results_listbox.focus_set()


    def _try_add_from_search_entry(self, event=None):
        """
        Attempts to add an item to the transaction directly from the search entry
        if it's an exact match or the only item in the search results.
        Triggered by pressing Enter in the item_search_entry.
        """
        query = self.item_search_entry.get().strip()
        if not query:
            return

        # Perform a fresh search based on the current query
        products = self.controller.inventory_manager.search_products(query, include_inactive=False)

        if not products:
            messagebox.showwarning("Item Not Found", f"No active item found matching '{query}'.")
            return
        
        # Check for exact match first
        exact_match_item_no = None
        for p in products:
            if p['item_no'].lower() == query.lower() or p['item_name'].lower() == query.lower():
                exact_match_item_no = p['item_no']
                break

        if exact_match_item_no:
            # If exact match found, add it directly
            try:
                quantity = int(self.quantity_entry.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be a positive integer.")
                    return
            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Please enter a valid number for quantity.")
                return

            self._add_item_to_transaction_logic(exact_match_item_no, quantity)
            self.item_search_entry.delete(0, tk.END) # Clear search entry after adding
            self._clear_search_results() # Clear search results after direct add
        elif len(products) == 1:
            # If only one product found in search results, add it
            try:
                quantity = int(self.quantity_entry.get())
                if quantity <= 0:
                    messagebox.showwarning("Invalid Quantity", "Quantity must be a positive integer.")
                    return
            except ValueError:
                messagebox.showwarning("Invalid Quantity", "Please enter a valid number for quantity.")
                return
            self._add_item_to_transaction_logic(products[0]['item_no'], quantity)
            self.item_search_entry.delete(0, tk.END) # Clear search entry after adding
            self._clear_search_results() # Clear search results after direct add
        else:
            # If multiple results but no exact match, just inform the user
            messagebox.showinfo("Multiple Results", "Multiple items found. Please select from the list or refine your search.")
            self.search_results_listbox.focus_set() # Move focus to listbox for selection

    def _on_result_select(self, event):
        """Handles selection in the search results listbox."""
        # This function is triggered when an item is selected in the listbox.
        # The "_add_selected_to_transaction" button/event will then use this selection.
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
        """
        Opens a dialog to finalize the sale.
        Ensures both customer name and additional charge prompts appear for credit sales.
        """
        total_amount = self.controller.pos_manager.calculate_transaction_total()
        if total_amount <= 0:
            messagebox.showwarning("No Items", "Please add items to the transaction before processing a sale.")
            return

        payment_type = self.payment_type_var.get()
        customer_name = None
        additional_charge = 0.0

        if payment_type == "Credit":
            # 1. Prompt for customer name for credit sales
            customer_name_dialog = tk.simpledialog.askstring("Credit Sale", "Enter Customer Name (required for credit sales):", parent=self.master)
            
            if customer_name_dialog is None: # User explicitly cancelled the customer name dialog
                messagebox.showwarning("Operation Cancelled", "Customer name entry cancelled. Credit sale cannot proceed.")
                return
            
            customer_name = customer_name_dialog.strip()
            if not customer_name: # If input was just whitespace or empty after stripping
                messagebox.showwarning("Input Required", "Customer Name cannot be empty for Credit Sales. Sale will not proceed.", parent=self.master)
                return # Exit if customer name is empty/invalid

            # --- Use a custom Toplevel dialog for additional charge for better control ---
            # Create an instance of the custom dialog
            additional_charge_dialog = AdditionalChargeDialog(self.master, total_amount, self.controller.report_generator.format_currency)
            # The wait_window call makes the dialog modal, execution pauses here until it's closed
            self.master.wait_window(additional_charge_dialog) 
            
            # Retrieve the result from the custom dialog
            if additional_charge_dialog.result is not None:
                additional_charge = additional_charge_dialog.result
            else:
                # User cancelled the additional charge dialog
                messagebox.showinfo("Charge Cancelled", "Additional charge entry cancelled. Credit sale will proceed without extra charge.")
                additional_charge = 0.0


        # Simple confirmation before processing
        final_total_display = total_amount + additional_charge if payment_type == "Credit" else total_amount
        if messagebox.askyesno("Confirm Sale", f"Process sale for {self.controller.report_generator.format_currency(final_total_display)} as {payment_type}?"):
            success, message = self.controller.pos_manager.process_sale(payment_type, customer_name, None, additional_charge)
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


class AdditionalChargeDialog(tk.Toplevel):
    """
    A custom Toplevel window for entering an additional charge for credit sales.
    Provides better control over focus and validation.
    """
    def __init__(self, parent, current_total_amount, format_currency_func):
        """
        Initializes the AdditionalChargeDialog.

        Args:
            parent: The parent widget (usually the main Tkinter root or Toplevel).
            current_total_amount (float): The current calculated total of the sale.
            format_currency_func (function): A function to format currency (e.g., self.controller.report_generator.format_currency).
        """
        super().__init__(parent)
        self.parent = parent
        self.result = None # Stores the entered charge amount, or None if cancelled
        self.current_total_amount = current_total_amount
        self.format_currency = format_currency_func

        self.title("Enter Additional Charge")
        self.geometry("350x180")
        self.transient(parent) # Make dialog transient to parent
        self.grab_set()        # Make dialog modal
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Current Sale Total:", font=('Inter', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Label(main_frame, text=self.format_currency(self.current_total_amount), font=('Inter', 10)).grid(row=0, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(main_frame, text="Additional Charge:", font=('Inter', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.charge_entry = ttk.Entry(main_frame, font=('Inter', 10))
        self.charge_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        self.charge_entry.insert(0, "0.00") # Default value
        self.charge_entry.focus_set() # Set initial focus to the entry field

        # Buttons
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill="x", side="bottom")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="OK", command=self._on_ok, style='Accent.TButton').grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).grid(row=0, column=1, padx=5, sticky="ew")

        # Bind Enter key to OK button
        self.charge_entry.bind("<Return>", lambda event: self._on_ok())
        
        self.protocol("WM_DELETE_WINDOW", self._on_cancel) # Handle window close button

    def _on_ok(self):
        """Handles the OK button click, validates input, and stores result."""
        try:
            charge = float(self.charge_entry.get())
            if charge < 0:
                messagebox.showwarning("Invalid Charge", "Additional charge cannot be negative. Please enter a positive number or 0.")
            else:
                self.result = charge
                self.destroy() # Close the dialog
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid numeric amount for the additional charge (e.g., 5.00).")

    def _on_cancel(self):
        """Handles the Cancel button click or window close, sets result to None."""
        self.result = None
        self.destroy() # Close the dialog

