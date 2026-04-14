"""
Odoo JSON-RPC Connector

Connects to Odoo 19.0 ERP via JSON-RPC API for accounting operations.
Supports invoices, customers, payments, and products.

Usage:
    python scripts/odoo_connector.py --test-connection
    python scripts/odoo_connector.py --create-invoice --customer "Test Customer" --amount 100.00
    python scripts/odoo_connector.py --sync-invoices --last-30-days
    python scripts/odoo_connector.py --list-customers
"""

import os
import sys
import json
import logging
import argparse
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class OdooConnector:
    """
    Odoo JSON-RPC API Connector.
    
    Implements Odoo 19.0 External API specification.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        Initialize Odoo connector.
        
        Args:
            url: Odoo URL (default: from env ODOO_URL)
            db: Database name (default: from env ODOO_DB)
            username: Username or email (default: from env ODOO_USERNAME)
            password: Password (default: from env ODOO_PASSWORD)
            api_key: API key (optional, from env ODOO_API_KEY)
            dry_run: If True, log actions without executing
        """
        self.url = url or os.getenv('ODOO_URL', 'http://localhost:8069')
        self.db = db or os.getenv('ODOO_DB', 'ai_employee')
        self.username = username or os.getenv('ODOO_USERNAME', 'admin')
        self.password = password or os.getenv('ODOO_PASSWORD')
        self.api_key = api_key or os.getenv('ODOO_API_KEY')
        self.dry_run = dry_run
        
        self.uid = None  # User ID after authentication
        self.session = requests.Session()
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info(f'Initialized OdooConnector for {self.url}/{self.db}')
    
    def _setup_logging(self):
        """Setup logging."""
        log_dir = Path('Logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'odoo_{datetime.now().strftime("%Y-%m-%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger('OdooConnector')
    
    def _json_rpc_call(self, endpoint: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Make JSON-RPC call to Odoo.
        
        Args:
            endpoint: API endpoint (e.g., '/web/session/authenticate')
            params: Request parameters
            
        Returns:
            Response data or None
        """
        url = f"{self.url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': params,
            'id': 1
        }
        
        if self.dry_run:
            self.logger.info(f'[DRY RUN] Would call {url}')
            self.logger.info(f'[DRY RUN] Params: {json.dumps(params, indent=2)}')
            return None
        
        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                error = result['error']
                self.logger.error(f'Odoo API Error: {error.get("data", {}).get("message", error)}')
                return None
            
            return result.get('result', {})
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Network error: {e}')
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f'JSON decode error: {e}')
            return None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Odoo.
        
        Returns:
            True if authentication successful
        """
        if self.uid:
            return True  # Already authenticated
        
        self.logger.info(f'Authenticating as {self.username}...')
        
        params = {
            'db': self.db,
            'login': self.username,
            'password': self.password,
        }
        
        # Add API key if available
        if self.api_key:
            params['api_key'] = self.api_key
        
        result = self._json_rpc_call('/web/session/authenticate', params)
        
        if result and result.get('uid'):
            self.uid = result['uid']
            self.logger.info(f'✅ Authenticated successfully (UID: {self.uid})')
            return True
        else:
            self.logger.error('❌ Authentication failed')
            return False
    
    def test_connection(self) -> bool:
        """
        Test Odoo connection.
        
        Returns:
            True if connection successful
        """
        print("Testing Odoo connection...")
        
        # Test basic connectivity
        try:
            response = requests.get(f"{self.url}/web/webclient/version_info", timeout=10)
            if response.status_code == 200:
                print(f"✅ Odoo server reachable at {self.url}")
            else:
                print(f"⚠️ Odoo server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot reach Odoo server: {e}")
            return False
        
        # Test authentication
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        print(f"✅ Authenticated as {self.username}")
        
        # Get available models
        models = self.search_read(
            'ir.model',
            domain=[('model', 'like', 'account')],
            fields=['name', 'model'],
            limit=10
        )
        
        if models:
            print(f"✅ Found {len(models)} accounting models")
            for model in models[:5]:
                print(f"   - {model.get('model', 'unknown')}")
        else:
            print("⚠️ No accounting models found")
        
        # Get company info
        companies = self.search_read(
            'res.company',
            domain=[],
            fields=['name', 'currency_id'],
            limit=1
        )
        
        if companies:
            company = companies[0]
            print(f"✅ Company: {company.get('name', 'Unknown')}")
        
        print("\n✅ Connection test successful!")
        return True
    
    def execute(
        self,
        model: str,
        method: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None
    ) -> Optional[Any]:
        """
        Execute a method on an Odoo model.
        
        Args:
            model: Model name (e.g., 'account.move')
            method: Method name (e.g., 'create')
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Method result
        """
        if not self.authenticate():
            return None
        
        params = {
            'model': model,
            'method': method,
            'args': args or [],
            'kwargs': kwargs or {}
        }
        
        result = self._json_rpc_call('/web/dataset/call', params)
        
        if result is None:
            self.logger.error(f'Failed to execute {method} on {model}')
        
        return result
    
    def search_read(
        self,
        model: str,
        domain: List[Any] = None,
        fields: List[str] = None,
        offset: int = 0,
        limit: int = 80,
        order: str = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search and read records from a model.
        
        Args:
            model: Model name
            domain: Search domain (Odoo domain syntax)
            fields: Fields to return
            offset: Result offset
            limit: Maximum records to return
            order: Order by field
            
        Returns:
            List of records
        """
        if not self.authenticate():
            return None
        
        params = {
            'model': model,
            'domain': domain or [],
            'fields': fields or [],
            'offset': offset,
            'limit': limit,
        }
        
        if order:
            params['order'] = order
        
        result = self._json_rpc_call('/web/dataset/search_read', params)
        
        if result and 'records' in result:
            return result['records']
        
        return None
    
    # === Invoice Operations ===
    
    def create_invoice(
        self,
        partner_name: str,
        partner_email: str = None,
        amount: float = 0.0,
        invoice_type: str = 'out_invoice',
        invoice_date: str = None,
        due_date: str = None,
        description: str = None,
        product_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new invoice.
        
        Args:
            partner_name: Customer name
            partner_email: Customer email
            amount: Invoice amount (without tax)
            invoice_type: 'out_invoice' (customer) or 'in_invoice' (vendor)
            invoice_date: Invoice date (YYYY-MM-DD)
            due_date: Due date (YYYY-MM-DD)
            description: Invoice description
            product_name: Product/service name
            
        Returns:
            Invoice data or None
        """
        if not self.authenticate():
            return None
        
        self.logger.info(f'Creating invoice for {partner_name}: ${amount}')
        
        if self.dry_run:
            self.logger.info('[DRY RUN] Would create invoice')
            return {
                'id': 0,
                'name': 'DRY_RUN_INVOICE',
                'partner_name': partner_name,
                'amount': amount
            }
        
        try:
            # Find or create partner
            partner_id = self._find_or_create_partner(partner_name, partner_email)
            
            if not partner_id:
                self.logger.error('Failed to create/find partner')
                return None
            
            # Find or create product
            product_id = None
            if product_name:
                product_id = self._find_or_create_product(product_name, amount)
            
            # Prepare invoice lines
            invoice_lines = []
            if product_id:
                invoice_lines = [(0, 0, {
                    'product_id': product_id,
                    'name': description or product_name,
                    'price_unit': amount,
                    'quantity': 1.0,
                })]
            else:
                invoice_lines = [(0, 0, {
                    'name': description or 'Service',
                    'price_unit': amount,
                    'quantity': 1.0,
                })]
            
            # Create invoice
            invoice_data = {
                'move_type': invoice_type,
                'partner_id': partner_id,
                'invoice_date': invoice_date or datetime.now().strftime('%Y-%m-%d'),
                'invoice_date_due': due_date or (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'invoice_line_ids': invoice_lines,
            }
            
            invoice_id = self.execute('account.move', 'create', [invoice_data])
            
            if invoice_id:
                self.logger.info(f'✅ Invoice created with ID: {invoice_id}')
                
                # Get full invoice data
                invoice = self.search_read(
                    'account.move',
                    domain=[('id', '=', invoice_id)],
                    fields=['name', 'partner_id', 'amount_total', 'state'],
                    limit=1
                )
                
                if invoice:
                    return invoice[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f'Error creating invoice: {e}', exc_info=True)
            return None
    
    def _find_or_create_partner(
        self,
        name: str,
        email: str = None
    ) -> Optional[int]:
        """
        Find existing partner or create new one.
        
        Args:
            name: Partner name
            email: Partner email
            
        Returns:
            Partner ID or None
        """
        # Try to find existing partner
        if email:
            partners = self.search_read(
                'res.partner',
                domain=[('email', '=', email)],
                fields=['id'],
                limit=1
            )
            
            if partners:
                self.logger.info(f'Found existing partner: {name}')
                return partners[0]['id']
        
        # Create new partner
        partner_data = {
            'name': name,
            'email': email,
            'customer_rank': 1,
        }
        
        partner_id = self.execute('res.partner', 'create', [partner_data])
        
        if partner_id:
            self.logger.info(f'Created new partner: {name} (ID: {partner_id})')
            return partner_id
        
        return None
    
    def _find_or_create_product(
        self,
        name: str,
        price: float = 0.0,
        product_type: str = 'service'
    ) -> Optional[int]:
        """
        Find existing product or create new one.
        
        Args:
            name: Product name
            price: Product price
            product_type: 'service' or 'product'
            
        Returns:
            Product ID or None
        """
        # Try to find existing product
        products = self.search_read(
            'product.template',
            domain=[('name', '=', name)],
            fields=['id'],
            limit=1
        )
        
        if products:
            self.logger.info(f'Found existing product: {name}')
            return products[0]['id']
        
        # Create new product
        product_data = {
            'name': name,
            'type': product_type,
            'list_price': price,
            'sale_ok': True,
            'purchase_ok': False,
        }
        
        product_id = self.execute('product.template', 'create', [product_data])
        
        if product_id:
            self.logger.info(f'Created new product: {name} (ID: {product_id})')
            return product_id
        
        return None
    
    def get_invoices(
        self,
        partner_name: str = None,
        state: str = None,
        last_days: int = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get invoices with optional filters.
        
        Args:
            partner_name: Filter by customer name
            state: Filter by state (draft, posted, paid, cancelled)
            last_days: Filter by date (last N days)
            
        Returns:
            List of invoices
        """
        domain = []
        
        if partner_name:
            domain.append(('partner_id', 'ilike', partner_name))
        
        if state:
            domain.append(('state', '=', state))
        
        if last_days:
            date_from = (datetime.now() - timedelta(days=last_days)).strftime('%Y-%m-%d')
            domain.append(('invoice_date', '>=', date_from))
        
        invoices = self.search_read(
            'account.move',
            domain=domain,
            fields=['name', 'partner_id', 'invoice_date', 'amount_total', 'state', 'payment_state'],
            order='invoice_date DESC',
            limit=50
        )
        
        return invoices or []
    
    def sync_invoices(self, last_days: int = 30) -> List[Dict[str, Any]]:
        """
        Sync invoices from Odoo to local vault.
        
        Args:
            last_days: Number of days to sync
            
        Returns:
            List of synced invoices
        """
        self.logger.info(f'Syncing invoices from last {last_days} days...')
        
        invoices = self.get_invoices(last_days=last_days)
        
        if not invoices:
            self.logger.info('No invoices found')
            return []
        
        # Create sync file in Accounting folder
        vault_path = Path('AI_Employee_Vault')
        accounting_path = vault_path / 'Accounting'
        accounting_path.mkdir(exist_ok=True)
        
        sync_file = accounting_path / f'odoo_invoices_{datetime.now().strftime("%Y-%m-%d")}.md'
        
        content = f"""---
synced: {datetime.now().isoformat()}
source: Odoo {self.url}
database: {self.db}
period: Last {last_days} days
---

# Odoo Invoices Sync

## Summary
- Total Invoices: {len(invoices)}
- Total Amount: ${sum(inv.get('amount_total', 0) for inv in invoices):.2f}

## Invoices

| # | Invoice | Customer | Date | Amount | Status | Payment |
|---|---------|----------|------|--------|--------|---------|
"""
        
        for i, inv in enumerate(invoices, 1):
            partner = inv.get('partner_id', ['', 'Unknown'])[1] if isinstance(inv.get('partner_id'), list) else inv.get('partner_id', 'Unknown')
            content += f"| {i} | {inv.get('name', 'N/A')} | {partner} | {inv.get('invoice_date', 'N/A')} | ${inv.get('amount_total', 0):.2f} | {inv.get('state', 'N/A')} | {inv.get('payment_state', 'N/A')} |\n"
        
        content += f"\n---\n*Generated by OdooConnector on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        sync_file.write_text(content, encoding='utf-8')
        
        self.logger.info(f'✅ Synced {len(invoices)} invoices to {sync_file}')
        
        return invoices
    
    # === Payment Operations ===
    
    def register_payment(
        self,
        invoice_id: int,
        amount: float = None,
        payment_date: str = None,
        payment_method: str = 'manual'
    ) -> Optional[Dict[str, Any]]:
        """
        Register payment for an invoice.
        
        Args:
            invoice_id: Invoice ID
            amount: Payment amount (default: full amount)
            payment_date: Payment date
            payment_method: Payment method
            
        Returns:
            Payment data
        """
        if not self.authenticate():
            return None
        
        self.logger.info(f'Registering payment for invoice {invoice_id}')
        
        if self.dry_run:
            self.logger.info('[DRY RUN] Would register payment')
            return {'id': 0, 'invoice_id': invoice_id, 'amount': amount}
        
        try:
            # Get invoice data
            invoice = self.search_read(
                'account.move',
                domain=[('id', '=', invoice_id)],
                fields=['name', 'amount_total', 'amount_residual'],
                limit=1
            )
            
            if not invoice:
                self.logger.error(f'Invoice {invoice_id} not found')
                return None
            
            invoice_data = invoice[0]
            
            if amount is None:
                amount = invoice_data.get('amount_residual', invoice_data.get('amount_total', 0))
            
            # Create payment wizard
            payment_wizard = self.execute(
                'account.payment.register',
                'create',
                [{
                    'payment_type': 'inbound',
                    'payment_method_line_id': payment_method,
                    'amount': amount,
                    'payment_date': payment_date or datetime.now().strftime('%Y-%m-%d'),
                }]
            )
            
            if payment_wizard:
                # Create payment
                payment_result = self.execute(
                    'account.payment.register',
                    'create_payments',
                    [[payment_wizard]]
                )
                
                self.logger.info(f'✅ Payment registered: ${amount}')
                return {'id': payment_result, 'amount': amount}
            
            return None
            
        except Exception as e:
            self.logger.error(f'Error registering payment: {e}', exc_info=True)
            return None
    
    # === Customer Operations ===
    
    def list_customers(self, limit: int = 50) -> Optional[List[Dict[str, Any]]]:
        """
        List all customers.
        
        Args:
            limit: Maximum customers to return
            
        Returns:
            List of customers
        """
        customers = self.search_read(
            'res.partner',
            domain=[('customer_rank', '>', 0)],
            fields=['name', 'email', 'phone', 'city', 'country_id'],
            order='name',
            limit=limit
        )
        
        return customers or []
    
    def get_customer(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get customer by name or email.
        
        Args:
            identifier: Customer name or email
            
        Returns:
            Customer data
        """
        customers = self.search_read(
            'res.partner',
            domain=['|', ('name', 'ilike', identifier), ('email', '=', identifier)],
            fields=['name', 'email', 'phone', 'street', 'city', 'country_id', 'customer_rank'],
            limit=1
        )
        
        if customers:
            return customers[0]
        
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Odoo JSON-RPC Connector')
    parser.add_argument('--test-connection', action='store_true', help='Test Odoo connection')
    parser.add_argument('--create-invoice', action='store_true', help='Create new invoice')
    parser.add_argument('--customer', type=str, help='Customer name')
    parser.add_argument('--email', type=str, help='Customer email')
    parser.add_argument('--amount', type=float, help='Invoice amount')
    parser.add_argument('--description', type=str, help='Invoice description')
    parser.add_argument('--product', type=str, help='Product name')
    parser.add_argument('--sync-invoices', action='store_true', help='Sync invoices from Odoo')
    parser.add_argument('--last-days', type=int, default=30, help='Days to sync')
    parser.add_argument('--list-customers', action='store_true', help='List all customers')
    parser.add_argument('--get-customer', type=str, help='Get customer by name/email')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual changes)')
    
    args = parser.parse_args()
    
    # Create connector
    connector = OdooConnector(dry_run=args.dry_run)
    
    # Execute requested operation
    if args.test_connection:
        success = connector.test_connection()
        sys.exit(0 if success else 1)
    
    elif args.create_invoice:
        if not args.customer or not args.amount:
            print("Error: --customer and --amount are required")
            sys.exit(1)
        
        invoice = connector.create_invoice(
            partner_name=args.customer,
            partner_email=args.email,
            amount=args.amount,
            description=args.description,
            product_name=args.product
        )
        
        if invoice:
            print(f"✅ Invoice created: {invoice.get('name', 'N/A')}")
            print(f"   Customer: {invoice.get('partner_id', ['N/A'])[1] if isinstance(invoice.get('partner_id'), list) else invoice.get('partner_id')}")
            print(f"   Amount: ${invoice.get('amount_total', 0):.2f}")
            print(f"   Status: {invoice.get('state', 'N/A')}")
        else:
            print("❌ Failed to create invoice")
            sys.exit(1)
    
    elif args.sync_invoices:
        invoices = connector.sync_invoices(last_days=args.last_days)
        print(f"✅ Synced {len(invoices)} invoices")
    
    elif args.list_customers:
        customers = connector.list_customers()
        if customers:
            print(f"Found {len(customers)} customers:\n")
            for cust in customers:
                print(f"  - {cust['name']} ({cust.get('email', 'N/A')})")
        else:
            print("No customers found")
    
    elif args.get_customer:
        customer = connector.get_customer(args.get_customer)
        if customer:
            print(f"Customer found:")
            print(f"  Name: {customer['name']}")
            print(f"  Email: {customer.get('email', 'N/A')}")
            print(f"  Phone: {customer.get('phone', 'N/A')}")
            print(f"  City: {customer.get('city', 'N/A')}")
        else:
            print("Customer not found")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
