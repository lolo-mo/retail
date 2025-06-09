import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime

class CreditSalesFrame(ttk.Frame):
    """
    Tkinter Frame for the Credit Sales section.
    Displays outstanding credit sales, allows recording payments,
    and filtering by customer.
    """
    def __init__(self, parent, controller):
        """
        Initializes the CreditSalesFrame.

        Args:
            parent: The parent widget (ttk.Notebook).
            controller: The MainApplication instance, providing access to managers.
        """
        super().__init__(parent, padding="15 15 15 15")
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Row for Treeview

        # --- 1. Search and Filter Section ---
        search_filter_frame = ttk.Frame(self, padding="5 5 5 5")
        search_filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_filter_frame.columnconfigure(1, weight=1) # Make search entry expand
        search_filter_frame.columnconfigure(2, weight=0) # For filter label
        search_filter_frame.columnconfigure(3, weight=0) # For filter combobox

        ttk.Label(search_filter_frame, text="Search Customer:", font=('Inter', 10)).grid(row=0, column=0, padx=5, sticky="w")
        self.search_entry = ttk.Entry(search_filter_frame, width=40, font=('Inter', 10))
        self.search_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.search_entry.bind("<Return>", self.search_credit_sales) # Bind Enter key for search
        
        ttk.Button(search_filter_frame, text="Search", command=self.search_credit_sales, style='Accent.TButton').grid(row=0, column=2, padx=5)
        ttk.Button(search_filter_frame, text="Refresh", command=self.refresh_data).grid(row=0, column=3, padx=5)


        # --- 2. Credit Sales Treeview ---
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("Credit ID", "Customer Name", "Sale ID", "Original Amount (₱)", "Amount Paid (₱)", "Balance (₱)", "Status", "Due Date")
        
        self.credit_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        # Define column headings and widths
        self.credit_tree.heading("Credit ID", text="Credit ID", anchor="center")
        self.credit_tree.heading("Customer Name", text="Customer Name", anchor="w")
        self.credit_tree.heading("Sale ID", text="Sale ID", anchor="center")
        self.credit_tree.heading("Original Amount (₱)", text="Original Amount (₱)", anchor="e")
        self.credit_tree.heading("Amount Paid (₱)", text="Amount Paid (₱)", anchor="e")
        self.credit_tree.heading("Balance (₱)", text="Balance (₱)", anchor="e")
        self.credit_tree.heading("Status", text="Status", anchor="center")
        self.credit_tree.heading("Due Date", text="Due Date", anchor="center")

        self.credit_tree.column("Credit ID", width=80, anchor="center")
        self.credit_tree.column("Customer Name", width=150, anchor="w")
        self.credit_tree.column("Sale ID", width=80, anchor="center")
        self.credit_tree.column("Original Amount (₱)", width=120, anchor="e")
        self.credit_tree.column("Amount Paid (₱)", width=120, anchor="e")
        self.credit_tree.column("Balance (₱)", width=120, anchor="e")
        self.credit_tree.column("Status", width=100, anchor="center")
        self.credit_tree.column("Due Date", width=100, anchor="center")

        self.credit_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbars for Treeview
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.credit_tree.yview)
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.credit_tree.configure(yscrollcommand=tree_scrollbar_y.set)

        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.credit_tree.xview)
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.credit_tree.configure(xscrollcommand=tree_scrollbar_x.set)

        # --- 3. Action Buttons ---
        button_frame = ttk.Frame(self, padding="5 5 5 5")
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Record Payment", command=self.open_record_payment_dialog, style='Accent.TButton').grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="View All Credit Sales", command=self.refresh_data).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # --- Initial Load of Data ---
        self.refresh_data()

    def _clear_treeview(self):
        """Clears all items from the credit sales treeview."""
        for item in self.credit_tree.get_children():
            self.credit_tree.delete(item)

    def load_credit_sales_data(self, credit_sales=None):
        """
        Loads and displays credit sales data in the Treeview.
        If credit_sales is None, fetches all unpaid/partially paid credit sales.
        """
        self._clear_treeview()
        if credit_sales is None:
            credit_sales = self.controller.credit_sales_manager.get_unpaid_credit_sales()

        for sale in credit_sales:
            # Color rows based on status
            tags = ()
            if sale.get('status') == 'Paid':
                tags = ('paid_credit_sale',)
            elif sale.get('status') == 'Partially Paid':
                tags = ('partially_paid_credit_sale',)

            self.credit_tree.insert("", "end", iid=sale['credit_id'], tags=tags, values=(
                sale.get('credit_id', ''),
                sale.get('customer_name', ''),
                sale.get('sale_id', ''),
                self.controller.report_generator.format_currency(sale.get('original_amount', 0.0)),
                self.controller.report_generator.format_currency(sale.get('amount_paid', 0.0)),
                self.controller.report_generator.format_currency(sale.get('balance', 0.0)),
                sale.get('status', ''),
                sale.get('due_date', 'N/A')
            ))
        
        # Configure row colors after inserting
        style = ttk.Style()
        style.tag_configure('paid_credit_sale', background='#d4edda', foreground='green') # Light green for paid
        style.tag_configure('partially_paid_credit_sale', background='#fff3cd', foreground='#856404') # Light yellow for partially paid

    def search_credit_sales(self, event=None):
        """Performs a search for credit sales by customer name."""
        query = self.search_entry.get().strip()
        if query:
            search_results = self.controller.credit_sales_manager.get_credit_sales_by_customer(query)
            self.load_credit_sales_data(search_results)
            if not search_results:
                messagebox.showinfo("Search Results", f"No credit sales found for customer '{query}'.")
        else:
            self.refresh_data() # If search query is empty, show all unpaid

    def open_record_payment_dialog(self):
        """Opens a dialog to record a payment for the selected credit sale."""
        selected_item_id = self.credit_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("No Credit Sale Selected", "Please select a credit sale to record a payment.")
            return

        credit_id = selected_item_id # Treeview iid is the credit_id
        selected_values = self.credit_tree.item(credit_id, 'values')
        
        # Extract data from selected row
        customer_name = selected_values[1]
        current_balance_str = selected_values[5]
        status = selected_values[6]

        if status == 'Paid':
            messagebox.showinfo("Already Paid", f"This credit sale for '{customer_name}' is already fully paid.")
            return

        # Strip currency symbol and convert to float
        try:
            current_balance = float(current_balance_str.replace('₱', '').replace(',', '').strip())
        except ValueError:
            messagebox.showerror("Error", "Could not parse current balance.")
            return

        # Open dialog for payment
        RecordPaymentDialog(self, self.controller, credit_id, customer_name, current_balance)

    def refresh_data(self):
        """
        Refreshes the data displayed in the credit sales Treeview.
        Called when the tab is selected or after operations.
        """
        self.search_entry.delete(0, tk.END) # Clear search bar on refresh
        self.load_credit_sales_data()
        self.controller.dashboard_frame.update_metrics() # Update dashboard as credit sales change

class RecordPaymentDialog(tk.Toplevel):
    """
    A Toplevel window for recording a payment for a credit sale.
    """
    def __init__(self, parent_frame, controller, credit_id, customer_name, current_balance):
        super().__init__(parent_frame)
        self.parent_frame = parent_frame
        self.controller = controller
        self.credit_id = credit_id
        self.customer_name = customer_name
        self.current_balance = current_balance

        self.title("Record Payment")
        self.geometry("350x200")
        self.transient(parent_frame.master)
        self.grab_set()
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1)

        ttk.Label(main_frame, text="Customer Name:", font=('Inter', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Label(main_frame, text=customer_name, font=('Inter', 10)).grid(row=0, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(main_frame, text="Current Balance:", font=('Inter', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Label(main_frame, text=self.controller.report_generator.format_currency(current_balance), font=('Inter', 10)).grid(row=1, column=1, sticky="w", pady=5, padx=5)

        ttk.Label(main_frame, text="Payment Amount:", font=('Inter', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.payment_amount_entry = ttk.Entry(main_frame, font=('Inter', 10))
        self.payment_amount_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        self.payment_amount_entry.focus_set()

        # Buttons
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill="x", side="bottom")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Submit Payment", command=self._submit_payment, style='Accent.TButton').grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=5, sticky="ew")

        self.wait_window(self)

    def _submit_payment(self):
        """Processes the payment for the credit sale."""
        try:
            payment_amount = float(self.payment_amount_entry.get())
            if payment_amount <= 0:
                messagebox.showwarning("Invalid Amount", "Payment amount must be a positive number.")
                return
            if payment_amount > self.current_balance + 0.01: # Add a small tolerance for floating point
                messagebox.showwarning("Excess Payment", f"Payment amount ({self.controller.report_generator.format_currency(payment_amount)}) exceeds current balance ({self.controller.report_generator.format_currency(self.current_balance)}). Please enter a valid amount.")
                return

            success, message = self.controller.credit_sales_manager.record_credit_payment(
                self.credit_id, payment_amount
            )
            if success:
                messagebox.showinfo("Payment Recorded", message)
                self.parent_frame.refresh_data() # Refresh the parent treeview
                self.destroy()
            else:
                messagebox.showerror("Payment Failed", message)

        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid numeric amount for payment.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
