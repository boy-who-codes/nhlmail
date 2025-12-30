from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg
from validator.models import ValidationBatch, EmailResult, SMTPSender, DisposableDomain, SystemConfig
from validator.engine import validate_email_single
from validator.tasks import process_batch_task
import csv
from django.conf import settings
import json

# @login_required # Temporarily disabled for dev until auth is set up or user created
def dashboard(request):
    total_emails = EmailResult.objects.count()
    total_batches = ValidationBatch.objects.count()
    recent_batches = ValidationBatch.objects.order_by('-created_at')[:5]
    
    context = {
        'total_emails': total_emails,
        'total_batches': total_batches,
        'recent_batches': recent_batches,
        'smtp_senders': list(SMTPSender.objects.filter(is_active=True).values_list('email', flat=True)) or getattr(settings, 'SMTP_LIST', [])
    }
    return render(request, 'web/dashboard.html', context)

def manual_validate(request):
    result = None
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            result = validate_email_single(email)
    
    return render(request, 'web/manual.html', {'result': result})

def batch_list(request):
    batches = ValidationBatch.objects.order_by('-created_at')
    return render(request, 'web/batch_list.html', {'batches': batches})

def upload_batch(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            # Step 1: Preview
            csv_file = request.FILES['csv_file']
            # Save temporarily or read in memory
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.reader(decoded_file)
            header = next(reader)
            preview_rows = []
            for i, row in enumerate(reader):
                if i >= 1000: break # Show up to 1000 rows as requested
                preview_rows.append(row)
            
            # We need to save the file to pass it to the next step, or re-upload.
            # Easiest: Create batch with status 'PENDING_APPROVAL'
            batch = ValidationBatch.objects.create(csv_file=csv_file, status='PENDING_APPROVAL', total_emails=0)
            
            return render(request, 'web/upload_preview.html', {
                'batch': batch, 
                'header': header, 
                'rows': preview_rows
            })
        
        elif 'confirm_batch_id' in request.POST:
            # Step 2: Confirm
            batch_id = request.POST.get('confirm_batch_id')
            batch = get_object_or_404(ValidationBatch, id=batch_id)
            batch.status = 'PENDING'
            batch.save()
            try:
                print(f"[-] Dispatching Async Task for Batch {batch.id}")
                process_batch_task.delay(batch.id)
            except Exception as e:
                print(f"[!] Async Dispatch Failed ({e}). Falling back to Synchronous execution.")
                process_batch_task(batch.id)
            return redirect('batch_list')

    return render(request, 'web/upload.html')

def management(request):
    smtp_senders = SMTPSender.objects.all().order_by('-created_at')
    disposable_domains = DisposableDomain.objects.all().order_by('-created_at')
    proxy_config = SystemConfig.objects.filter(key='PROXY_URL').first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_smtp':
            email = request.POST.get('email')
            if email: SMTPSender.objects.get_or_create(email=email)
        elif action == 'delete_smtp':
            sid = request.POST.get('id')
            SMTPSender.objects.filter(id=sid).delete()
        elif action == 'add_disposable':
            domain = request.POST.get('domain')
            if domain: DisposableDomain.objects.get_or_create(domain=domain)
        elif action == 'delete_disposable':
            did = request.POST.get('id')
            DisposableDomain.objects.filter(id=did).delete()
        elif action == 'update_proxy':
            url = request.POST.get('proxy_url')
            SystemConfig.objects.update_or_create(key='PROXY_URL', defaults={'value': url})
            
        return redirect('management')
        
    return render(request, 'web/management.html', {
        'smtp_senders': smtp_senders,
        'disposable_domains': disposable_domains,
        'proxy_url': proxy_config.value if proxy_config else ''
    })

def batch_detail(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    results = batch.results.all()
    
    # Calculate stats for Spider Graph
    total = results.count()
    stats = {
        'deliverable': 0, 'risky': 0, 'undeliverable': 0,
        'disposable': 0, 'role_based': 0, 'smtp_success': 0
    }
    
    if total > 0:
        stats['deliverable'] = results.filter(status='DELIVERABLE').count() / total * 100
        stats['risky'] = results.filter(status='RISKY').count() / total * 100
        stats['undeliverable'] = results.filter(status='NOT DELIVERABLE').count() / total * 100
        stats['disposable'] = results.filter(is_disposable=True).count() / total * 100
        stats['role_based'] = results.filter(is_role_based=True).count() / total * 100
        stats['smtp_success'] = results.filter(smtp_check='Success').count() / total * 100
        
    progress_percent = (batch.processed_emails / batch.total_emails * 100) if batch.total_emails > 0 else 0
        
    return render(request, 'web/batch_detail.html', {
        'batch': batch, 
        'results': results, 
        'graph_stats': json.dumps(stats),
        'progress_percent': progress_percent
    })

def export_batch_csv(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="batch_{batch_id}_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Email', 'Status', 'RTPC Score', 'Recommendation', 'Reason', 'Provider', 'Disposable', 'Role', 'Smtp Check', 'Firewall Info', 'SPF', 'DMARC', 'Spammy', 'Asian Region', 'Server Message'])
    
    for r in batch.results.all():
        writer.writerow([
            r.email, r.status, r.rtpc_score, r.recommendation, r.reason, 
            r.provider, r.is_disposable, r.is_role_based, r.smtp_check,
            r.firewall_info or '',
            'Yes' if r.has_spf else 'No',
            'Yes' if r.has_dmarc else 'No',
            'Yes' if r.is_spammy else 'No',
            'Yes' if r.is_asian_region else 'No',
            r.check_message or ''
        ])
        
    return response

from django.views.decorators.http import require_POST

@require_POST
def recheck_batch(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    # Clear previous results to avoid duplicates
    batch.results.all().delete()
    batch.processed_emails = 0
    batch.total_emails = 0
    batch.status = 'PENDING'
    batch.save()
    
    # Trigger task with fallback
    try:
        print(f"[-] Rechecking Batch {batch.id}")
        process_batch_task.delay(batch.id)
    except Exception as e:
        print(f"[!] Async Dispatch Failed ({e}). Falling back to Synchronous execution.")
        process_batch_task(batch.id)
    
    return redirect('batch_detail', batch_id=batch.id)

@require_POST
def pause_batch(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    if batch.status == 'PROCESSING' or batch.status == 'PENDING':
        batch.status = 'PAUSED'
        batch.save()
    return redirect('batch_detail', batch_id=batch.id)

@require_POST
def resume_batch(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    if batch.status == 'PAUSED':
        batch.status = 'PENDING'
        batch.save()
        try:
            process_batch_task.delay(batch.id)
        except:
            process_batch_task(batch.id)
    return redirect('batch_detail', batch_id=batch.id)

def batch_status_api(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    return JsonResponse({
        'status': batch.status,
        'processed': batch.processed_emails,
        'total': batch.total_emails,
        'current_email': batch.current_processing_email or 'Initializing...',
        'progress_percent': (batch.processed_emails / batch.total_emails * 100) if batch.total_emails > 0 else 0
    })

@require_POST
def delete_batch(request, batch_id):
    batch = get_object_or_404(ValidationBatch, id=batch_id)
    batch.delete()
    return redirect('batch_list')

def batch_bulk_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_items')
        
        if not selected_ids:
            messages.warning(request, "No batches selected.")
            return redirect('batch_list')
            
        batches = ValidationBatch.objects.filter(id__in=selected_ids)
        
        count = 0
        if action == 'delete':
            count = batches.count()
            batches.delete()
            messages.success(request, f"Deleted {count} batches.")
            
        elif action == 'resume':
            for batch in batches:
                if batch.status == 'PAUSED':
                    resume_batch(request, batch.id)
                    count += 1
            messages.success(request, f"Resumed {count} batches.")
            
        elif action == 'pause':
            for batch in batches:
                if batch.status in ['PROCESSING', 'PENDING']:
                    pause_batch(request, batch.id)
                    count += 1
            messages.success(request, f"Paused {count} batches.")
            
    return redirect('batch_list')

from django.http import JsonResponse
from django.conf import settings
import redis

def system_health_api(request):
    # 1. Check Redis
    redis_status = False
    try:
        r = redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=1)
        r.ping()
        redis_status = True
    except:
        redis_status = False
        
    # 2. Check Active Processes
    running_count = ValidationBatch.objects.filter(status__in=['PROCESSING', 'PENDING']).count()
    
    # 3. Overall Status
    status = "Healthy"
    if not redis_status:
        status = "Critical Issue"
    elif running_count > 0:
        status = "Processing"
        
    return JsonResponse({
        "status": status,
        "redis_connected": redis_status,
        "active_processes": running_count,
        "worker_mode": "Multi-Threaded" if "threads" in str(settings.CELERY_BROKER_URL) or True else "Unknown" # Just a placeholder
    })
