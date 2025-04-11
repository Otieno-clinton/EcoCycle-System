# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse  # Add this import

def home_view(request):
    return render(request, 'accounts/home.html')  # or HttpResponse if simpler


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists!")
        if User.objects.filter(email=email).exists():
            return HttpResponse("Email already exists!")

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        user.save()
        return redirect('accounts:login')
    return render(request, 'accounts/signup.html')

from django.contrib.auth import login as auth_login

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                auth_login(request, user)  # THIS IS CRUCIAL
                if user.role == 'admin':
                    return redirect('accounts:admin_dashboard')
                elif user.role == 'producer':
                    return redirect('accounts:producer_dashboard')
                elif user.role == 'collector':
                    return redirect('accounts:collector_dashboard')
            else:
                return HttpResponse("Invalid password!")
        except User.DoesNotExist:
            return HttpResponse("User does not exist!")
    return render(request, 'accounts/login.html')


def admin_dashboard_view(request):
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def producer_dashboard_view(request):
    if request.user.role != 'producer':
        return HttpResponse("Unauthorized", status=403)
    
    active_requests = CollectionRequest.objects.filter(
        producer=request.user,
        status__in=['pending', 'approved', 'assigned', 'collected']
    ).order_by('-request_date')
    
    completed_requests = CollectionRequest.objects.filter(
        producer=request.user,
        status__in=['recycled', 'landfill', 'rejected']
    ).order_by('-recycling_date')[:10]
    
    # Add this check
    has_payable_requests = active_requests.filter(status='approved').exists()
    
    context = {
        'active_requests': active_requests,
        'completed_requests': completed_requests,
        'has_payable_requests': has_payable_requests  # Add this
    }
    return render(request, 'accounts/producer_dashboard.html', context)
@login_required
def collector_dashboard_view(request):
    if request.user.role != 'collector':
        return HttpResponse("Unauthorized", status=403)
    
    assigned_requests = CollectionRequest.objects.filter(
        collector=request.user,
        status='assigned'
    ).order_by('-request_date')
    
    collected_requests = CollectionRequest.objects.filter(
        collector=request.user,
        status='collected'
    ).order_by('-request_date')[:5]  # Show only 5 recent collected requests
    
    context = {
        'assigned_requests': assigned_requests,
        'collected_requests': collected_requests
    }
    return render(request, 'accounts/collector_dashboard.html', context)






from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import User, CollectionRequest

@login_required
def new_request(request):
    if request.method == 'POST':
        waste_type = request.POST.get('waste_type')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description')
        collection_date = request.POST.get('collection_date')
        
        request = CollectionRequest.objects.create(
            producer=request.user,
            waste_type=waste_type,
            quantity=quantity,
            description=description,
            collection_date=collection_date
        )
        return redirect('accounts:producer_dashboard')
    
    return render(request, 'accounts/new_request.html')

@login_required
def request_list(request):
    if request.user.role == 'admin':
        requests = CollectionRequest.objects.all().order_by('-request_date')
        template = 'accounts/admin_request_list.html'
    elif request.user.role == 'collector':
        requests = CollectionRequest.objects.filter(
            collector=request.user
        ).order_by('-request_date')
        template = 'accounts/collector_request_list.html'
    else:  # producer
        requests = CollectionRequest.objects.filter(
            producer=request.user
        ).order_by('-request_date')
        template = 'accounts/producer_dashboard.html'
    
    context = {
        'requests': requests,
        'pending_requests': CollectionRequest.objects.filter(status='pending') if request.user.role == 'admin' else None,
        'assigned_requests': CollectionRequest.objects.filter(status='assigned') if request.user.role == 'admin' else None
    }
    return render(request, template, context)

@login_required
def approve_request(request, request_id):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=401)
    
    collection_request = get_object_or_404(CollectionRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        collector_id = request.POST.get('collector')
        admin_notes = request.POST.get('admin_notes')
        
        if action == 'approve':
            collector = User.objects.get(id=collector_id)
            collection_request.collector = collector
            collection_request.status = 'assigned'
        elif action == 'reject':
            collection_request.status = 'rejected'
        
        collection_request.admin_notes = admin_notes
        collection_request.save()
        return redirect('accounts:request_list')
    
    collectors = User.objects.filter(role='collector')
    context = {
        'request': collection_request,
        'collectors': collectors
    }
    return render(request, 'accounts/approve_request.html', context)

@login_required
def update_request_status(request, request_id):
    collection_request = get_object_or_404(CollectionRequest, id=request_id)
    
    # Ensure only the assigned collector or admin can update status
    if request.user.role == 'collector' and collection_request.collector != request.user:
        return HttpResponse("Unauthorized", status=403)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        # Validate status transitions
        valid_transitions = {
            'assigned': ['collected'],
            'collected': ['recycled', 'landfill']
        }
        
        if (request.user.role == 'collector' and 
            new_status not in valid_transitions.get(collection_request.status, [])):
            return HttpResponse("Invalid status transition", status=400)
        
        collection_request.status = new_status
        
        # Set recycling date when marked as recycled/landfill
        if new_status in ['recycled', 'landfill']:
            collection_request.recycling_date = timezone.now().date()
            collection_request.final_disposition = new_status
        
        collection_request.save()
        
        if request.user.role == 'collector':
            return redirect('accounts:collector_assignments')
        else:
            return redirect('accounts:request_list')
    
    return render(request, 'accounts/update_status.html', {'request': collection_request})


'''@login_required
def request_list(request):
    if request.user.role == 'admin':
        requests = CollectionRequest.objects.all().order_by('-request_date')
        template = 'accounts/admin_request_list.html'
    elif request.user.role == 'collector':
        requests = CollectionRequest.objects.filter(
            collector=request.user
        ).order_by('-request_date')
        template = 'accounts/collector_request_list.html'
    else:
        requests = CollectionRequest.objects.filter(
            producer=request.user
        ).order_by('-request_date')
        template = 'accounts/producer_request_list.html'
    
    return render(request, template, {'requests': requests})'''


from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def logout_view(request):
    """Log out the current user and redirect to login page"""
    logout(request)
    return redirect('accounts:login')  # Redirect to login page after logout


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CollectionRequest
from django.contrib import messages

@login_required
def create_request(request):
    if request.user.role != 'producer':
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        waste_type = request.POST.get('waste_type')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description')
        collection_date = request.POST.get('collection_date')
        
        try:
            CollectionRequest.objects.create(
                producer=request.user,
                waste_type=waste_type,
                quantity=quantity,
                description=description,
                collection_date=collection_date
            )
            messages.success(request, 'Collection request created successfully!')
            return redirect('accounts:request_list')
        except Exception as e:
            messages.error(request, f'Error creating request: {str(e)}')
    
    waste_types = CollectionRequest.WASTE_TYPES
    return render(request, 'accounts/create_request.html', {'waste_types': waste_types})






'''@login_required
def collector_assignments(request):
    if request.user.role != 'collector':
        return HttpResponse("Unauthorized", status=403)
    
    assigned_requests = CollectionRequest.objects.filter(
        collector=request.user,
        status='assigned'
    ).order_by('-request_date')
    
    context = {
        'assigned_requests': assigned_requests
    }
    return render(request, 'accounts/collector_assignments.html', context)'''









from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout
from django.utils import timezone
from .models import User, CollectionRequest
import csv

@login_required
def recycling_log(request):
    if request.user.role != 'collector':
        return HttpResponse("Unauthorized", status=403)
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        final_disposition = request.POST.get('final_disposition')
        actual_quantity = request.POST.get('actual_quantity')
        recycling_notes = request.POST.get('recycling_notes')
        
        try:
            collection_request = CollectionRequest.objects.get(
                id=request_id, 
                collector=request.user,
                status='collected'
            )
            
            collection_request.final_disposition = final_disposition
            collection_request.actual_quantity = actual_quantity
            collection_request.recycling_notes = recycling_notes
            collection_request.recycling_date = timezone.now().date()
            collection_request.status = final_disposition  # 'recycled' or 'landfill'
            collection_request.save()
            
            messages.success(request, 'Recycling information logged successfully!')
            return redirect('accounts:recycling_log')
        except CollectionRequest.DoesNotExist:
            messages.error(request, 'Invalid request or unauthorized action')
            return redirect('accounts:recycling_log')
    
    # Get requests ready for logging (collected but not yet disposed)
    pending_logs = CollectionRequest.objects.filter(
        collector=request.user,
        status='collected'
    ).order_by('-collection_date')
    
    # Get completed logs
    completed_logs = CollectionRequest.objects.filter(
        collector=request.user,
        status__in=['recycled', 'landfill']
    ).order_by('-recycling_date')
    
    return render(request, 'accounts/recycling_log.html', {
        'pending_logs': pending_logs,
        'completed_logs': completed_logs
    })

@login_required
def admin_reports(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    # Filter parameters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    reports = CollectionRequest.objects.all().order_by('-recycling_date')
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if date_from:
        reports = reports.filter(recycling_date__gte=date_from)
    if date_to:
        reports = reports.filter(recycling_date__lte=date_to)
    
    # Export to CSV
    if 'export' in request.GET:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ewaste_reports.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Producer', 'Collector', 'Waste Type', 
            'Requested Qty', 'Actual Qty', 'Status',
            'Request Date', 'Collection Date', 'Recycling Date',
            'Final Disposition', 'Notes'
        ])
        
        for report in reports:
            writer.writerow([
                report.id,
                report.producer.username,
                report.collector.username if report.collector else '',
                report.get_waste_type_display(),
                report.quantity,
                report.actual_quantity,
                report.get_status_display(),
                report.request_date.strftime('%Y-%m-%d'),
                report.collection_date.strftime('%Y-%m-%d') if report.collection_date else '',
                report.recycling_date.strftime('%Y-%m-%d') if report.recycling_date else '',
                report.get_final_disposition_display() if report.final_disposition else '',
                report.recycling_notes
            ])
        
        return response
    
    return render(request, 'accounts/admin_reports.html', {
        'reports': reports,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to
    })






from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .models import CollectionRequest, Payment
from .payment_utils import calculate_charges, format_phone_number, initiate_stk_push

@login_required
def payment_page(request, request_id):
    # Remove status restriction - allow payment for any request
    collection_request = get_object_or_404(
        CollectionRequest, 
        id=request_id, 
        producer=request.user  # Only keep producer ownership check
    )
    
    # Calculate amount based on waste type and quantity
    amount = calculate_charges(
        collection_request.waste_type,
        collection_request.quantity
    )
    
    context = {
        'request': collection_request,
        'amount': amount,
        'payment_history': Payment.objects.filter(request=collection_request).order_by('-created_at')
    }
    return render(request, 'accounts/payment_page.html', context)

from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def initiate_payment(request, request_id):
    if request.method == 'POST':
        # Get the collection request
        collection_request = get_object_or_404(
            CollectionRequest, 
            id=request_id, 
            producer=request.user
        )
        
        # Format phone number and calculate amount
        phone_number = format_phone_number(request.POST.get('phone_number'))
        amount = calculate_charges(
            collection_request.waste_type,
            collection_request.quantity
        )
        
        # Create payment record
        payment = Payment.objects.create(
            request=collection_request,
            amount=amount,
            phone_number=phone_number,
            status='pending'
        )
        
        # Initiate STK push
        try:
            # Use callback URL from settings if defined, otherwise build dynamically
            callback_url = getattr(settings, 'MPESA_CALLBACK_URL', None)
            if not callback_url:
                callback_url = request.build_absolute_uri(reverse('accounts:mpesa_callback'))
            
            response = initiate_stk_push(
                phone=phone_number,
                amount=amount,
                order_id=payment.id,
                callback_url=callback_url
            )
            
            if response and response.get('ResponseCode') == '0':
                payment.mpesa_receipt_number = response.get('CheckoutRequestID')
                payment.save()
                messages.success(request, 'Payment initiated successfully! Check your phone to complete the payment.')
                return redirect('accounts:verify_payment', payment_id=payment.id)
            else:
                payment.status = 'failed'
                payment.save()
                error_msg = response.get('errorMessage', 'Failed to initiate payment. Please try again.')
                messages.error(request, error_msg)
        except Exception as e:
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment error: {str(e)}')
        
        return redirect('accounts:payment_page', request_id=request_id)
    
    return redirect('accounts:payment_page', request_id=request_id)

@login_required
def verify_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, request__producer=request.user)
    
    if request.method == 'POST':
        mpesa_code = request.POST.get('mpesa_code')
        if mpesa_code:
            payment.mpesa_receipt_number = mpesa_code
            payment.verified = True
            payment.save()
            messages.success(request, 'Payment verification submitted! Admin will review your payment.')
            return redirect('accounts:producer_dashboard')
    
    context = {'payment': payment}
    return render(request, 'accounts/verify_payment.html', context)









from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Payment

@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            # Parse the callback data
            callback_data = json.loads(request.body)
            
            # Extract relevant information
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            callback_metadata = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {})
            
            # Find the payment record
            payment = Payment.objects.filter(mpesa_receipt_number=checkout_request_id).first()
            
            if not payment:
                return JsonResponse({'status': 'error', 'message': 'Payment not found'}, status=404)
            
            # Process based on result code
            if result_code == '0':
                # Successful payment
                payment.status = 'completed'
                
                # Extract transaction details from metadata
                if callback_metadata:
                    for item in callback_metadata.get('Item', []):
                        if item.get('Name') == 'MpesaReceiptNumber':
                            payment.mpesa_receipt_number = item.get('Value')
                        elif item.get('Name') == 'Amount':
                            payment.amount = item.get('Value')
                        elif item.get('Name') == 'TransactionDate':
                            payment.transaction_date = item.get('Value')
                
                payment.save()
                
                # You can trigger additional actions here like sending notifications
                return JsonResponse({'status': 'success', 'message': 'Payment processed successfully'})
            else:
                # Failed payment
                payment.status = 'failed'
                payment.save()
                return JsonResponse({'status': 'error', 'message': 'Payment failed'}, status=400)
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)









'''@login_required
def admin_payments(request):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    pending_payments = Payment.objects.filter(
        status='completed',
        admin_approved=False
    ).order_by('-created_at')
    
    payment_history = Payment.objects.exclude(
        status='pending'
    ).order_by('-created_at')[:50]
    
    context = {
        'pending_payments': pending_payments,
        'payment_history': payment_history
    }
    return render(request, 'accounts/admin_payments.html', context)'''

'''@login_required
def approve_payment(request, payment_id):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    payment = get_object_or_404(Payment, id=payment_id)
    payment.admin_approved = True
    payment.save()
    
    # Update the associated request status if needed
    collection_request = payment.request
    collection_request.status = 'approved'  # Or whatever status makes sense
    collection_request.save()
    
    # Here you would typically send a notification to the producer
    messages.success(request, f'Payment #{payment.id} approved successfully!')
    return redirect('admin_payments')

@login_required
def reject_payment(request, payment_id):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    payment = get_object_or_404(Payment, id=payment_id)
    payment.admin_approved = False
    payment.status = 'failed'
    payment.save()
    
    # Here you would typically send a notification to the producer
    messages.warning(request, f'Payment #{payment.id} has been rejected.')
    return redirect('admin_payments')'''







@login_required
def producer_payment_list(request):
    if request.user.role != 'producer':
        return HttpResponse("Unauthorized", status=403)
    
    # Show all requests without status filtering
    all_requests = CollectionRequest.objects.filter(
        producer=request.user
    ).order_by('-request_date')
    
    payment_history = Payment.objects.filter(
        request__producer=request.user
    ).order_by('-created_at')
    
    context = {
        'payable_requests': all_requests,  # Renamed from payable_requests to all_requests
        'payment_history': payment_history
    }
    return render(request, 'accounts/producer_payment_list.html', context)





@login_required
def view_payment(request, payment_id):
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    context = {
        'payment': payment,
        'verification_details': {
            'amount': payment.amount,
            'phone': payment.phone_number,
            'receipt': payment.mpesa_receipt_number,
            'date': payment.created_at,
            'verified': payment.verified,
            'request_id': payment.request.id,
            'producer': payment.request.producer.username
        }
    }
    return render(request, 'accounts/view_payment.html', context)



















    

















    # views.py - Add these functions to your existing views.py file

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import CollectionRequest

@login_required
def collector_assignments(request):
    if request.user.role != 'collector':
        return HttpResponse("Unauthorized", status=403)
    
    assigned_requests = CollectionRequest.objects.filter(
        collector=request.user,
        status='assigned'
    ).order_by('-request_date')
    
    context = {
        'assigned_requests': assigned_requests
    }
    return render(request, 'accounts/collector_assignments.html', context)

@login_required
def assignment_details(request, request_id):
    """View for collectors to see detailed information about an assigned collection request"""
    if request.user.role != 'collector':
        return HttpResponse("Unauthorized", status=403)
    
    # Get the collection request, ensuring it belongs to this collector
    collection_request = get_object_or_404(
        CollectionRequest, 
        id=request_id,
        collector=request.user
    )
    
    # Only allow viewing details for approved/assigned requests
    if collection_request.status not in ['approved', 'assigned', 'collected']:
        return HttpResponse("This request is not available for viewing", status=403)
    
    context = {
        'request': collection_request
    }
    return render(request, 'accounts/collector_assignment_details.html', context)

@login_required
def update_status(request, request_id):
    """Update the status of a collection request"""
    if request.user.role != 'collector':
        return HttpResponse("Unauthorized", status=403)
    
    collection_request = get_object_or_404(
        CollectionRequest, 
        id=request_id,
        collector=request.user
    )
    
    # Get the new status from URL parameters
    new_status = request.GET.get('status')
    
    # Validate the status transition
    valid_transitions = {
        'assigned': ['collected'],
        'collected': ['recycled', 'landfill']
    }
    
    current_status = collection_request.status
    
    if new_status not in valid_transitions.get(current_status, []):
        return HttpResponse("Invalid status transition", status=400)
    
    # Update the status
    collection_request.status = new_status
    
    # If marking as collected, set the collection date to today
    if new_status == 'collected':
        from django.utils import timezone
        collection_request.collection_date = timezone.now().date()
    
    collection_request.save()
    
    # Redirect based on the new status
    if new_status == 'collected':
        return redirect('accounts:recycling_log')
    else:
        return redirect('accounts:collector_assignments')











# Updated views for payment verification functionality

@login_required
def verify_payment(request, payment_id):
    """View for producers to verify payments by submitting M-Pesa code"""
    payment = get_object_or_404(Payment, id=payment_id, request__producer=request.user)
    
    if request.method == 'POST':
        mpesa_code = request.POST.get('mpesa_code')
        if mpesa_code:
            payment.mpesa_receipt_number = mpesa_code
            payment.verified = True
            payment.status = 'completed'  # Update status to completed when code is provided
            payment.save()
            messages.success(request, 'Payment verification submitted! Admin will review your payment.')
            return redirect('accounts:producer_dashboard')
    
    context = {'payment': payment}
    return render(request, 'accounts/verify_payment.html', context)

@login_required
def admin_payments(request):
    """Admin panel for managing payment approvals"""
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    # Get payments pending admin approval (verified by producer but not yet approved)
    pending_payments = Payment.objects.filter(
        verified=True,
        status='completed',
        admin_approved=False
    ).order_by('-created_at')
    
    # Get payment history (approved or rejected)
    payment_history = Payment.objects.exclude(
        status='pending'
    ).order_by('-created_at')[:50]
    
    context = {
        'pending_payments': pending_payments,
        'payment_history': payment_history
    }
    return render(request, 'accounts/admin_payments.html', context)

@login_required
def approve_payment(request, payment_id):
    """Admin function to approve payment"""
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    payment = get_object_or_404(Payment, id=payment_id)
    payment.admin_approved = True
    payment.save()
    
    # Update the associated request status to approved
    collection_request = payment.request
    collection_request.status = 'approved'
    collection_request.save()
    
    messages.success(request, f'Payment #{payment.id} approved successfully!')
    return redirect('accounts:admin_payments')

@login_required
def reject_payment(request, payment_id):
    """Admin function to reject payment"""
    if request.user.role != 'admin':
        return HttpResponse("Unauthorized", status=403)
    
    payment = get_object_or_404(Payment, id=payment_id)
    payment.admin_approved = False
    payment.status = 'failed'
    payment.save()
    
    messages.warning(request, f'Payment #{payment.id} has been rejected.')
    return redirect('accounts:admin_payments')