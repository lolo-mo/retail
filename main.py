import tkinter as tk
from tkinter import ttk
import os
import datetime

# Import manager classes
from database import DatabaseManager
from inventory_manager import InventoryManager
from pos_manager import POSManager
from stock_log_manager import StockLogManager
from credit_sales_manager import CreditSalesManager
from expenses_manager import ExpensesManager
from report_generator import ReportGenerator

# Import UI frame classes
from ui_components.dashboard_frame import DashboardFrame
from ui_components.inventory_frame import InventoryFrame
from ui_components.pos_frame import POSFrame
from ui_components.stock_in_frame import StockInFrame
from ui_components.credit_sales_frame import CreditSalesFrame
from ui_components.expenses_frame import ExpensesFrame
from ui_components.reports_frame import ReportsFrame

class MainApplication(tk.Tk):
    """
    The main application class for the Grocery Store Management System.
    It sets up the main window, initializes database and business logic managers,
    and creates the tabbed user interface.
    """
    def __init__(self):
        super().__init__()
        self.title("Grocery Store Management System - " + datetime.datetime.now().strftime("%B %d, %Y"))
        self.geometry("1200x800") # Set initial window size
        self.state('zoomed') # Start the window maximized for a better experience

        # --- 1. Initialize Database Manager ---
        # Ensure the 'data' directory exists
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.db_manager = DatabaseManager(os.path.join(data_dir, 'store.db'))
        self.db_manager.initialize_db() # Create tables if they don't exist

        # --- 2. Initialize Business Logic Managers ---
        # These managers encapsulate the core logic and interact with the database.
        self.inventory_manager = InventoryManager(self.db_manager)
        # Initialize CreditSalesManager before POSManager as POSManager depends on it
        self.credit_sales_manager = CreditSalesManager(self.db_manager)
        # Corrected line: Pass self.credit_sales_manager to POSManager
        self.pos_manager = POSManager(self.db_manager, self.inventory_manager, self.credit_sales_manager)
        self.stock_log_manager = StockLogManager(self.db_manager, self.inventory_manager)
        self.expenses_manager = ExpensesManager(self.db_manager)
        self.report_generator = ReportGenerator(self.db_manager)

        # --- 3. Set up the Main Tabbed Interface (ttk.Notebook) ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10) # Add some padding

        # Configure a modern style for the notebook tabs (optional, but improves aesthetics)
        style = ttk.Style()
        style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        style.configure('TNotebook.Tab', padding=[10, 5], font=('Inter', 10, 'bold'))
        style.configure('TNotebook', tabposition='nw') # Tabs on north-west
        style.map('TNotebook.Tab', background=[('selected', '#e0e0e0')], foreground=[('selected', 'black')])


        # --- 4. Create and Add UI Frames as Tabs ---
        # Each frame is instantiated with the notebook as its parent and a reference to this
        # MainApplication instance (controller) to access the managers.

        # Dashboard Tab
        self.dashboard_frame = DashboardFrame(self.notebook, self)
        self.notebook.add(self.dashboard_frame, text=" Dashboard ")

        # Inventory Management Tab
        self.inventory_frame = InventoryFrame(self.notebook, self)
        self.notebook.add(self.inventory_frame, text=" Inventory ")

        # POS Tab
        self.pos_frame = POSFrame(self.notebook, self)
        self.notebook.add(self.pos_frame, text=" POS ")

        # Stock In Log Tab
        self.stock_in_frame = StockInFrame(self.notebook, self)
        self.notebook.add(self.stock_in_frame, text=" Stock In ")

        # Credit Sales Tab
        self.credit_sales_frame = CreditSalesFrame(self.notebook, self)
        self.notebook.add(self.credit_sales_frame, text=" Credit Sales ")

        # Expenses Tab
        self.expenses_frame = ExpensesFrame(self.notebook, self)
        self.notebook.add(self.expenses_frame, text=" Expenses ")

        # Reports Tab
        self.reports_frame = ReportsFrame(self.notebook, self)
        self.notebook.add(self.reports_frame, text=" Reports ")

        # --- 5. Bind notebook tab change event to refresh frames ---
        # When a tab is selected, its refresh_data method (if it exists) will be called.
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # --- 6. Initial Data Load for Dashboard ---
        # Ensure the dashboard is updated when the app starts
        self.after(100, self.dashboard_frame.update_metrics) # Schedule an update shortly after app starts

    def _on_tab_change(self, event):
        """
        Callback function when a notebook tab is changed.
        It calls a 'refresh_data' method on the newly selected tab's frame, if it exists.
        This ensures that data displayed in a tab is fresh when the user switches to it.
        """
        selected_tab_id = self.notebook.select()
        selected_tab_widget = self.notebook.nametowidget(selected_tab_id)

        # Call refresh_data if the selected frame has such a method
        if hasattr(selected_tab_widget, 'refresh_data'):
            selected_tab_widget.refresh_data()
        elif hasattr(selected_tab_widget, 'update_metrics'): # Special case for Dashboard
            selected_tab_widget.update_metrics()


    def run(self):
        """Starts the Tkinter event loop."""
        self.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()
