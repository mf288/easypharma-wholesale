from django.test import TestCase
from django.urls import reverse
from wholesaleApp.models import (
    CompanyMaster, DrugMaster, ProductTypeMaster, ProductMaster,
    SupplierMaster, ProductBatch, PurchaseOrder, PurchaseOrderItem,
    PurchaseEntry, PurchaseEntryItem, AreaMaster, SubareaMaster, CustomerMaster,
    SalesInvoice, SalesInvoiceItem
)

class MasterDataTests(TestCase):
    def setUp(self):
        # Create master data
        self.company = CompanyMaster.objects.create(name="Cipla Ltd", code="CIPLA")
        self.drug = DrugMaster.objects.create(name="Paracetamol 500mg")
        self.p_type = ProductTypeMaster.objects.create(name="Tablet")
        self.product = ProductMaster.objects.create(
            name="Crocin 650mg",
            company=self.company,
            drug_composition=self.drug,
            product_type=self.p_type,
            pack_size="10 Tab",
            hsn_code="3004",
            gst_rate=12.00,
            min_stock=10
        )

    def test_model_creation(self):
        # Verify model data saved correctly
        self.assertEqual(CompanyMaster.objects.count(), 1)
        self.assertEqual(DrugMaster.objects.count(), 1)
        self.assertEqual(ProductTypeMaster.objects.count(), 1)
        self.assertEqual(ProductMaster.objects.count(), 1)
        
        self.assertEqual(self.product.company.name, "Cipla Ltd")
        self.assertEqual(self.product.drug_composition.name, "Paracetamol 500mg")
        self.assertEqual(self.product.product_type.name, "Tablet")

    def test_view_status_codes(self):
        # Test company list view
        response = self.client.get(reverse('company_list'))
        self.assertEqual(response.status_code, 200)

        # Test drug list view
        response = self.client.get(reverse('drug_list'))
        self.assertEqual(response.status_code, 200)

        # Test product type list view
        response = self.client.get(reverse('type_list'))
        self.assertEqual(response.status_code, 200)

        # Test product list view
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)


class PurchaseModuleTests(TestCase):
    def setUp(self):
        # Create base master data
        self.supplier = SupplierMaster.objects.create(
            name="Alpha Pharma Pvt Ltd",
            mobile="9876543210",
            city="Mumbai",
            state="Maharashtra"
        )
        self.company = CompanyMaster.objects.create(name="Cipla Ltd", code="CIPLA")
        self.p_type = ProductTypeMaster.objects.create(name="Tablet")
        self.product = ProductMaster.objects.create(
            name="Crocin 650mg",
            company=self.company,
            product_type=self.p_type,
            pack_size="10 Tab",
            gst_rate=12.00
        )

    def test_purchase_order_creation(self):
        po = PurchaseOrder.objects.create(
            po_number="PO-TEST-0001",
            supplier=self.supplier,
            po_date="2026-07-13",
            status="Sent"
        )
        item = PurchaseOrderItem.objects.create(
            purchase_order=po,
            product=self.product,
            quantity=100,
            expected_rate=15.00
        )
        
        # Verify total amount calculation
        self.assertEqual(item.total_amount, 1500.00)
        
        # Verify status code for PO views
        response = self.client.get(reverse('po_list'))
        self.assertEqual(response.status_code, 200)

    def test_purchase_entry_inventory_and_balance_update(self):
        # Initial supplier balance should be 0
        self.assertEqual(float(self.supplier.opening_balance), 0.00)
        
        # Initial stock should be 0
        self.assertEqual(ProductBatch.objects.filter(product=self.product).count(), 0)

        # Post data to simulate invoice save
        # Taxable value: 10 packs * 100 Rs = 1000 Rs
        # 10% disc = 100 Rs, taxable after disc = 900 Rs
        # 12% GST = 108 Rs
        # Total amount = 1008 Rs
        response = self.client.post(reverse('purchase_entry_create'), {
            'supplier': self.supplier.id,
            'invoice_number': 'BILL-1002',
            'invoice_date': '2026-07-13',
            'gross_amount': '900.00',
            'discount_amount': '100.00',
            'gst_amount': '108.00',
            'net_amount': '1008.00',
            
            # Arrays
            'product[]': [self.product.id],
            'batch_number[]': ['B101'],
            'expiry_date[]': ['2028-12-31'],
            'mrp[]': ['120.00'],
            'purchase_rate[]': ['100.00'],
            'sale_rate[]': ['110.00'],
            'quantity[]': [10],
            'free_quantity[]': [2],
            'discount_percentage[]': [10.00],
            'total_amount[]': [1008.00]
        })
        
        # Verify redirect to entry list
        self.assertRedirects(response, reverse('purchase_entry_list'))

        # Verify entry created
        self.assertEqual(PurchaseEntry.objects.count(), 1)
        self.assertEqual(PurchaseEntryItem.objects.count(), 1)
        
        # Verify batch inventory created with correct quantity (billed 10 + free 2 = 12)
        self.assertEqual(ProductBatch.objects.count(), 1)
        batch = ProductBatch.objects.first()
        self.assertEqual(batch.batch_number, 'B101')
        self.assertEqual(batch.quantity, 12)
        
        # Verify supplier balance updated
        self.supplier.refresh_from_db()
        self.assertEqual(float(self.supplier.opening_balance), 1008.00)


class AreaMasterTests(TestCase):
    def setUp(self):
        self.area = AreaMaster.objects.create(city="Mumbai", code="MUM")
        self.subarea = SubareaMaster.objects.create(area=self.area, name="Andheri West")

    def test_area_list_view(self):
        response = self.client.get(reverse('area_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mumbai")
        self.assertContains(response, "Andheri West")

    def test_area_create(self):
        response = self.client.post(reverse('area_create'), {
            'city': 'Thane',
            'code': 'THN'
        })
        self.assertRedirects(response, reverse('area_list'))
        self.assertEqual(AreaMaster.objects.filter(city="Thane").count(), 1)


class SalesModuleTests(TestCase):
    def setUp(self):
        # Create base master data
        self.area = AreaMaster.objects.create(city="Mumbai", code="MUM")
        self.customer = CustomerMaster.objects.create(
            name="Apex Chemist",
            mobile="9988776655",
            area=self.area,
            city="Mumbai",
            state="Maharashtra"
        )
        self.company = CompanyMaster.objects.create(name="Alkem Ltd", code="ALKEM")
        self.p_type = ProductTypeMaster.objects.create(name="Capsule")
        self.product = ProductMaster.objects.create(
            name="Amoxicillin 500mg",
            company=self.company,
            product_type=self.p_type,
            pack_size="10 Caps",
            gst_rate=12.00,
            scheme_qty=10,
            scheme_free=1
        )
        # Add stock batch
        self.batch = ProductBatch.objects.create(
            product=self.product,
            batch_number="B-AMX-99",
            expiry_date="2027-06-30",
            mrp=150.00,
            purchase_rate=100.00,
            sale_rate=120.00,
            quantity=100
        )

    def test_sales_invoice_creation_and_stock_deduction(self):
        # Initial values
        self.assertEqual(self.batch.quantity, 100)
        self.assertEqual(float(self.customer.opening_balance), 0.00)

        # Post invoice request
        # 20 quantity should auto calculate 2 free items -> 22 packs deducted
        # Taxable value: 20 packs * 120 Rs = 2400 Rs
        # 12% GST = 288 Rs
        # Net Amount = 2688 Rs
        response = self.client.post(reverse('invoice_create'), {
            'customer': self.customer.id,
            'invoice_date': '2026-07-13',
            'gross_amount': '2400.00',
            'discount_amount': '0.00',
            'gst_amount': '288.00',
            'net_amount': '2688.00',
            
            # Arrays
            'product[]': [self.product.id],
            'batch[]': [self.batch.id],
            'sale_rate[]': ['120.00'],
            'quantity[]': [20],
            'free_quantity[]': [2],
            'discount_percentage[]': [0.00],
            'total_amount[]': [2688.00]
        })

        # Verify redirect
        self.assertRedirects(response, reverse('invoice_list'))

        # Verify database invoice record
        self.assertEqual(SalesInvoice.objects.count(), 1)
        self.assertEqual(SalesInvoiceItem.objects.count(), 1)

        # Verify batch stock deducted (100 - (20 + 2) = 78)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 78)

        # Verify customer outstanding updated
        self.customer.refresh_from_db()
        self.assertEqual(float(self.customer.opening_balance), 2688.00)

    def test_insufficient_stock_prevention(self):
        # Post invoice requesting 150 items (exceeding stock of 100)
        response = self.client.post(reverse('invoice_create'), {
            'customer': self.customer.id,
            'invoice_date': '2026-07-13',
            'gross_amount': '18000.00',
            'discount_amount': '0.00',
            'gst_amount': '2160.00',
            'net_amount': '20160.00',
            
            'product[]': [self.product.id],
            'batch[]': [self.batch.id],
            'sale_rate[]': ['120.00'],
            'quantity[]': [150],
            'free_quantity[]': [0],
            'discount_percentage[]': [0.00],
            'total_amount[]': [20160.00]
        })

        # Verify that it redirects back to create invoice page on failure
        self.assertRedirects(response, reverse('invoice_create'))
        
        # Verify no invoice was saved
        self.assertEqual(SalesInvoice.objects.count(), 0)

        # Verify stock batch remains unchanged (100)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.quantity, 100)


from django.contrib.auth.models import User
from wholesaleApp.models.permissions import AppGroupModule, AppFeature, UserFeaturePermission

class PermissionMatrixTests(TestCase):
    def setUp(self):
        # Create a test employee user
        self.employee = User.objects.create_user(username="ramesh", password="password123")
        
        # Seed permissions
        from wholesaleApp.views.security_helpers import seed_default_permissions
        seed_default_permissions()
        
        self.sales_create_feature = AppFeature.objects.get(codename="sales_create")
        self.purchase_create_feature = AppFeature.objects.get(codename="purchase_create")
        
    def test_unauthorized_user_is_blocked_from_invoicing(self):
        self.client.force_login(self.employee)
        
        # Try to view invoice creation
        response = self.client.get(reverse('invoice_create'))
        self.assertEqual(response.status_code, 302) # Redirects with permission denied
        self.assertRedirects(response, reverse('home'))
        
    def test_authorized_user_can_access_invoicing(self):
        self.client.force_login(self.employee)
        
        # Grant sales_create permission
        UserFeaturePermission.objects.create(
            user=self.employee,
            feature=self.sales_create_feature,
            is_granted=True
        )
        
        response = self.client.get(reverse('invoice_create'))
        self.assertEqual(response.status_code, 200) # Access granted!
        
    def test_owner_permissions_matrix_view_access(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('user_permission_matrix'))
        self.assertEqual(response.status_code, 302) # Blocked!
        
        # Owner superuser has access
        self.owner = User.objects.create_superuser(username="owner", password="password")
        self.client.force_login(self.owner)
        response = self.client.get(reverse('user_permission_matrix'))
        self.assertEqual(response.status_code, 200) # Access granted!


class UserManagementCRUDTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(username="ramesh", password="password123")
        self.owner = User.objects.create_superuser(username="owner", password="password")

    def test_unauthorized_user_blocked_from_user_management(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_owner_can_manage_users(self):
        self.client.force_login(self.owner)
        
        # 1. List
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Create User
        response = self.client.post(reverse('user_create'), {
            'username': 'suresh',
            'email': 'suresh@easypharma.com',
            'password': 'password123',
            'role': 'Salesman',
            'mobile': '9876543210'
        })
        self.assertRedirects(response, reverse('user_list'))
        self.assertEqual(User.objects.filter(username="suresh").count(), 1)
        
        # Verify Profile and Role
        suresh = User.objects.get(username="suresh")
        self.assertEqual(suresh.profile.role, "Salesman")
        
        # 3. Edit User
        response = self.client.post(reverse('user_edit', args=[suresh.id]), {
            'username': 'suresh_edit',
            'email': 'suresh_new@easypharma.com',
            'role': 'Delivery Boy',
            'mobile': '9998887776'
        })
        self.assertRedirects(response, reverse('user_list'))
        suresh.refresh_from_db()
        self.assertEqual(suresh.username, "suresh_edit")
        self.assertEqual(suresh.profile.role, "Delivery Boy")
        
        # 4. Delete User
        response = self.client.post(reverse('user_delete', args=[suresh.id]))
        self.assertRedirects(response, reverse('user_list'))
        self.assertEqual(User.objects.filter(username="suresh_edit").count(), 0)


class AuthAndReportsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="biller", password="password123")
        
        # Seed permissions
        from wholesaleApp.views.security_helpers import seed_default_permissions
        seed_default_permissions()

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_reports_dashboard_access(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('reports_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_sales_report_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_sales'))
        self.assertEqual(response.status_code, 200)

    def test_expiry_report_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_expiry'))
        self.assertEqual(response.status_code, 200)

    def test_stock_report_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_stock'))
        self.assertEqual(response.status_code, 200)

    def test_outstanding_report_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_outstanding'))
        self.assertEqual(response.status_code, 200)




