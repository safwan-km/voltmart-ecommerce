from orders.models import Order,OrderItem,CouponUsage
from products.models import Product, Category,NewsletterSubscriber
from django.contrib.auth.models import User
from django.db.models import Sum,Q,Count,F

from django.contrib.admin.views.decorators import staff_member_required

from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import timedelta, datetime


from .forms import ProductForm, CategoryForm
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView,DetailView

from django.contrib import messages
from orders.models import Coupon
from .forms import CouponForm


@method_decorator(staff_member_required, name="dispatch")
class DashboardHomeView(View):

    def get(self, request):
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(order_status="PENDING").count()
        total_users = User.objects.count()
        total_products = Product.objects.count()

        revenue = Order.objects.filter(
            payment_status="PAID"
        ).aggregate(
            total=Sum("final_amount")
        )["total"] or 0

        context = {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_users": total_users,
            "total_products": total_products,
            "revenue": revenue,
        }

        return render(request, "dashboard/index.html", context)



@method_decorator(staff_member_required, name="dispatch")
class OrderListView(View):

    def get(self, request):
        orders = Order.objects.select_related("user").all()

        # -------- SEARCH --------
        search = request.GET.get("search")
        if search:
            orders = orders.filter(
                Q(id__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search)
            )

        # -------- STATUS FILTER --------
        status = request.GET.get("status")
        if status:
            orders = orders.filter(order_status=status)

        # -------- DATE FILTER --------
        date_filter = request.GET.get("date")

        if date_filter == "today":
            orders = orders.filter(created_at__date=timezone.now().date())

        elif date_filter == "week":
            orders = orders.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            )

        elif date_filter == "month":
            orders = orders.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            )

        # -------- SORTING --------
        sort = request.GET.get("sort")

        if sort == "oldest":
            orders = orders.order_by("created_at")
        elif sort == "highest":
            orders = orders.order_by("-final_amount")
        elif sort == "lowest":
            orders = orders.order_by("final_amount")
        else:
            orders = orders.order_by("-created_at")  # default newest

        context = {
            "orders": orders,
        }

        return render(request, "dashboard/orders/order_list.html", context)
    
    
@method_decorator(staff_member_required, name="dispatch")
class OrderDetailView(View):

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        return render(request, "dashboard/orders/order_detail.html", {
            "order": order
        })

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        new_status = request.POST.get("status")

        valid_status = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        
        

        if new_status in valid_status:
            order.order_status = new_status
            
            if new_status == 'DELIVERED' and order.payment_method == 'COD':
                order.payment_status = 'PAID'
            if new_status == 'CANCELLED':
                order.payment_status = 'FAILED' 
              
            order.save()


        return redirect("dashboard:order_detail", pk=pk)



@method_decorator(staff_member_required, name="dispatch")
class ProductListView(ListView):
    model = Product
    template_name = "dashboard/products/product_list.html"
    context_object_name = "products"
    paginate_by = None

    def get_queryset(self):
        queryset = Product.objects.select_related("category").all()

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        category = self.request.GET.get("category")
        if category:
            queryset = queryset.filter(category__id=category)

        status = self.request.GET.get("status")

        if status == "active":
            queryset = queryset.filter(
                is_active=True,
                category__is_active=True
            )
        
        elif status == "inactive":
            queryset = queryset.filter(
                Q(is_active=False) | Q(category__is_active=False)
            )


        sort = self.request.GET.get("sort")
        if sort == "price_high":
            queryset = queryset.order_by("-price")
        elif sort == "price_low":
            queryset = queryset.order_by("price")
        elif sort == "stock_low":
            queryset = queryset.order_by("stock")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset


@method_decorator(staff_member_required, name="dispatch")
class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = "dashboard/products/product_form.html"
    success_url = reverse_lazy("dashboard:products")


@method_decorator(staff_member_required, name="dispatch")
class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "dashboard/products/product_form.html"
    success_url = reverse_lazy("dashboard:products")


@method_decorator(staff_member_required, name="dispatch")
class ProductToggleStatusView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        product.is_active = not product.is_active
        product.save()

        return redirect("dashboard:products")
    
@method_decorator(staff_member_required, name="dispatch")
class ProductSafeDeleteView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        used_in_orders = OrderItem.objects.filter(product=product).exists()

        if used_in_orders:
            messages.error(
                request,
                "Cannot delete product because it exists in orders. Deactivate instead."
            )
        else:
            product.delete()
            messages.success(request, "Product deleted successfully.")

        return redirect("dashboard:products")
    
    
@method_decorator(staff_member_required, name="dispatch")
class CategoryListView(ListView):
    model = Category
    template_name = "dashboard/categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        queryset = Category.objects.annotate(
            product_count=Count("products")
        )

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by("-created_at")


@method_decorator(staff_member_required, name="dispatch")
class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/categories/category_form.html"
    success_url = reverse_lazy("dashboard:categories")


@method_decorator(staff_member_required, name="dispatch")
class CategoryUpdateView(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/categories/category_form.html"
    success_url = reverse_lazy("dashboard:categories")


@method_decorator(staff_member_required, name="dispatch")
class CategoryToggleStatusView(View):
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        category.is_active = not category.is_active
        category.save()
        return redirect("dashboard:categories")


@method_decorator(staff_member_required, name="dispatch")
class CategorySafeDeleteView(View):
    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)

        if category.products.exists():
            messages.error(
                request,
                "Cannot delete category because it contains products."
            )
        else:
            category.delete()
            messages.success(request, "Category deleted successfully.")

        return redirect("dashboard:categories")
    
    
@method_decorator(staff_member_required, name="dispatch")
class UserListView(ListView):
    model = User
    template_name = "dashboard/users/user_list.html"
    context_object_name = "users"

    def get_queryset(self):
        queryset = User.objects.all()

        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )

        status = self.request.GET.get("status")
        if status == "active":
            queryset = queryset.filter(is_active=True)
        elif status == "inactive":
            queryset = queryset.filter(is_active=False)

        role = self.request.GET.get("role")
        if role == "staff":
            queryset = queryset.filter(is_staff=True)
        elif role == "customer":
            queryset = queryset.filter(is_staff=False)

        return queryset.order_by("-date_joined")


@method_decorator(staff_member_required, name="dispatch")
class UserDetailView(DetailView):
    model = User
    template_name = "dashboard/users/user_detail.html"
    context_object_name = "user_obj"


@method_decorator(staff_member_required, name="dispatch")
class UserToggleStatusView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Prevent admin from deactivating themselves
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("dashboard:users")

        user.is_active = not user.is_active
        user.save()

        messages.success(request, "User status updated.")
        return redirect("dashboard:users")

@method_decorator(staff_member_required, name="dispatch")
class UserToggleStaffView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        # Only superuser can change staff roles
        if not request.user.is_superuser:
            messages.error(request, "Only superuser can change staff roles.")
            return redirect("dashboard:users")

        # Never allow modifying a superuser
        if user.is_superuser:
            messages.error(request, "Cannot modify superuser.")
            return redirect("dashboard:users")

        user.is_staff = not user.is_staff
        user.save()

        messages.success(request, "User staff role updated.")
        return redirect("dashboard:users")
    
    
@method_decorator(staff_member_required, name="dispatch")
class CouponListView(ListView):
    model = Coupon
    template_name = "dashboard/coupons/coupon_list.html"
    context_object_name = "coupons"

    def get_queryset(self):
        return Coupon.objects.all().order_by("-created_at")


@method_decorator(staff_member_required, name="dispatch")
class CouponCreateView(CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = "dashboard/coupons/coupon_form.html"
    success_url = reverse_lazy("dashboard:coupons")


@method_decorator(staff_member_required, name="dispatch")
class CouponUpdateView(UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = "dashboard/coupons/coupon_form.html"
    success_url = reverse_lazy("dashboard:coupons")


@method_decorator(staff_member_required, name="dispatch")
class CouponToggleStatusView(View):
    def post(self, request, pk):
        coupon = get_object_or_404(Coupon, pk=pk)
        coupon.is_active = not coupon.is_active
        coupon.save()
        return redirect("dashboard:coupons")


@method_decorator(staff_member_required, name="dispatch")
class CouponDeleteView(DeleteView):
    model = Coupon
    template_name = "dashboard/coupons/coupon_confirm_delete.html"
    success_url = reverse_lazy("dashboard:coupons")
    
    
@method_decorator(staff_member_required, name="dispatch")
class ReportsView(View):

    def get(self, request):

        orders = Order.objects.filter(payment_status="PAID")

        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")

        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)

        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)

        # Revenue
        total_revenue = orders.aggregate(
            total=Sum("final_amount")
        )["total"] or 0

        total_orders = orders.count()

        avg_order_value = (
            total_revenue / total_orders
            if total_orders > 0 else 0
        )

        # Order status breakdown
        status_data = Order.objects.values("order_status").annotate(
            count=Count("id")
        )

        # Top selling products
        top_products = OrderItem.objects.filter(
            order__in=orders
        ).values(
            "product__name"
        ).annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum(F("price") * F("quantity"))
        ).order_by("-total_quantity")[:5]

        # Coupon usage
        coupon_usage = CouponUsage.objects.filter(
            coupon__is_active=True
        ).values(
            "coupon__code"
        ).annotate(
            total_used=Sum("usage_count")
        )

        context = {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "avg_order_value": avg_order_value,
            "status_data": status_data,
            "top_products": top_products,
            "coupon_usage": coupon_usage,
            "date_from": date_from,
            "date_to": date_to,
        }

        return render(request, "dashboard/reports.html", context)
    


from django.shortcuts import render, redirect
from products.models import HeroBanner
from .forms import HeroBannerForm


def banner_list(request):
    banners = HeroBanner.objects.all()
    return render(request, "dashboard/banner/banner_list.html", {"banners": banners})


def banner_create(request):

    if request.method == "POST":
        form = HeroBannerForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect("dashboard:banner_list")

    else:
        form = HeroBannerForm()

    return render(request, "dashboard/banner/banner_form.html", {"form": form})

def banner_edit(request, pk):

    banner = HeroBanner.objects.get(id=pk)

    if request.method == "POST":

        form = HeroBannerForm(request.POST, request.FILES, instance=banner)

        if form.is_valid():
            form.save()
            return redirect("dashboard:banner_list")

    else:
        form = HeroBannerForm(instance=banner)

    return render(request,"dashboard/banner/banner_form.html",{"form":form})

def banner_delete(request, pk):

    banner = HeroBanner.objects.get(id=pk)
    banner.delete()

    return redirect("dashboard:banner_list")



def newsletter_list(request):
    subscribers = NewsletterSubscriber.objects.all().order_by("-created_at")

    return render(
        request,
        "dashboard/newsletter/newsletter_list.html",
        {"subscribers": subscribers}
    )
    
    
import csv
from django.http import HttpResponse

def export_newsletter(request):

    subscribers = NewsletterSubscriber.objects.all()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="newsletter_subscribers.csv"'

    writer = csv.writer(response)
    writer.writerow(["Email", "Subscribed At"])

    for sub in subscribers:
        writer.writerow([sub.email, sub.created_at])

    return response

def newsletter_delete(request, pk):

    subscriber = NewsletterSubscriber.objects.get(id=pk)
    subscriber.delete()

    return redirect("dashboard:newsletter_list")
