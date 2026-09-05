import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
tracker_dir = os.path.join(root_dir, "expense_tracker")
if tracker_dir not in sys.path:
    sys.path.insert(0, tracker_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from expense_tracker.app import (
    app, db, User, Expense, Budget, Subscription, Group, GroupMember, GroupExpense
)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
