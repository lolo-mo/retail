import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog # For user feedback and file operations
import os # For file path manipulation
import datetime # Import the datetime module

class InventoryFrame(ttk.Frame):
    """
    Tkinter Frame for the Inventory Management section.
    Displays all inventory items, allows searching, adding, editing,
    deleting, and importing/exporting product data.
    """
    def __init__(self, parent, controller):
        """
        Initializes the InventoryFrame.

        Args:
            parent: The parent widget (ttk.Notebook).
            controller: The MainApplication instance, providing access to managers.
        """
        super().__init__(parent, padding="15 15 15 15") # Add some padding
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) # Row for Treeview

        # --- Configure Treeview Styles ---
        style = ttk.Style()
        # Map for selected/non-selected states (applies to all Treeviews if not specifically tagged)
        style.map('Treeview', background=[('selected', '#a3d9ff')], foreground=[('selected', 'black')])
        # Define default background for non-selected rows (usually white)
        style.configure('Treeview', background='white', foreground='black', rowheight=25)
        style.configure('Treeview.Heading', font=('Inter', 10, 'bold'))

        # --- 1. Search and Filter Section ---
        search_filter_frame = ttk.Frame(self, padding="5 5 5 5")
        search_filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_filter_frame.columnconfigure(1, weight=1) # Make search entry expand
        search_filter_frame.columnconfigure(3, weight=0) # For filter label
        search_filter_frame.columnconfigure(4, weight=0) # For filter combobox


        ttk.Label(search_filter_frame, text="Search (Item Name or No.):", font=('Inter', 10)).grid(row=0, column=0, padx=5, sticky="w")
        self.search_entry = ttk.Entry(search_filter_frame, width=40, font=('Inter', 10))
        self.search_entry.grid(row=0, column=1, padx=5, sticky="ew")
        # Bind <KeyRelease> for live search
        self.search_entry.bind("<KeyRelease>", self.search_items) 

        # Filter for Active/All Items
        ttk.Label(search_filter_frame, text="Show Items:", font=('Inter', 10)).grid(row=0, column=3, padx=(15,5), sticky="w")
        self.show_items_filter = ttk.Combobox(search_filter_frame, values=["Active Only", "All Items"], state="readonly", width=12)
        self.show_items_filter.set("Active Only") # Default value
        self.show_items_filter.grid(row=0, column=4, padx=5, sticky="ew")
        self.show_items_filter.bind("<<ComboboxSelected>>", lambda event: self.refresh_data())


        # Removed the explicit "Search" button as it's now live
        ttk.Button(search_filter_frame, text="Refresh", command=self.refresh_data).grid(row=0, column=5, padx=5)


        # --- 2. Inventory Treeview ---
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("Item No.", "Item Name", "Description", "Unit",
                   "Supplier Price (Per Unit)", "Selling Price", "Current Stock",
                   "Re-Order Alert", "Re-Order QTY", "Status") # Added Status column
        
        self.inventory_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        # IMPORTANT: tag_configure must be on the Treeview instance, not the Style object
        self.inventory_tree.tag_configure('reorder_yes', background='#ffdddd', foreground='black') # Light red background
        self.inventory_tree.tag_configure('inactive_item', foreground='grey', font=('Inter', 10, 'italic')) # Grey out inactive items

        # Dictionary to store current sort order for each column
        self.treeview_sort_order = {col: False for col in columns} # False for ascending, True for descending

        # Define column headings, widths, and bind to sorting function
        self.inventory_tree.heading("Item No.", text="Item No.", anchor="center", command=lambda: self._sort_treeview_column(self.inventory_tree, "Item No.", 0))
        self.inventory_tree.heading("Item Name", text="Item Name", anchor="w", command=lambda: self._sort_treeview_column(self.inventory_tree, "Item Name", 1))
        self.inventory_tree.heading("Description", text="Description", anchor="w", command=lambda: self._sort_treeview_column(self.inventory_tree, "Description", 2))
        self.inventory_tree.heading("Unit", text="Unit", anchor="center", command=lambda: self._sort_treeview_column(self.inventory_tree, "Unit", 3))
        self.inventory_tree.heading("Supplier Price (Per Unit)", text="Supplier Price (₱)", anchor="e", command=lambda: self._sort_treeview_column(self.inventory_tree, "Supplier Price (Per Unit)", 4, type=float))
        self.inventory_tree.heading("Selling Price", text="Selling Price (₱)", anchor="e", command=lambda: self._sort_treeview_column(self.inventory_tree, "Selling Price", 5, type=float))
        self.inventory_tree.heading("Current Stock", text="Current Stock", anchor="center", command=lambda: self._sort_treeview_column(self.inventory_tree, "Current Stock", 6, type=int))
        self.inventory_tree.heading("Re-Order Alert", text="Re-Order Alert", anchor="center", command=lambda: self._sort_treeview_column(self.inventory_tree, "Re-Order Alert", 7))
        self.inventory_tree.heading("Re-Order QTY", text="Re-Order QTY", anchor="center", command=lambda: self._sort_treeview_column(self.inventory_tree, "Re-Order QTY", 8, type=int))
        self.inventory_tree.heading("Status", text="Status", anchor="center", command=lambda: self._sort_treeview_column(self.inventory_tree, "Status", 9))


        self.inventory_tree.column("Item No.", width=90, anchor="center")
        self.inventory_tree.column("Item Name", width=180, anchor="w")
        self.inventory_tree.column("Description", width=200, anchor="w")
        self.inventory_tree.column("Unit", width=60, anchor="center")
        self.inventory_tree.column("Supplier Price (Per Unit)", width=120, anchor="e")
        self.inventory_tree.column("Selling Price", width=120, anchor="e")
        self.inventory_tree.column("Current Stock", width=100, anchor="center")
        self.inventory_tree.column("Re-Order Alert", width=100, anchor="center")
        self.inventory_tree.column("Re-Order QTY", width=100, anchor="center")
        self.inventory_tree.column("Status", width=80, anchor="center")


        self.inventory_tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbars for Treeview
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.inventory_tree.yview)
        tree_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.inventory_tree.configure(yscrollcommand=tree_scrollbar_y.set)

        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.inventory_tree.xview)
        tree_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.inventory_tree.configure(xscrollcommand=tree_scrollbar_x.set)

        # Bind double-click to edit item
        self.inventory_tree.bind("<Double-1>", self._on_double_click_edit)

        # --- 3. Action Buttons ---
        button_frame = ttk.Frame(self, padding="5 5 5 5")
        button_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        # Adjust column weights to accommodate the new button
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        button_frame.columnconfigure(4, weight=1)
        button_frame.columnconfigure(5, weight=1)
        button_frame.columnconfigure(6, weight=1) # New column for Discontinue/Activate

        ttk.Button(button_frame, text="Add New Item", command=self.open_add_item_dialog).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Edit Selected Item", command=self.open_edit_item_dialog).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Delete Selected Item", command=self.delete_selected_item).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Import CSV", command=self.import_csv_dialog).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Export CSV", command=self.export_csv_dialog).grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Clear All Inventory", command=self.clear_all_inventory_dialog, style='Danger.TButton').grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        ttk.Button(button_frame, text="Toggle Active Status", command=self._toggle_item_status).grid(row=0, column=6, padx=5, pady=5, sticky="ew")


        # --- Initial Load of Data ---
        self.refresh_data()

    def _clear_treeview(self):
        """Clears all items from the inventory treeview."""
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

    def load_inventory_data(self, products=None):
        """
        Loads and displays inventory data in the Treeview.
        If products is None, fetches all products from the manager,
        respecting the 'include_inactive' filter.
        Applies 'reorder_yes' tag for highlighting and 'inactive_item' tag.
        """
        self._clear_treeview()
        
        include_inactive = (self.show_items_filter.get() == "All Items")

        if products is None:
            products = self.controller.inventory_manager.get_all_products(include_inactive=include_inactive)

        for product in products:
            reorder_status = "Yes" if product.get('reorder_alert') == 1 else "No"
            active_status = "Active" if product.get('is_active', 1) == 1 else "Inactive" # Default to active if column missing

            tags = []
            if reorder_status == "Yes":
                tags.append('reorder_yes') # Apply the highlighting tag
            if active_status == "Inactive":
                tags.append('inactive_item') # Apply inactive styling

            self.inventory_tree.insert("", "end", iid=product['item_no'], tags=tuple(tags), values=(
                product.get('item_no', ''),
                product.get('item_name', ''),
                product.get('description', ''),
                product.get('unit', ''),
                self.controller.report_generator.format_currency(product.get('supplier_price', 0.0)),
                self.controller.report_generator.format_currency(product.get('selling_price', 0.0)),
                product.get('current_stock', 0),
                reorder_status,
                product.get('reorder_qty', self.controller.inventory_manager.reorder_default_level),
                active_status # Display the status
            ))

    def search_items(self, event=None): # event=None allows binding to button and Enter key
        """Performs a live search based on the entry field and updates the Treeview."""
        query = self.search_entry.get().strip()
        include_inactive = (self.show_items_filter.get() == "All Items")
        search_results = self.controller.inventory_manager.search_products(query, include_inactive=include_inactive)
        self.load_inventory_data(search_results)
        # Removed the messagebox.showinfo for no results, as live search should be subtle.
        # Users expect the list to simply filter.

    def _sort_treeview_column(self, tree, col_name, col_index, type=str):
        """
        Sorts the Treeview column when its header is clicked.
        """
        # Get all items from the treeview
        data = []
        for item_id in tree.get_children():
            values = list(tree.item(item_id, 'values'))
            data.append((values[col_index], item_id)) # Store value and item_id (which is the original iid)

        # Determine sort order
        reverse_sort = self.treeview_sort_order[col_name]
        self.treeview_sort_order[col_name] = not reverse_sort # Toggle for next click

        # Sort the data
        try:
            if type == float:
                # Need to strip currency symbol for proper float conversion
                data.sort(key=lambda x: float(str(x[0]).replace('₱', '').replace(',', '').strip()), reverse=reverse_sort)
            elif type == int:
                data.sort(key=lambda x: int(str(x[0])), reverse=reverse_sort)
            else: # For strings or mixed types
                data.sort(key=lambda x: str(x[0]).lower() if isinstance(x[0], str) else str(x[0]), reverse=reverse_sort)
        except ValueError as ve:
            # Fallback for inconsistent data in column if type conversion fails, print error for debugging
            print(f"ValueError during sorting column {col_name}: {ve}. Falling back to string sort.")
            data.sort(key=lambda x: str(x[0]).lower(), reverse=reverse_sort)
        except Exception as e:
            print(f"Error during sorting column {col_name}: {e}")
            messagebox.showerror("Sorting Error", f"An error occurred while sorting: {e}")
            return


        # Re-insert sorted data into the Treeview
        for index, (val, item_id_to_move) in enumerate(data):
            tree.move(item_id_to_move, '', index) # Move item to its new sorted position

        # Optional: Add a visual indicator for sorting (e.g., arrow in heading)
        # This is more complex and usually involves custom heading widgets or image manipulation.
        # For now, sorting direction is handled by the internal self.treeview_sort_order.

    def open_add_item_dialog(self):
        """Opens a dialog for adding a new inventory item."""
        AddEditItemDialog(self, self.controller, mode='add')

    def open_edit_item_dialog(self):
        """Opens a dialog for editing the selected inventory item."""
        selected_item_id = self.inventory_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("No Item Selected", "Please select an item to edit.")
            return

        item_no = selected_item_id # Treeview iid is the item_no
        product_data = self.controller.inventory_manager.get_product_by_item_no(item_no)
        if product_data:
            AddEditItemDialog(self, self.controller, mode='edit', item_data=product_data)
        else:
            messagebox.showerror("Error", "Could not retrieve item data for editing.")

    def _on_double_click_edit(self, event):
        """Handles double-click event on a Treeview item to open edit dialog."""
        self.open_edit_item_dialog()

    def delete_selected_item(self):
        """Deletes the selected inventory item from the database."""
        selected_item_id = self.inventory_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("No Item Selected", "Please select an item to delete.")
            return

        item_no = selected_item_id
        item_name = self.inventory_tree.item(selected_item_id, 'values')[1] # Get item name from Treeview values

        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{item_name}' (Item No: {item_no})? This action cannot be undone."):
            success, message = self.controller.inventory_manager.delete_product(item_no)
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_data()
            else:
                messagebox.showerror("Error", message)

    def _toggle_item_status(self):
        """
        Toggles the 'is_active' status of the selected item.
        """
        selected_item_id = self.inventory_tree.focus()
        if not selected_item_id:
            messagebox.showwarning("No Item Selected", "Please select an item to change its status.")
            return

        item_no = selected_item_id
        current_status_text = self.inventory_tree.item(item_no, 'values')[9] # Get current status from Treeview
        current_is_active = 1 if current_status_text == "Active" else 0
        
        new_is_active = 1 if current_is_active == 0 else 0 # Toggle status
        
        confirm_action = "activate" if new_is_active == 1 else "discontinue"
        item_name = self.inventory_tree.item(item_no, 'values')[1]

        if messagebox.askyesno(
            f"Confirm {confirm_action.capitalize()}",
            f"Are you sure you want to {confirm_action} '{item_name}' (Item No: {item_no})?"
        ):
            success, message = self.controller.inventory_manager.update_product_status(item_no, new_is_active)
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_data() # Refresh UI to show updated status and filtering
            else:
                messagebox.showerror("Error", message)

    def clear_all_inventory_dialog(self):
        """
        Opens a confirmation dialog to clear all inventory data.
        """
        if messagebox.askyesno(
            "Confirm Clear All",
            "ARE YOU ABSOLUTELY SURE YOU WANT TO CLEAR ALL INVENTORY DATA?\n\n"
            "This action is irreversible and will delete ALL products from your inventory. "
            "This is intended for testing purposes only.\n\n"
            "Do you wish to proceed?"
        ):
            success, message = self.controller.inventory_manager.clear_all_inventory()
            if success:
                messagebox.showinfo("Success", message)
                self.refresh_data()
            else:
                messagebox.showerror("Error", message)

    def import_csv_dialog(self):
        """Opens a file dialog to select a CSV file for import."""
        file_path = filedialog.askopenfilename(
            title="Select CSV file for Inventory Import",
            filetypes=[("CSV files", "*.csv")]
        )
        if file_path:
            success_count, update_count, fail_count, errors = \
                self.controller.inventory_manager.import_inventory_from_csv(file_path)

            summary_message = f"CSV Import Complete:\n\n" \
                              f"New items added: {success_count}\n" \
                              f"Existing items updated: {update_count}\n" \
                              f"Failed entries: {fail_count}\n"

            if errors:
                summary_message += "\nErrors/Warnings:\n" + "\n".join(errors[:5]) # Show first 5 errors
                if len(errors) > 5:
                    summary_message += f"\n...and {len(errors) - 5} more errors."
                messagebox.showwarning("Import Results with Warnings", summary_message)
            else:
                messagebox.showinfo("Import Results", summary_message + "\n\nAll items imported successfully.")

            self.refresh_data()

    def export_csv_dialog(self):
        """Opens a file dialog to specify where to save the exported CSV file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Inventory as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"inventory_export_{datetime.date.today().strftime('%Y%m%d')}.csv"
        )
        if file_path:
            success, message = self.controller.inventory_manager.export_inventory_to_csv(file_path)
            if success:
                messagebox.showinfo("Export Successful", message)
            else:
                messagebox.showerror("Export Failed", message)

    def refresh_data(self):
        """
        Refreshes the data displayed in the inventory Treeview.
        Called when the tab is selected or after C/U/D operations.
        """
        self.search_entry.delete(0, tk.END) # Clear search bar on refresh
        self.load_inventory_data()
        self.controller.dashboard_frame.update_metrics() # Also update dashboard as inventory changes

class AddEditItemDialog(tk.Toplevel):
    """
    A Toplevel window for adding a new inventory item or editing an existing one.
    """
    def __init__(self, parent_frame, controller, mode='add', item_data=None):
        """
        Initializes the AddEditItemDialog.

        Args:
            parent_frame: The parent InventoryFrame instance.
            controller: The MainApplication instance.
            mode (str): 'add' for adding new, 'edit' for editing existing.
            item_data (dict): Dictionary of existing item data if mode is 'edit'.
        """
        super().__init__(parent_frame)
        self.parent_frame = parent_frame
        self.controller = controller
        self.mode = mode
        self.item_data = item_data if item_data else {}
        self.original_item_no = self.item_data.get('item_no', '') # Store original item_no for updates

        self.title("Add New Item" if self.mode == 'add' else "Edit Item")
        self.geometry("450x450")
        self.transient(parent_frame.master) # Make dialog transient to main window
        self.grab_set() # Make dialog modal
        self.resizable(False, False)

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1) # Make entry columns expandable

        # Labels and Entry fields for product details
        fields = [
            ("Item No.", "item_no", tk.StringVar()),
            ("Item Name", "item_name", tk.StringVar()),
            ("Description", "description", tk.StringVar()),
            ("Unit", "unit", tk.StringVar()),
            ("Supplier Price (Per Unit)", "supplier_price", tk.StringVar()),
            ("Selling Price", "selling_price", tk.StringVar()),
            ("Current Stock", "current_stock", tk.StringVar()),
            ("Re-Order QTY", "reorder_qty", tk.StringVar())
        ]

        self.entries = {}
        for i, (label_text, key, var) in enumerate(fields):
            ttk.Label(main_frame, text=f"{label_text}:", font=('Inter', 10, 'bold')).grid(row=i, column=0, sticky="w", pady=5, padx=5)
            entry = ttk.Entry(main_frame, textvariable=var, width=30, font=('Inter', 10))
            entry.grid(row=i, column=1, sticky="ew", pady=5, padx=5)
            self.entries[key] = var

            # Populate fields if in edit mode
            if self.mode == 'edit' and key in self.item_data:
                # Special handling for prices and stock to ensure float/int conversion for display
                if key in ['supplier_price', 'selling_price', 'current_stock', 'reorder_qty']:
                    val = self.item_data[key]
                    var.set(f"{val:.2f}" if isinstance(val, (float, int)) and key in ['supplier_price', 'selling_price'] else str(val))
                else:
                    var.set(self.item_data[key])

            # Disable Item No. editing for existing items to prevent breaking FKs easily
            if self.mode == 'edit' and key == 'item_no':
                entry.config(state='readonly')
            
            # Special button for suggesting selling price
            if key == 'supplier_price':
                suggest_btn = ttk.Button(main_frame, text="Suggest Price", command=self._suggest_selling_price)
                suggest_btn.grid(row=i, column=2, padx=5, sticky="e")


        # --- Buttons ---
        button_frame = ttk.Frame(self, padding="10")
        button_frame.pack(fill="x", side="bottom")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        ttk.Button(button_frame, text="Save", command=self._save_item, style='Accent.TButton').grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(button_frame, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=5, sticky="ew")

        # Set initial focus
        if self.mode == 'add':
            self.entries['item_no'].set("") # Clear fields for add mode
            self.entries['item_name'].set("")
            self.entries['description'].set("")
            self.entries['unit'].set("pcs") # Default unit
            self.entries['supplier_price'].set("0.00")
            self.entries['selling_price'].set("0.00")
            self.entries['current_stock'].set("0")
            self.entries['reorder_qty'].set(str(self.controller.inventory_manager.reorder_default_level))
            main_frame.winfo_children()[1].focus_set() # Focus on Item No.
        else:
            main_frame.winfo_children()[3].focus_set() # Focus on Item Name for edit

        self.wait_window(self) # Keep dialog open until closed

    def _suggest_selling_price(self):
        """Calculates and suggests a selling price based on supplier price."""
        try:
            supplier_price = float(self.entries['supplier_price'].get())
            suggested_price = self.controller.inventory_manager.suggest_selling_price(supplier_price)
            self.entries['selling_price'].set(f"{suggested_price:.2f}")
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter a valid number for Supplier Price.")

    def _save_item(self):
        """Saves the item data (add new or update existing)."""
        # Get data from entry fields
        item_no = self.entries['item_no'].get().strip()
        item_name = self.entries['item_name'].get().strip()
        description = self.entries['description'].get().strip()
        unit = self.entries['unit'].get().strip()
        
        # Validate required fields
        if not item_no or not item_name:
            messagebox.showerror("Validation Error", "Item No. and Item Name are required.")
            return

        # Validate and convert numeric fields
        try:
            supplier_price = float(self.entries['supplier_price'].get())
            selling_price = float(self.entries['selling_price'].get())
            current_stock = int(self.entries['current_stock'].get())
            reorder_qty = int(self.entries['reorder_qty'].get())

            if supplier_price < 0 or selling_price < 0 or current_stock < 0 or reorder_qty < 0:
                messagebox.showerror("Validation Error", "Prices, stock, and re-order quantity cannot be negative.")
                return

        except ValueError:
            messagebox.showerror("Validation Error", "Please enter valid numbers for prices, stock, and re-order quantity.")
            return

        # Prepare data for manager
        item_data = {
            'item_no': item_no,
            'item_name': item_name,
            'description': description,
            'unit': unit,
            'supplier_price': supplier_price,
            'selling_price': selling_price,
            'current_stock': current_stock,
            'reorder_qty': reorder_qty
        }

        success = False
        message = ""

        if self.mode == 'add':
            success, message = self.controller.inventory_manager.add_product(
                item_no, item_name, description, unit, supplier_price,
                selling_price, current_stock, reorder_qty
            )
        elif self.mode == 'edit':
            success, message = self.controller.inventory_manager.update_product(
                self.original_item_no, item_data # Pass original_item_no as the key to update
            )
        
        if success:
            messagebox.showinfo("Success", message)
            self.parent_frame.refresh_data() # Refresh parent Treeview
            self.destroy() # Close the dialog
        else:
            messagebox.showerror("Error", message)
