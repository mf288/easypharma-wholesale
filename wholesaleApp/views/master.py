from django.shortcuts import render
from django.views import View


class HomeView(View):
    template_name = "include/home.html"

    def get(self, request):
        context = {
            "name": "Wholesale Dashboard Test"
        }
        return render(request, self.template_name, context)