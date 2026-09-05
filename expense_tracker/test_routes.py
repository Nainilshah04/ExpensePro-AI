import unittest
from app import app, db, User, Expense, Budget, Subscription, Group
from services.ocr_service import ocr_parser

class ExpenseProTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_01_favicon(self):
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/svg+xml')

    def test_02_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Expense', response.data)

    def test_03_demo_login(self):
        response = self.client.get('/demo-login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Expense', response.data)

    def test_04_predict_category_api(self):
        response = self.client.get('/api/predict-category?text=Uber+cab+ride')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['category'], 'Transport')

    def test_05_add_and_edit_expense(self):
        self.client.get('/demo-login', follow_redirects=True)
        # Add
        response = self.client.post('/add', data={
            'date': '2026-09-05',
            'amount': '250.00',
            'category': 'Food',
            'note': 'Test Burger',
            'payment_method': 'UPI'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with app.app_context():
            exp = Expense.query.filter_by(note='Test Burger').first()
            self.assertIsNotNone(exp)
            exp_id = exp.id

        # Edit
        response = self.client.post(f'/edit/{exp_id}', data={
            'date': '2026-09-05',
            'amount': '300.00',
            'category': 'Food',
            'note': 'Test Burger Gourmet',
            'payment_method': 'Card'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            updated = db.session.get(Expense, exp_id)
            self.assertEqual(updated.amount, 300.0)
            self.assertEqual(updated.note, 'Test Burger Gourmet')

    def test_06_period_filtering(self):
        self.client.get('/demo-login', follow_redirects=True)
        # Check August 2026 period
        response = self.client.get('/?period=2026-08')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'August 2026', response.data)

        # Check All Time period
        response = self.client.get('/?period=all')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All Time', response.data)

    def test_07_ocr_enhanced_parsing(self):
        raw_bill = """
        MSEDCL Electricity Distribution
        Subject to Thane Jurisdiction
        GSTIN: 27AABCM1234F1Z5
        Bill Date: 17/08/2026
        Due Date: 01/09/2026
        Total Amount Payable: Rs. 15,328.00
        """
        parsed = ocr_parser.parse_text(raw_bill)
        self.assertTrue(parsed["success"])
        # Verify it prioritized Bill Date over Due Date or other dates
        self.assertEqual(parsed["date"], "2026-08-17")
        # Verify amount is extracted accurately
        self.assertEqual(parsed["amount"], 15328.0)
        # Verify merchant ignored "Subject to Thane Jurisdiction"
        self.assertNotIn("jurisdiction", parsed["merchant"].lower())

    def test_08_export_pdf(self):
        self.client.get('/demo-login', follow_redirects=True)
        response = self.client.get('/export/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')

    def test_09_export_excel(self):
        self.client.get('/demo-login', follow_redirects=True)
        response = self.client.get('/export/excel')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    unittest.main()
