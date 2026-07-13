from django.db import models
from django.contrib.auth.models import User
from wholesaleApp.models.supplier import SupplierMaster
from wholesaleApp.models.products import ProductMaster


# ==================== PURCHASE MASTER (INVOICE HEADER) ====================
class PurchaseMaster(models.Model):
    supplier = models.ForeignKey(SupplierMaster, on_delete=models.PROTECT, related_name='purchases', verbose_name="Supplier")
    invoice_number = models.CharField(max_length=100, verbose_name="Supplier Invoice / Bill Number")
    invoice_date = models.DateField(verbose_name="Invoice Date")
    remarks = models.TextField(blank=True, null=True)

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, verbose_name="Total Invoice Amount")

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-invoice_date', '-id']

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier.name}"


# ==================== PURCHASE ITEM (BATCHWISE LINE ITEMS) ====================
class PurchaseItem(models.Model):
    purchase = models.ForeignKey(PurchaseMaster, on_delete=models.CASCADE, related_name='items', verbose_name="Purchase Invoice")
    product = models.ForeignKey(ProductMaster, on_delete=models.PROTECT, related_name='purchase_items', verbose_name="Product")

    batch_number = models.CharField(max_length=50, verbose_name="Batch Number")
    expiry_date = models.DateField(verbose_name="Expiry Date")

    quantity = models.PositiveIntegerField(default=0, verbose_name="Purchase Quantity")
    free_quantity = models.PositiveIntegerField(default=0, verbose_name="Free / Scheme Quantity")

    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Purchase Rate (per unit)")
    mrp = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="MRP (per unit)")
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00, verbose_name="GST Rate (%)")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Discount (%)")

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Net Amount")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} (Batch: {self.batch_number}) x {self.quantity}"

    @property
    def total_quantity(self):
        """Total physical units added to stock (purchased + free)."""
        return self.quantity + self.free_quantity

    def calculate_amount(self):
        """Compute net amount = (qty * rate) - discount% + gst% on discounted value."""
        taxable_value = (self.quantity or 0) * (self.purchase_rate or 0)
        discount_amount = taxable_value * (self.discount_percent or 0) / 100
        after_discount = taxable_value - discount_amount
        gst_amount = after_discount * (self.gst_rate or 0) / 100
        return round(after_discount + gst_amount, 2)

    def save(self, *args, **kwargs):
        self.amount = self.calculate_amount()
        super().save(*args, **kwargs)


# ==================== BATCH STOCK (BATCHWISE STOCK LEDGER) ====================
class BatchStock(models.Model):
    """
    Auto-maintained batchwise stock. A row here represents the current
    available quantity of a product for a specific batch + expiry combination.
    It is created/updated automatically whenever a purchase entry is
    created, edited, or deleted (see wholesaleApp.views.purchase_views).
    """
    product = models.ForeignKey(ProductMaster, on_delete=models.PROTECT, related_name='batch_stocks', verbose_name="Product")
    batch_number = models.CharField(max_length=50, verbose_name="Batch Number")
    expiry_date = models.DateField(verbose_name="Expiry Date")

    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Latest Purchase Rate")
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="MRP")
    quantity = models.IntegerField(default=0, verbose_name="Available Stock Quantity")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Batch Stock"
        verbose_name_plural = "Batch Stocks"
        ordering = ['product__name', 'expiry_date']
        unique_together = ('product', 'batch_number', 'expiry_date')

    def __str__(self):
        return f"{self.product.name} (Batch: {self.batch_number}) - {self.quantity} units"
