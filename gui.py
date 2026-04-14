from aqt.qt import *
from datetime import date, timedelta
from logic import minimize_dates

class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Suspension Tracker")
        self.setMinimumWidth(350)
        self.setModal(True)
        layout = QVBoxLayout(self)
        
        self.event_selector = QComboBox()
        self.event_selector.addItems(["Unsuspended", "Suspended"])
        layout.addWidget(self.event_selector)
        
        # date range input
        range_layout = QHBoxLayout()
        self.start_edit = QDateEdit(date.today() - timedelta(days=7))
        self.start_edit.setCalendarPopup(True)
        self.end_edit = QDateEdit(date.today())
        self.end_edit.setCalendarPopup(True)
        
        range_layout.addWidget(QLabel("Start:"))
        range_layout.addWidget(self.start_edit)
        range_layout.addWidget(QLabel("End:"))
        range_layout.addWidget(self.end_edit)
        layout.addLayout(range_layout)
        
        self.info = QLabel("Select start and end dates to filter cards.")
        self.info.setStyleSheet("font-size: 10px; color: grey;")
        layout.addWidget(self.info)

        # button
        self.search_button = QPushButton("Search")
        self.search_button.setDefault(True)
        self.search_button.clicked.connect(self.accept)
        layout.addWidget(self.search_button)

    def get_selected_dates(self) -> list[date]:
        start_q = self.start_edit.date()
        end_q = self.end_edit.date()
        
        start = date(start_q.year(), start_q.month(), start_q.day())
        end = date(end_q.year(), end_q.month(), end_q.day())
        
        if start > end:
            return []
            
        dates = []
        curr = start
        while curr <= end:
            dates.append(curr)
            curr += timedelta(days=1)
        return dates

    def get_search_string(self) -> str:
        dates = self.get_selected_dates()
        if not dates:
            return ""
        
        event = self.event_selector.currentText().lower()
        minimized = minimize_dates(dates)
        
        parts = [f"tag:suspension-tracker::{event}::{m}" for m in minimized]
        return " OR ".join(parts) if len(parts) > 1 else parts[0]
