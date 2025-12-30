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
import socks


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

def check_dns_security(domain):
    """Returns (spf_status, dmarc_status) strings"""
    spf_status = "None"
    dmarc_status = "None"

    try:
        # DMARC Check
        # Use our configured resolver
        dmarc_records = resolver.resolve(f"_dmarc.{domain}", "TXT")
        for r in dmarc_records:
            txt = str(r).strip('"')
            if txt.startswith("v=DMARC1"):
                # Parse policy
                if "p=reject" in txt: dmarc_status = "Reject"
                elif "p=quarantine" in txt: dmarc_status = "Quarantine"
                elif "p=none" in txt: dmarc_status = "Monitor"
                else: dmarc_status = "Present"
                break
    except:
        pass
        
    try:
        # SPF Check
        spf_records = resolver.resolve(domain, "TXT")
        for r in spf_records:
            txt = str(r).strip('"')
            if txt.startswith("v=spf1"):
                if "-all" in txt: spf_status = "HardFail"
                elif "~all" in txt: spf_status = "SoftFail"
                elif "?all" in txt: spf_status = "Neutral"
                elif "+all" in txt: spf_status = "AllowAll"
                else: spf_status = "Present"
                break
    except:
        pass
        
    return spf_status, dmarc_status

@lru_cache(maxsize=1000)
def suggest_domain_typo(domain):
    common = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "aol.com"]
    import difflib
    matches = difflib.get_close_matches(domain, common, n=1, cutoff=0.85)
    return matches[0] if matches else None

def detect_spam_filter(mx_host, banner=None):
    mx = mx_host.lower() if mx_host else ""
    banner = banner.lower() if banner else ""
    
    content = f"{mx} {banner}"
    
    if "pphosted" in content or "proofpoint" in content: return "Proofpoint"
    if "mimecast" in content: return "Mimecast"
    if "barracuda" in content: return "Barracuda"
    if "outlook" in content or "naming" in content or "microsoft" in content: return "Microsoft EOP"
    if "google" in content: return "Google Postini"
    if "messagelabs" in content or "symantec" in content: return "Broadcom/Symantec"
    if "ironport" in content: return "Cisco IronPort"
    if "trendmicro" in content: return "TrendMicro"
    if "sophos" in content: return "Sophos"
    if "sendgrid" in content: return "SendGrid"
    return None

def detect_firewall_info(mx_host, banner=None):
    """Returns detected firewall name for new field"""
    return detect_spam_filter(mx_host, banner)


def check_catch_all(domain):
    """Probes a random non-existent address to see if domain accepts everything."""
    import uuid
    random_user = f"verify_{uuid.uuid4().hex[:8]}@{domain}"
    success, code, _, _ = check_smtp_detailed(random_user)
    # If a random user is accepted (250), it's a catch-all.
    return success

def check_smtp_detailed(email):
    """Detailed SMTP check returning (is_success, code, message, banner)"""
    try:
        try:
            # 1. Get senders from DB
            db_senders = list(SMTPSender.objects.filter(is_active=True).values_list('email', flat=True))
            if db_senders:
                smtp_list = db_senders
            else:
                # Strictly use settings, no hardcode fallback
                smtp_list = getattr(settings, 'SMTP_LIST', [])
                if not smtp_list: raise ValueError("No SMTP Senders available")
        except Exception:
             # Fallback if DB fails
             smtp_list = getattr(settings, 'SMTP_LIST', [])
             if not smtp_list: raise ValueError("No SMTP Senders available")

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
         # Final safety net if logic above fails
         smtp_list = getattr(settings, 'SMTP_LIST', [])
         if smtp_list:
             smtp_sender = random.choice(smtp_list)
         else:
             return False, 999, "Configuration Error: No Senders", ""

         if socket.socket != ORIG_SOCKET:
             socket.socket = ORIG_SOCKET
         
    try:
        domain = email.split("@")[1]
        mx_records = resolver.resolve(domain, 'MX')
        mx_records = sorted(mx_records, key=lambda x: x.preference)
        mx_host = str(mx_records[0].exchange)
        
        # Determine HELO hostname from sender
        try:
             helo_host = smtp_sender.split("@")[1]
        except:
             helo_host = socket.getfqdn()

        server = smtplib.SMTP(timeout=5)
        # Capture banner
        connect_code, connect_msg = server.connect(mx_host)
        banner = str(connect_msg)
        
        server.helo(helo_host)
        server.mail(smtp_sender)
        code, msg = server.rcpt(email)
        server.quit()
        return code == 250, code, msg, banner
    except (socket.timeout, socket.error, smtplib.SMTPException, dns.exception.Timeout) as e:
        return False, 999, str(e), ""
    except Exception as e:
        return False, 999, str(e), ""

# Legacy wrapper for backward compatibility if needed
def check_smtp(email):
    s, _, _, _ = check_smtp_detailed(email)
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
            current_score -= 30 # Reduced from -50

    if email_data.get('is_disposable'):
        current_score -= 50

    if email_data.get('is_role_based'):
        current_score -= 30

    # Bonuses for SPF/DMARC (helps legit domains)
    if email_data.get("has_spf"):
        current_score += 5
    if email_data.get("has_dmarc"):
        current_score += 5

    # Legacy field bonus (if still used)
    if email_data.get('has_anti_spam') and not (email_data.get("has_spf") or email_data.get("has_dmarc")):
         current_score += 5

    if email_data.get('bounce_history'):
        current_score -= 40

    # Catch-All Penalty
    if email_data.get('is_catch_all'):
        current_score -= 15 # Reduced from -30
        # Cap score is removed or relaxed for now based on user feedback
        # if current_score > 70: current_score = 70

    if email_data.get('firewall_info'):
        current_score -= 15 # New penalty for firewall

    if email_data.get('is_spammy'):
        current_score -= 40

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
        "has_spf": False,
        "has_dmarc": False,
        "spam_filter": None,
        "bounce_history": False,
        "rtpc_score": 0,
        "status": "NOT DELIVERABLE",
        "recommendation": "DO NOT SEND",
        "reason": "",
        "check_message": "",
        "firewall_info": None,
        "is_spammy": False,
        "is_asian_region": False,
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
    
    spf_status, dmarc_status = check_dns_security(dom)
    # Map detailed status to boolean for backward compatibility/scoring
    out["has_spf"] = spf_status != "None"
    out["has_dmarc"] = dmarc_status != "None"
    # Store detailed info in check_message or reason if helpful? 
    # For now, just logging it into the result object if we had fields, 
    # but sticking to requirements, we just improved the *logic* of finding them.
    # We can append to check_message if verified
    # out["check_message"] = f"SPF: {spf_status}, DMARC: {dmarc_status}" # Optional
    
    out["has_anti_spam"] = out["has_spf"] or out["has_dmarc"]
    
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
    deliverable, code, msg, banner = check_smtp_detailed(email)
    out["check_message"] = msg


    # Detect Spam Filter from MX (if valid domain)
    if has_ms:
        try:
            mx_records = resolver.resolve(dom, 'MX')
            mx_start = str(mx_records[0].exchange).lower()
            out["spam_filter"] = detect_spam_filter(mx_start, banner)
            # Use same logic for firewall_info
            out["firewall_info"] = detect_firewall_info(mx_start, banner)
        except:
             out["spam_filter"] = None
             out["firewall_info"] = None
    else:
        out["spam_filter"] = None
        out["firewall_info"] = None

    # Spammy & Asian region detection
    out["is_spammy"] = out["is_disposable"] # Simplified for now, or add specific logic
    try:
        w = whois.whois(dom)
        country = w.country
        asian_countries = {"CN", "JP", "KR", "IN", "SG", "TH", "MY", "ID", "PH", "VN", "HK", "TW"}
        out["is_asian_region"] = country in asian_countries if country else False
    except Exception:
        out["is_asian_region"] = False

    
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
