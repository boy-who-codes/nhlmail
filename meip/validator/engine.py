import dns.resolver
import tldextract
import random
import smtplib
import socket
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from django.conf import settings
from functools import lru_cache
import whois
from .models import DisposableDomain, SMTPSender, SystemConfig
import socks # Requires pip install pysocks

# Helper to get disposable domains
def get_disposable_domains():
    try:
        # Hybrid approach: Start with critical ones, then add DB ones
        defaults = {
            "mailinator.com","10minutemail.com","10minutemail.net","10minutemail.org",
            "tempmail.com","temp-mail.org","guerrillamail.com","guerrillamail.org",
            "yopmail.com","yopmail.net","yopmail.fr","yopmail.gq"
        }
        db_domains = set(DisposableDomain.objects.values_list('domain', flat=True))
        return defaults.union(db_domains)
    except:
        return {"mailinator.com"}

# Load disposable domains
# For performance, we'll cache this or load it per request, keeping it simple for now as function call


ROLE_PREFIXES = {"admin","info","support","sales","contact","help","customercare","no-reply"}

@lru_cache(maxsize=10000)
def base_domain(email):
    try:
        ext = tldextract.extract(email.split("@")[1])
        return f"{ext.domain}.{ext.suffix}"
    except IndexError:
        return ""

# Configure DNS Resolver with timeouts
resolver = dns.resolver.Resolver()
resolver.lifetime = 5.0 # Timeout for total query
resolver.timeout = 2.0 # Timeout per server

# Save original socket execution for proxy handling
ORIG_SOCKET = socket.socket

@lru_cache(maxsize=10000)
def has_mail_server(domain):
    try:
        resolver.resolve(domain, "MX")
        return True
    except:
        try:
            resolver.resolve(domain, "A")
            return True
        except:
            return False

@lru_cache(maxsize=5000)
def get_domain_age(domain):
    # This can be slow and rate-limited.
    try:
        w = whois.whois(domain)
        c = w.creation_date
        if isinstance(c, list): c = c[0]
        if not c: return None
        if isinstance(c, datetime):
             return (datetime.now() - c).days
        return None
    except:
        return None

@lru_cache(maxsize=5000)
def get_provider(domain):
    try:
        mx = str(resolver.resolve(domain, "MX")[0].exchange).lower()
        if "google" in mx: return "Google Workspace"
        if "outlook" in mx or "microsoft" in mx: return "Microsoft 365"
        if "zoho" in mx: return "Zoho"
        return "Custom"
    except:
        return "Unknown"

def is_disposable(email):
    return base_domain(email).lower() in get_disposable_domains()

def is_role_based(email):
    return email.split('@')[0].lower() in ROLE_PREFIXES

def has_anti_spam(domain):
    try:
        # Use our configured resolver
        dmarc_records = resolver.resolve(f"_dmarc.{domain}", "TXT")
        spf_records = resolver.resolve(domain, "TXT")
        dmarc_exists = any("v=DMARC1" in str(r) for r in dmarc_records)
        spf_exists = any("v=spf1" in str(r) for r in spf_records)
        return dmarc_exists or spf_exists
    except:
        return False

@lru_cache(maxsize=1000)
def suggest_domain_typo(domain):
    common = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"]
    import difflib
    matches = difflib.get_close_matches(domain, common, n=1, cutoff=0.85)
    return matches[0] if matches else None

def check_catch_all(domain):
    """Probes a random non-existent address to see if domain accepts everything."""
    import uuid
    random_user = f"verify_{uuid.uuid4().hex[:8]}@{domain}"
    success, code, _ = check_smtp_detailed(random_user)
    # If a random user is accepted (250), it's a catch-all.
    return success

def check_smtp_detailed(email):
    """Detailed SMTP check returning (is_success, code, message)"""
    try:
        # Fetch from DB or fallback
        senders = list(SMTPSender.objects.filter(is_active=True).values_list('email', flat=True))
        if not senders:
            smtp_list = getattr(settings, 'SMTP_LIST', ["dev@meta-insyt.com"])
        else:
            smtp_list = senders
            
        smtp_sender = random.choice(smtp_list)
        
        # PROXY Handling (Simplified for brevity, assumes logic matches check_smtp)
        proxy_config = SystemConfig.objects.filter(key="PROXY_URL").first()
        if proxy_config and proxy_config.value:
            try:
                import socks
                socks.set_default_proxy() 
                socket.socket = ORIG_SOCKET 
                p_url = proxy_config.value.replace("socks5://", "").replace("http://", "")
                if "@" in p_url:
                    auth, end = p_url.split("@")
                    user, pwd = auth.split(":")
                    host, port = end.split(":")
                else:
                    user, pwd = None, None
                    host, port = p_url.split(":")
                socks.set_default_proxy(socks.SOCKS5, host, int(port), True, user, pwd)
                socket.socket = socks.socksocket
            except:
                socket.socket = ORIG_SOCKET
        else:
             if socket.socket != ORIG_SOCKET:
                 socket.socket = ORIG_SOCKET
                 
    except:
         smtp_sender = "dev@meta-insyt.com"
         if socket.socket != ORIG_SOCKET:
             socket.socket = ORIG_SOCKET
         
    try:
        domain = email.split("@")[1]
        mx_records = resolver.resolve(domain, 'MX')
        mx_records = sorted(mx_records, key=lambda x: x.preference)
        mx_host = str(mx_records[0].exchange)
        
        server = smtplib.SMTP(timeout=5)
        server.connect(mx_host)
        server.helo()
        server.mail(smtp_sender)
        code, msg = server.rcpt(email)
        server.quit()
        return code == 250, code, msg
    except (socket.timeout, socket.error, smtplib.SMTPException, dns.exception.Timeout) as e:
        return False, 999, str(e)
    except Exception as e:
        return False, 999, str(e)

# Legacy wrapper for backward compatibility if needed
def check_smtp(email):
    s, _, _ = check_smtp_detailed(email)
    return s

def calculate_rtpc_score(email_data):
    # Logic based on SRS (Software Requirements Specification) Line 171
    # Base score: 100
    # Penalties apply for negative signals.
    # Bonus applies for positive signals (Anti-Spam).
    
    current_score = 100
    
    if not email_data.get('smtp_check_success'):
        # If greylisted (soft bounce), penalty is less severe
        if email_data.get('is_greylisted'):
            current_score -= 20
        else:
            current_score -= 50 # SRS: SMTP Fail -50
    
    if email_data.get('is_disposable'):
        current_score -= 50 # SRS: Disposable -50
        
    if email_data.get('is_role_based'):
        current_score -= 30 # SRS: Role-Based -30

    if email_data.get('has_anti_spam'):
        current_score += 10 # SRS Line 171: DMARC/SPF Present | +10
        
    if email_data.get('bounce_history'):
        current_score -= 40 # SRS: Bounce History -40
        
    # Catch-All Penalty
    if email_data.get('is_catch_all'):
        current_score -= 30 
        # Cap score at 70 for catch-all (Risky)
        if current_score > 70: current_score = 70

    return max(0, min(100, current_score))

def validate_email_single(email):
    out = {
        "email": email,
        "syntax_valid": False,
        "domain_valid": False,
        "is_disposable": False,
        "is_role_based": False,
        "catch_all": "No",
        "is_catch_all": False,
        "is_greylisted": False,
        "domain_age_days": None,
        "provider": None,
        "smtp_check": "Unknown",
        "smtp_check_success": False,
        "has_anti_spam": False,
        "bounce_history": False,
        "rtpc_score": 0,
        "status": "NOT DELIVERABLE",
        "recommendation": "DO NOT SEND",
        "reason": ""
    }

    try:
        validate_email(email, check_deliverability=False)
        out["syntax_valid"] = True
    except EmailNotValidError as e:
        out["reason"] = f"Invalid syntax: {str(e)}"
        return out

    dom = base_domain(email)
    
    # Typosquatting Check
    typo_fix = suggest_domain_typo(dom)
    if typo_fix and typo_fix != dom:
         out["reason"] = f"Did you mean {typo_fix}?"
         out["status"] = "RISKY" 
         out["recommendation"] = "CHECK TYPO"
         return out

    if not dom:
        out["reason"] = "Invalid domain"
        return out
        
    has_ms = has_mail_server(dom)
    out["domain_valid"] = has_ms
    if not has_ms:
        out["reason"] = "No mail server"
        return out

    out["is_disposable"] = is_disposable(email)
    out["is_role_based"] = is_role_based(email)
    
    # Slow checks
    out["domain_age_days"] = get_domain_age(dom)
    out["provider"] = get_provider(dom)
    
    out["has_anti_spam"] = has_anti_spam(dom)
    
    # 1. Catch-All Probe
    # Only probe if not disposable and domain is valid
    is_ca = False
    if not out["is_disposable"]:
        is_ca = check_catch_all(dom)
        out["is_catch_all"] = is_ca
        if is_ca:
            out["catch_all"] = "Yes"
    
    # 2. SMTP Check
    # If catch-all, we still check, but we know 250 is meaningless. 
    # But if 550, it is definitely invalid.
    deliverable, code, msg = check_smtp_detailed(email)
    
    # Greylisting detection (4xx codes)
    if code and 400 <= code < 500:
        out["is_greylisted"] = True
        out["smtp_check"] = f"Greylisted ({code})"
    else:
        out["smtp_check_success"] = deliverable
        out["smtp_check"] = "Success" if deliverable else f"Fail ({code})"
    
    # Score
    score = calculate_rtpc_score(out)
    out["rtpc_score"] = score
    
    if score >= 81:
        out["status"] = "DELIVERABLE"
        out["recommendation"] = "SEND"
        out["reason"] = "Passed all checks"
    elif score >= 51:
        out["status"] = "RISKY"
        out["recommendation"] = "DO NOT SEND" # SRS default
        if out["is_catch_all"]:
            out["reason"] = "Catch-All Domain (Verify Manually)"
        elif out["is_greylisted"]:
             out["reason"] = "Server Busy/Greylisted (Retry Later)"
        else:
            out["reason"] = "Medium confidence"
    else:
        out["status"] = "NOT DELIVERABLE"
        out["recommendation"] = "DO NOT SEND"
        out["reason"] = "Low confidence score"
        
    return out
