from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django_filters.views import FilterView
from django.urls import reverse_lazy
from django.contrib.auth.models import User

from .utils import create_plt
from budget_manager.forms import CurrencyFilter, UpdateUserForm
from .filtersets import ExpenseFilter, IncomeFilter
from budget_manager.models import Expense, Source, Category, Income, Currency


class BalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        currency_filter_form = CurrencyFilter(self.request.GET)
        if currency_filter_form.data.__len__() == 0:
            filtered_currency_pk = 1
        else:
            filtered_currency_pk = currency_filter_form.data["currency_filter"]

        total_expense = round(Expense.objects.filter(user=self.request.user).filter(
            currency__id=filtered_currency_pk).aggregate(Sum("cost", default=0))["cost__sum"], ndigits=2)
        total_income = round(Income.objects.filter(user=self.request.user).filter(
            currency__id=filtered_currency_pk).aggregate(Sum("amount", default=0))["amount__sum"], ndigits=2)
        total_balance = round(total_income - total_expense, ndigits=2)
        monthly_income = Income.objects.filter(user=self.request.user).annotate(
            month=ExtractMonth('income_date')).values('month').annotate(total_amount=Sum('amount'))
        monthly_expense = Expense.objects.filter(user=self.request.user).annotate(
            month=ExtractMonth('expense_date')).values('month').annotate(total_amount=Sum('cost'))

        context = {
            'total_expense': total_expense,
            'total_income': total_income,
            'total_balance': total_balance,
            'monthly_income': monthly_income,
            'monthly_expense': monthly_expense,
            "currency_filter_form": currency_filter_form,
            "displayed_currency": Currency.objects.get(pk=filtered_currency_pk)
        }

        create_plt(total_expense, total_income)

        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    template_name = 'expenses_form.html'
    fields = ['name', 'cost', 'expense_date', 'currency', 'category']
    success_url = reverse_lazy('expense-filter-list')

    def form_valid(self, form):
        """Object creation method based on given model. Saves logged user
        as object creator"""
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        """Displays only categories made by currently logged user"""
        form = super(ExpenseCreateView, self).get_form(*args, **kwargs)
        form.fields['category'].queryset = Category.objects.filter(
            user=self.request.user) | Category.objects.filter(user=None)
        field_labels = {'name': 'Nazwa',
                        'cost': 'Koszt',
                        'expense_date': 'Data wydatku',
                        'currency': 'Waluta',
                        'category': 'Kategoria'}

        for field_name, label in field_labels.items():
            if field_name in form.fields:
                form.fields[field_name].label = label
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
        """Object creation method based on given model. Saves logged user
            as object creator"""
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = 'categories_form.html'
    fields = ['name']
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """Object creation method based on given model. Saves logged user
            as object creator"""
        form.instance.user = self.request.user
        return super().form_valid(form)


class IncomeCreateView(LoginRequiredMixin, CreateView):
    model = Income
    template_name = 'income_form.html'
    fields = ['amount', 'source', 'income_date', 'currency']
    success_url = reverse_lazy('income-list')

    def form_valid(self, form):
        """Object creation method based on given model. Saves logged user
            as object creator"""
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_form(self, *args, **kwargs):
        """Displays only categories made by currently logged user"""
        form = super(IncomeCreateView, self).get_form(*args, **kwargs)
        form.fields['source'].queryset = Source.objects.filter(
            user=self.request.user) | Source.objects.filter(user=None)

        field_labels = {'amount': 'Wartość',
                        'income_date': 'Data przychodu',
                        'source': 'Źródło',
                        'currency': 'Waluta'}

        for field_name, label in field_labels.items():
            if field_name in form.fields:
                form.fields[field_name].label = label
        return form


class IncomeListView(LoginRequiredMixin, FilterView):
    context_object_name = 'income'
    filterset_class = IncomeFilter
    template_name = 'income_list.html'

    def get_queryset(self):
        """Displays only objects made by currently logged user"""
        return Income.objects.filter(user=self.request.user)


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
    form_class = UpdateUserForm
    model = User
    template_name = 'user_update.html'
    success_url = reverse_lazy('user-list')

    def get_initial(self):
        initial_values = super().get_initial()
        initial_values["username"] = self.request.user.username
        initial_values["first_name"] = self.request.user.first_name
        initial_values["last_name"] = self.request.user.last_name
        initial_values['"email"'] = self.request.user.email
        return initial_values
