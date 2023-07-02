import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.contrib.auth.models import User

from .filtersets import ExpenseFilter, IncomeFilter
import matplotlib.pyplot as plt
from budget_manager.models import Expense, Source, Category, Income, Currency


class HomePageView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if 4 < datetime.datetime.now().hour < 19:
            greet = 'Dzień dobry'
        else:
            greet = 'Dobry wieczór'

        context['user'] = self.request.user
        context['greet'] = greet

        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    template_name = 'expenses_form.html'
    fields = ['name', 'cost', 'expense_date', 'currency', 'category']
    success_url = reverse_lazy('expense-filter-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        """Displays only categories made by currently logged user"""
        form = super(ExpenseCreateView, self).get_form(*args, **kwargs)
        form.fields['category'].queryset = Category.objects.filter(user=self.request.user)
        return form


class ExpenseList(LoginRequiredMixin, FilterView):
    context_object_name = 'expense'
    filterset_class = ExpenseFilter
    template_name = 'expense_filter_list.html'

    def get_queryset(self):
        """Displays only objects made by currently logged user"""
        return Expense.objects.filter(user=self.request.user)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    template_name = 'expenses_update.html'
    fields = ['name', 'cost', 'expense_date', 'currency', 'category']
    success_url = reverse_lazy('expense-filter-list')
    context_object_name = 'expense'


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses_confirm_delete.html'
    success_url = reverse_lazy('expense-filter-list')


class SourceCreateView(LoginRequiredMixin, CreateView):
    model = Source
    template_name = 'sources_form.html'
    fields = ['name']
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = 'categories_form.html'
    fields = ['name']
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class IncomeCreateView(LoginRequiredMixin, CreateView):
    model = Income
    template_name = 'income_form.html'
    fields = ['amount', 'source', 'income_date', 'currency']
    success_url = reverse_lazy('income-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class IncomeListView(LoginRequiredMixin, FilterView):
    model = Income
    filterset_class = IncomeFilter
    template_name = 'income_list.html'
    fields = ['amount', 'source', 'income_date', 'currency']


class IncomeUpdateView(LoginRequiredMixin, UpdateView):
    model = Income
    template_name = 'income_update.html'
    fields = ['amount', 'source', 'income_date', 'currency']
    success_url = reverse_lazy('income-list')
    context_object_name = 'income'


class IncomeDeleteView(LoginRequiredMixin, DeleteView):
    model = Income
    template_name = 'income_confirm_delete.html'
    success_url = reverse_lazy('income-list')


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'user_list.html'
    fields = ['username', 'first_name', 'last_name', 'email']


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'user_update.html'
    fields = ['username', 'first_name', 'last_name', 'email']
    success_url = reverse_lazy('user-list')


class BalanceView(TemplateView):
    template_name = 'balance.html'

    def get_context_data(self, **kwargs):
        try:
            total_expense = round(Expense.objects.filter(user=self.request.user).filter(
                currency__currency_code="PLN").aggregate(Sum("cost", default=0))["cost__sum"], ndigits=2)
            total_income = round(Income.objects.filter(user=self.request.user).filter(
                currency__currency_code="PLN").aggregate(Sum("amount", default=0))["amount__sum"], ndigits=2)
            total_balance = round(total_income - total_expense, ndigits=2)
            fig = plt.figure(figsize=(8, 5))
            plt.bar(['Wydatki', 'Przychody'], [total_expense, total_income], color=['red', 'green'], width=0.4)
            plt.xlabel('Rodzaj')
            plt.ylabel('Wartość')
            plt.title('Bilans wydatków')
            plt.savefig('budget_manager/static/budget_manager/expense.jpg')

        except TypeError:
            print('Brak danych')

        monthly_income = Income.objects.filter(user=self.request.user).annotate(
            month=TruncMonth('income_date')).values('month').annotate(total_amount=Sum('amount'))
        monthly_expense = Expense.objects.filter(user=self.request.user).annotate(
            month=TruncMonth('expense_date')).values('month').annotate(total_amount=Sum('cost'))

        context = {
            'total_expense': total_expense,
            'total_income': total_income,
            'total_balance': total_balance,
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
        }
    #     context["list_of_currencies"] = Currency.objects.all()
        return context
