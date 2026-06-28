from wholesaleApp.urls.master import urlpatterns as masterurl
from wholesaleApp.urls.customers import urlpatterns as cusromerurl
#from wholesaleApp.urls.supplier import urlpatterns as supplierurl


urlpatterns = masterurl + cusromerurl