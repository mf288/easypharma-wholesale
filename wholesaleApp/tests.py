from django.test import TestCase
from django.urls import reverse
from wholesaleApp.models import CompanyMaster, DrugMaster, ProductTypeMaster, ProductMaster

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

