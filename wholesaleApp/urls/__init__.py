from wholesaleApp.urls.master import urlpatterns as masterurl
from wholesaleApp.urls.customers import urlpatterns as customerurl
from wholesaleApp.urls.supplier import urlpatterns as supplierurl
from wholesaleApp.urls.products import urlpatterns as producturl


urlpatterns = masterurl + customerurl + supplierurl + producturl
