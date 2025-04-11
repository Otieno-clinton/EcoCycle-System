from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('producer/dashboard/', views.producer_dashboard_view, name='producer_dashboard'),
    path('collector/dashboard/', views.collector_dashboard_view, name='collector_dashboard'),

        # Request Management URLs
    path('requests/new/', views.new_request, name='new_request'),
    path('collector/assignments/', views.collector_assignments, name='collector_assignments'),

    path('requests/', views.request_list, name='request_list'),
    path('requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:request_id>/update-status/', views.update_request_status, name='update_status'),
    path('requests/new/', views.create_request, name='create_request'),


    path('collector/recycling-log/', views.recycling_log, name='recycling_log'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('payment/<int:request_id>/', views.payment_page, name='payment_page'),
    path('payment/<int:request_id>/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    

    #path('producer/payments/', views.producer_payments, name='producer_payments'),
    path('payment/<int:request_id>/', views.payment_page, name='payment_page'),

    path('admin/payments/', views.admin_payments, name='admin_payments'),
        path('payment/verify/<int:payment_id>/', views.verify_payment, name='verify_payment'),

    path('admin/payments/<int:payment_id>/approve/', views.approve_payment, name='approve_payment'),
    path('admin/payments/<int:payment_id>/reject/', views.reject_payment, name='reject_payment'),
    path('producer/payments/', views.producer_payment_list, name='producer_payment_list'),

    path('logout/', views.logout_view, name='logout'),
    # Add this to your urls.py
path('admin/payments/<int:payment_id>/view/', views.view_payment, name='view_payment'),

# Add this to your urls.py in the urlpatterns list

#path('admin/payments/<int:payment_id>/details/', views.payment_details, name='payment_details'),


    path('collector/assignments/', views.collector_assignments, name='collector_assignments'),
    path('collector/assignments/<int:request_id>/', views.assignment_details, name='assignment_details'),
    path('collector/requests/<int:request_id>/update-status/', views.update_status, name='update_status'),

    


    


]
