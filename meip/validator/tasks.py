from celery import shared_task
from .models import ValidationBatch, EmailResult
from .engine import validate_email_single
import pandas as pd
import os
from django.conf import settings

@shared_task
def process_batch_task(batch_id):
    print(f"[-] RECEIVED TASK for Batch ID: {batch_id}")
    try:
        batch = ValidationBatch.objects.get(id=batch_id)
        batch.status = 'PROCESSING'
        batch.save()
        
        file_path = batch.csv_file.path
        if not os.path.exists(file_path):
             batch.status = 'FAILED'
             batch.save()
             return "File not found"
             
        df = pd.read_csv(file_path)
        # Normalize column names
        df.columns = [c.strip() for c in df.columns]
        
        # Check for 'Email' column (case insensitive)
        email_col = next((c for c in df.columns if c.lower() == 'email'), None)
        if not email_col:
            batch.status = 'FAILED'
            batch.save()
            return "No Email column found"
            
        emails = df[email_col].dropna().unique().tolist()
        batch.total_emails = len(emails)
        batch.save()
        
        # RESUME LOGIC: Filter out emails already processed for this batch
        processed_emails_list = set(EmailResult.objects.filter(batch=batch).values_list('email', flat=True))
        emails_to_process = [e for e in emails if e not in processed_emails_list]
        
        print(f"[-] Resuming Batch {batch.id}. Total: {len(emails)}. Already Done: {len(processed_emails_list)}. To Do: {len(emails_to_process)}")
        
        processed_count = len(processed_emails_list)
        results_objs = []
        
        for email in emails_to_process:
            # CHECK PAUSE
            batch.refresh_from_db()
            if batch.status == 'PAUSED':
                print(f"[-] Batch {batch.id} PAUSED by user.")
                # Save any pending buffer
                if results_objs:
                    EmailResult.objects.bulk_create(results_objs)
                return "Paused"

            print(f"    > Verifying: {email}")
            
            # Update current email status
            batch.current_processing_email = email
            batch.save(update_fields=['current_processing_email'])

            res = validate_email_single(email)
            
            # Save result
            er = EmailResult(
                batch=batch,
                email=email,
                normalized_email=res['email'],
                syntax_valid=res['syntax_valid'],
                domain_valid=res['domain_valid'],
                is_disposable=res['is_disposable'],
                is_role_based=res['is_role_based'],
                catch_all=res['catch_all'],
                domain_age_days=res['domain_age_days'],
                provider=res['provider'],
                smtp_check=res['smtp_check'],
                check_message=res.get('check_message', ''), 
                has_anti_spam=res['has_anti_spam'],
                bounce_history=res['bounce_history'],
                rtpc_score=res['rtpc_score'],
                status=res['status'],
                recommendation=res['recommendation'],
                reason=res['reason']
            )
            # Save immediately (or small buffer) to support robust pausing
            er.save() 
            processed_count += 1
            
            # Update batch progress periodically
            if processed_count % 5 == 0:
                batch.processed_emails = processed_count
                batch.save(update_fields=['processed_emails'])
        
        batch.processed_emails = processed_count
        batch.status = 'COMPLETED'
        batch.current_processing_email = "" # Clear on completion
        batch.save()
        
    except Exception as e:
        print(f"[!] BATCH TASK ERROR: {e}")
        if 'batch' in locals():
            batch.status = 'FAILED'
            batch.save()
        return str(e)
