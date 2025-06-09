import tkinter as tk
from tkinter import ttk
import datetime
import threading # For background updates

class DashboardFrame(ttk.Frame):
    """
    Tkinter Frame for the Dashboard section of the Grocery Store Management System.
    Displays real-time metrics and key financial summaries.
    """
    def __init__(self, parent, controller):
        """
        Initializes the DashboardFrame.

        Args:
            parent: The parent widget (ttk.Notebook).
            controller: The MainApplication instance, providing access to managers.
        """
        super().__init__(parent, padding="15 15 15 15") # Add some padding
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=0) # For header
        self.rowconfigure(1, weight=1) # For main content

        # --- 1. Header Section (Date and Time) ---
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="ew")
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=1)

        self.date_label = ttk.Label(header_frame, text="", font=('Inter', 14, 'bold'), anchor="w")
        self.date_label.grid(row=0, column=0, sticky="ew", padx=10)

        self.time_label = ttk.Label(header_frame, text="", font=('Inter', 14, 'bold'), anchor="e")
        self.time_label.grid(row=0, column=1, sticky="ew", padx=10)

        # --- 2. Main Metrics Grid ---
        metrics_frame = ttk.Frame(self)
        metrics_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)
        for i in range(5): # Up to 5 rows for different metric sections
            metrics_frame.rowconfigure(i, weight=1)

        # --- Dashboard Card Styling Helper ---
        # A simple helper function to create consistent looking cards
        def create_dashboard_card(parent_frame, title_text, row, column, colspan=1):
            card_frame = ttk.LabelFrame(parent_frame, text=f" {title_text} ", padding="10 10 10 10")
            card_frame.grid(row=row, column=column, columnspan=colspan, padx=10, pady=10, sticky="nsew")
            card_frame.columnconfigure(0, weight=1)
            return card_frame

        # --- Inventory Valuation Card ---
        self.inventory_val_card = create_dashboard_card(metrics_frame, "Inventory Valuation", 0, 0)
        ttk.Label(self.inventory_val_card, text="Total Selling Value:", font=('Inter', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=2)
        self.total_selling_value_label = ttk.Label(self.inventory_val_card, text="₱ 0.00", font=('Inter', 12))
        self.total_selling_value_label.grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(self.inventory_val_card, text="Total Supplier Value (Cost):", font=('Inter', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=2)
        self.total_supplier_value_label = ttk.Label(self.inventory_val_card, text="₱ 0.00", font=('Inter', 12))
        self.total_supplier_value_label.grid(row=3, column=0, sticky="w", pady=2)


        # --- Projected Profit Card ---
        self.projected_profit_card = create_dashboard_card(metrics_frame, "Projected Profit", 0, 1)
        ttk.Label(self.projected_profit_card, text="From Current Inventory:", font=('Inter', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=2)
        self.projected_profit_label = ttk.Label(self.projected_profit_card, text="₱ 0.00", font=('Inter', 18, 'bold'), foreground='#28a745') # Green for profit
        self.projected_profit_label.grid(row=1, column=0, sticky="w", pady=2)


        # --- Re-Order Cost Card ---
        self.reorder_cost_card = create_dashboard_card(metrics_frame, "Re-Order Cost", 0, 2)
        ttk.Label(self.reorder_cost_card, text="Cost to Reorder Low Stock:", font=('Inter', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=2)
        self.reorder_cost_label = ttk.Label(self.reorder_cost_card, text="₱ 0.00", font=('Inter', 18, 'bold'), foreground='#dc3545') # Red for cost
        self.reorder_cost_label.grid(row=1, column=0, sticky="w", pady=2)

        # --- Sales Statistics Card ---
        self.sales_stats_card = create_dashboard_card(metrics_frame, "Sales Statistics (Revenue & Net Profit)", 1, 0, colspan=2)
        self.sales_stats_card.columnconfigure(0, weight=1)
        self.sales_stats_card.columnconfigure(1, weight=1)

        ttk.Label(self.sales_stats_card, text="Today's Revenue:", font=('Inter', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.daily_revenue_label = ttk.Label(self.sales_stats_card, text="₱ 0.00", font=('Inter', 12))
        self.daily_revenue_label.grid(row=0, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(self.sales_stats_card, text="Today's Net Profit:", font=('Inter', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.daily_net_profit_label = ttk.Label(self.sales_stats_card, text="₱ 0.00", font=('Inter', 12), foreground='#28a745')
        self.daily_net_profit_label.grid(row=1, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(self.sales_stats_card, text="Weekly Revenue:", font=('Inter', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=2, padx=5)
        self.weekly_revenue_label = ttk.Label(self.sales_stats_card, text="₱ 0.00", font=('Inter', 12))
        self.weekly_revenue_label.grid(row=2, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(self.sales_stats_card, text="Weekly Net Profit:", font=('Inter', 10, 'bold')).grid(row=3, column=0, sticky="w", pady=2, padx=5)
        self.weekly_net_profit_label = ttk.Label(self.sales_stats_card, text="₱ 0.00", font=('Inter', 12), foreground='#28a745')
        self.weekly_net_profit_label.grid(row=3, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(self.sales_stats_card, text="Monthly Revenue:", font=('Inter', 10, 'bold')).grid(row=4, column=0, sticky="w", pady=2, padx=5)
        self.monthly_revenue_label = ttk.Label(self.sales_stats_card, text="₱ 0.00", font=('Inter', 12))
        self.monthly_revenue_label.grid(row=4, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(self.sales_stats_card, text="Monthly Net Profit:", font=('Inter', 10, 'bold')).grid(row=5, column=0, sticky="w", pady=2, padx=5)
        self.monthly_net_profit_label = ttk.Label(self.sales_stats_card, text="₱ 0.00", font=('Inter', 12), foreground='#28a745')
        self.monthly_net_profit_label.grid(row=5, column=1, sticky="w", pady=2, padx=5)


        # --- Items Sold (COGS) Today Card ---
        self.cogs_today_card = create_dashboard_card(metrics_frame, "Items Sold (COGS) Today", 1, 2)
        self.cogs_today_card.rowconfigure(0, weight=0) # Header
        self.cogs_today_card.rowconfigure(1, weight=1) # Treeview
        self.cogs_today_card.columnconfigure(0, weight=1)

        cogs_columns = ("Item Name", "Qty", "Selling Value", "COGS")
        self.cogs_treeview = ttk.Treeview(self.cogs_today_card, columns=cogs_columns, show='headings', height=8)
        for col in cogs_columns:
            self.cogs_treeview.heading(col, text=col, anchor="center")
            self.cogs_treeview.column(col, anchor="center", width=80)
        self.cogs_treeview.column("Item Name", anchor="w", width=120) # Item Name left-aligned

        self.cogs_treeview.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        cogs_scrollbar = ttk.Scrollbar(self.cogs_today_card, orient="vertical", command=self.cogs_treeview.yview)
        cogs_scrollbar.grid(row=1, column=1, sticky="ns")
        self.cogs_treeview.configure(yscrollcommand=cogs_scrollbar.set)

        # --- Initial Update Call ---
        self._update_datetime() # Start date/time updates immediately
        self.update_metrics() # Populate all dashboard metrics

    def _update_datetime(self):
        """Updates the current date and time labels."""
        now = datetime.datetime.now()
        self.date_label.config(text=now.strftime("%A, %d-%b-%Y"))
        self.time_label.config(text=now.strftime("%I:%M:%S %p"))
        # Schedule the next update after 1000 milliseconds (1 second)
        self.after(1000, self._update_datetime)

    def update_metrics(self):
        """
        Fetches and updates all dashboard metrics from the respective managers.
        This method should be called periodically or when the dashboard tab is selected.
        """
        # Using a thread for _perform_metric_updates to prevent UI freeze
        # for potentially long database operations.
        threading.Thread(target=self._perform_metric_updates).start()

    def _perform_metric_updates(self):
        """
        Internal method to perform the actual data fetching and label updates.
        Separated to allow for potential threading.
        """
        try:
            # --- Inventory Valuation ---
            inventory_val = self.controller.inventory_manager.calculate_inventory_valuation()
            # Use report_generator.format_currency for all formatting
            self.total_selling_value_label.config(text=self.controller.report_generator.format_currency(inventory_val['selling_value']))
            self.total_supplier_value_label.config(text=self.controller.report_generator.format_currency(inventory_val['supplier_value']))

            # --- Projected Profit ---
            projected_profit = self.controller.inventory_manager.calculate_projected_profit()
            self.projected_profit_label.config(text=self.controller.report_generator.format_currency(projected_profit))
            if projected_profit < 0:
                self.projected_profit_label.config(foreground='#dc3545') # Red if loss
            else:
                self.projected_profit_label.config(foreground='#28a745') # Green if profit


            # --- Re-Order Cost ---
            reorder_cost = self.controller.inventory_manager.calculate_reorder_cost()
            self.reorder_cost_label.config(text=self.controller.report_generator.format_currency(reorder_cost))
            if reorder_cost > 0:
                self.reorder_cost_label.config(foreground='#dc3545') # Red if cost exists
            else:
                self.reorder_cost_label.config(foreground='black') # Default color


            # --- Sales Statistics (Daily, Weekly, Monthly) ---
            today = datetime.date.today()
            # Daily
            daily_report = self.controller.report_generator.generate_financial_summary_report(
                today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
            )
            self.daily_revenue_label.config(text=self.controller.report_generator.format_currency(daily_report['total_revenue']))
            self.daily_net_profit_label.config(text=self.controller.report_generator.format_currency(daily_report['net_income']))
            self.daily_net_profit_label.config(foreground='#28a745' if daily_report['net_income'] >= 0 else '#dc3545')


            # Weekly (Last 7 days including today)
            # Find the start of the current week (Monday)
            # For consistent weekly reports, use a fixed start (e.g., Monday).
            # The .weekday() method returns 0 for Monday, 6 for Sunday.
            start_of_week = today - datetime.timedelta(days=today.weekday())
            weekly_report = self.controller.report_generator.generate_financial_summary_report(
                start_of_week.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
            )
            self.weekly_revenue_label.config(text=self.controller.report_generator.format_currency(weekly_report['total_revenue']))
            self.weekly_net_profit_label.config(text=self.controller.report_generator.format_currency(weekly_report['net_income']))
            self.weekly_net_profit_label.config(foreground='#28a745' if weekly_report['net_income'] >= 0 else '#dc3545')

            # Monthly (Current month)
            start_of_month = today.replace(day=1)
            monthly_report = self.controller.report_generator.generate_financial_summary_report(
                start_of_month.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
            )
            self.monthly_revenue_label.config(text=self.controller.report_generator.format_currency(monthly_report['total_revenue']))
            self.monthly_net_profit_label.config(text=self.controller.report_generator.format_currency(monthly_report['net_income']))
            self.monthly_net_profit_label.config(foreground='#28a745' if monthly_report['net_income'] >= 0 else '#dc3545')

            # --- Items Sold (COGS) Today ---
            # Use after(0, lambda: ...) to safely update GUI from a separate thread
            self.after(0, lambda: self.cogs_treeview.delete(*self.cogs_treeview.get_children())) # Clear existing items
            items_sold_cogs = self.controller.report_generator.get_cogs_per_item_today()
            for item in items_sold_cogs:
                self.after(0, lambda item=item: self.cogs_treeview.insert("", "end", values=(
                    item['item_name'],
                    item['quantity_sold'],
                    self.controller.report_generator.format_currency(item['total_selling_value']),
                    self.controller.report_generator.format_currency(item['total_cogs_item'])
                )))

        except Exception as e:
            print(f"Error updating dashboard metrics: {e}")
            # Optionally show an error message in the GUI for the user

    def refresh_data(self):
        """
        Method called when this tab is selected in the notebook.
        Ensures the dashboard metrics are up-to-date.
        """
        self.update_metrics()
