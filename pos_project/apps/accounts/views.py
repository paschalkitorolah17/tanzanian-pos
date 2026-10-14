from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth import logout


class PosLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if getattr(user, 'role', None) in ['cashier', 'sales_associate']:
            return reverse_lazy('pos')
        return reverse_lazy('dashboard')


class PosLogoutView(View):
    """
    Simple logout that always redirects to the login page.
    Avoids Django's default "Logged out" template.
    """
    def get(self, request):
        logout(request)
        return redirect('accounts:login')

    def post(self, request):
        logout(request)
        return redirect('accounts:login')
