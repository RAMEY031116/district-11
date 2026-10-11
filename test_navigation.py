"""Run with python test_navigation.py; uses fixture data, never a live database."""
from datetime import date
from pathlib import Path
import sys
import types
import unittest
from streamlit.testing.v1 import AppTest

members = [{'id': 'a', 'name': 'Alex'}, {'id': 'b', 'name': 'Sam'}, {'id': 'c', 'name': 'Jo'}]
expenses = [{'id': 'e', 'paid_by_member_id': 'a', 'amount_pence': 3000,
             'description': 'Groceries', 'expense_date': date.today().isoformat()}]
splits = [{'expense_id': 'e', 'member_id': m['id'], 'share_pence': 1000} for m in members]
fixture_db = types.ModuleType('db')
fixture_db.get_or_create_household = lambda *a: {'id': 'home'}
fixture_db.list_members = lambda *a: members
fixture_db.list_expenses = lambda *a: expenses
fixture_db.list_all_expenses = lambda *a: expenses
fixture_db.list_splits = lambda *a: splits
fixture_db.list_settlements = lambda *a: []
fixture_db.list_shopping = lambda *a: []
fixture_db.list_events = lambda *a: []
fixture_db.mark_settlement_paid = lambda *a: recorded.append(a)
recorded = []
sys.modules['db'] = fixture_db

class NavigationTests(unittest.TestCase):
    def app(self):
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        self.assertEqual(list(app.exception), [])
        return app

    def test_dashboard_shortcuts(self):
        for key, destination in [('home_debt', 'Balance'), ('home_shopping', 'Shopping'),
                                 ('home_payments', 'Balance'), ('home_reminders', 'Reminders')]:
            with self.subTest(destination=destination):
                app = self.app()
                app.button(key=key).click().run()
                self.assertEqual(list(app.exception), [])
                self.assertEqual(app.session_state['top_navigation'], destination)
                self.assertTrue(len(app.title))

    def test_specific_debt_is_first_and_receipt_required(self):
        recorded.clear()
        app = self.app()
        app.button(key='home_transfer_1').click().run()
        self.assertEqual(list(app.exception), [])
        pair = app.session_state['focused_transfer']
        self.assertIsNotNone(pair)
        self.assertTrue(any(c.value == 'SELECTED FROM HOME' for c in app.caption))
        payment_keys = [n.key for n in app.number_input]
        self.assertTrue(payment_keys[0].startswith(f'payment_amount_{pair[0]}_{pair[1]}_'))
        submit = next(b for b in app.button if b.label == 'Record received payment')
        submit.click().run()
        self.assertEqual(recorded, [])
        self.assertTrue(any('Confirm that the recipient' in e.value for e in app.error))
        app.checkbox[0].check().run()
        next(b for b in app.button if b.label == 'Record received payment').click().run()
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0][1:3], pair)

    def test_empty_dashboard(self):
        original = fixture_db.list_all_expenses
        fixture_db.list_all_expenses = lambda *a: []
        try:
            app = self.app()
            self.assertIn('£0.00', app.button(key='home_debt').label)
            app.button(key='home_debt').click().run()
            self.assertEqual(list(app.exception), [])
            self.assertTrue(any('No payments are outstanding' in s.value for s in app.success))
        finally:
            fixture_db.list_all_expenses = original

if __name__ == '__main__':
    unittest.main()
