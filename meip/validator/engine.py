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
from .models import DisposableDomain, SMTPSender, SystemConfig, SpamTrap
import socks


# Professional Grade Disposable Domains List (Top 100+ Common Providers)
def get_disposable_domains():
    try:
        defaults = {
            "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com", "yopmail.com",
            "trashmail.com", "maildrop.cc", "throwawaymail.com", "getairmail.com", "dispostable.com",
            "sharklasers.com", "guerrillamail.net", "guerrillamail.org", "guerrillamail.biz",
            "grr.la", "guerrillamailblock.com", "spam4.me", "yopmail.net", "yopmail.fr", "yopmail.uk",
            "cool.fr.nf", "jetable.fr.nf", "nospam.ze.tc", "nomail.xl.cx", "mega.zik.dj",
            "speed.1s.fr", "courriel.fr.nf", "moncourrier.fr.nf", "monemail.fr.nf", "monmail.fr.nf",
            "10minutemail.net", "10minutemail.org", "temp-mail.org", "temp-mail.ru", "temp-mail.info",
            "1secmail.com", "1secmail.org", "1secmail.net", "fastmail.fm", "hushmail.com",
            "mail-temp.com", "email-temp.com", "tempemail.net", "tempemail.co", "tempemail.biz",
            "mytemp.email", "temp-mail.io", "tempmail.net", "tempmail.co", "tempmail.biz",
            "mailnesia.com", "mailcatch.com", "incognitomail.org", "mohmal.com", "emailondeck.com",
            "tempail.com", "luxusmail.org", "generator.email", "mintemail.com", "spambox.us",
            "spamgourmet.com", "trashmail.net", "trashmail.me", "anonymbox.com", "anonbox.net",
            "antichef.com", "antichef.net", "bouncr.com", "eadspost.com", "emailconf.com",
            "emailengine.net", "emailengine.org", "emailproxsy.com", "faked.org", "fakemail.net",
            "fakermail.com", "filzmail.com", "fleckens.hu", "get2mail.fr", "grr.la", "guerrillamail.de",
            "my10minutemail.com", "neomailbox.com", "neomailbox.net", "netcourrier.com",
            "nospam.today", "nospamfor.us", "nospam4.us", "nospamtable.com", "notmail.com"
        }
        db_domains = set(DisposableDomain.objects.values_list('domain', flat=True))
        return defaults.union(db_domains)
    except:
        return {"mailinator.com", "yopmail.com", "tempmail.com"}

# Comprehensive Role-Based Prefixes (~60 Standard Roles)
ROLE_PREFIXES = {
    # Executives & Management
    "admin", "administrator", "manager", "ceo", "cto", "cfo", "coo", "president", "director",
    "founder", "owner", "management", "executive", "office", "secretary", "reception",
    
    # Operations & Support
    "info", "support", "help", "sales", "contact", "enquiry", "inquiry", "questions",
    "service", "care", "customercare", "helpdesk", "billing", "accounts", "accounting",
    "finance", "invoice", "invoices", "orders", "returns", "shipping", "logistics", "operations",
    
    # Technical & IT
    "webmaster", "hostmaster", "postmaster", "abuse", "noc", "security", "sysadmin", "system",
    "it", "tech", "technical", "api", "dev", "developer", "engineering", "bugs", "error",
    "ftp", "www", "ratelimit", "noreply", "no-reply", "donotreply", "notify", "alert", "alerts",
    
    # HR & Staff
    "hr", "jobs", "careers", "recruitment", "hiring", "team", "staff", "all", "everyone",
    "marketing", "press", "media", "pr", "legal", "compliance", "privacy", "gdpr"
}

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
        mx_records = resolver.resolve(domain, "MX")
        if not mx_records: return "None"
        
        # Sort by priority
        mx_records = sorted(mx_records, key=lambda r: r.preference)
        mx = str(mx_records[0].exchange).lower().strip('.')
        
        # Major Providers
        if "google" in mx or "gmail" in mx: return "Google Workspace"
        if "outlook" in mx or "microsoft" in mx or "hotmail" in mx: return "Microsoft 365"
        if "zoho" in mx: return "Zoho Mail"
        if "yahoodns" in mx or "yahoo" in mx: return "Yahoo Business"
        if "amazonses" in mx: return "Amazon SES"
        
        # Hosting / Registrars
        if "secureserver" in mx or "godaddy" in mx: return "GoDaddy"
        if "privateemail" in mx or "jellyfish.systems" in mx or "registrar-servers" in mx: return "Namecheap"
        if "spaceship" in mx or "spacemail" in mx: return "Spaceship"
        if "name.com" in mx: return "Name.com"
        if "unifiedlayer" in mx or "bluehost" in mx: return "Bluehost"
        if "hostgator" in mx or "websitewelcome" in mx: return "HostGator"
        if "dreamhost" in mx: return "DreamHost"
        if "kundenserver" in mx or "ionos" in mx or "1and1" in mx: return "IONOS"
        if "ovh" in mx: return "OVHcloud"
        
        # Security / Filters
        if "pphosted" in mx: return "Proofpoint"
        if "mimecast" in mx: return "Mimecast"
        if "barracuda" in mx: return "Barracuda"
        if "trendmicro" in mx: return "Trend Micro"
        
        # Privacy / Specialized
        if "protonmail" in mx or "proton" in mx: return "ProtonMail"
        if "tutanota" in mx: return "Tuta"
        if "fastmail" in mx or "messagingengine" in mx: return "Fastmail"
        if "rackspace" in mx or "emailsrvr" in mx: return "Rackspace"
        if "icloud" in mx or "apple" in mx: return "Apple iCloud"
        if "yandex" in mx: return "Yandex"
        if "gmx" in mx: return "GMX"
        if "mail.ru" in mx: return "Mail.ru"
        
        # Dynamic Fallback for Custom
        # Try to extract the main domain from the MX record
        parts = mx.split('.')
        if len(parts) >= 2:
            return f"{parts[-2].capitalize()}.{parts[-1]} (Custom)"
            
        return "Custom/Private"
    except Exception as e:
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
    
    # Enterprise Leaders
    if "pphosted" in content or "proofpoint" in content: return "Proofpoint"
    if "mimecast" in content: return "Mimecast"
    if "barracuda" in content: return "Barracuda Networks"
    if "protection.outlook.com" in content or "mail.protection.outlook" in content: return "Microsoft EOP (Exchange Online Protection)"
    if "google.com" in content or "googlemail.com" in content: 
        if "aspmx" in mx: return "Google Workspace (Standard)"
        return "Google Postini/Cloud"

    # Legacy & Heavy Iron
    if "messagelabs" in content or "symantec" in content or "broadcom" in content: return "Symantec/Broadcom (MessageLabs)"
    if "ironport" in content or "iphmx" in content or "cisco" in content: return "Cisco IronPort"
    if "mcafee" in content or "mxlogic" in content: return "McAfee/Trellix"
    if "trendmicro" in content or "intersame" in content: return "Trend Micro"
    if "sophos" in content: return "Sophos Email Security"
    if "forcepoint" in content or "mailcontrol" in content: return "Forcepoint (Websense)"
    
    # Cloud & Specialized
    if "appriver" in content: return "AppRiver"
    if "spamtitan" in content: return "SpamTitan"
    if "fortimail" in content or "fortinet" in content: return "Fortinet FortiMail"
    if "fireeye" in content: return "FireEye"
    if "zscaler" in content: return "Zscaler"
    if "checkpoint" in content or "cpcloud" in content: return "Check Point Harmony"
    if "sonicwall" in content: return "SonicWall"
    if "watchguard" in content: return "WatchGuard"
    
    # Hosting Security
    if "secureserver" in content: return "GoDaddy Security"
    if "spamexperts" in content: return "SpamExperts (SolarWinds)"
    if "mailchannels" in content: return "MailChannels"
    
    # SaaS / Other
    if "sendgrid" in content: return "SendGrid"
    if "mailgun" in content: return "Mailgun"
    if "zoho" in content: return "Zoho Filters"
    if "protonmail" in content: return "ProtonMail Guard"
    
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

# Global sender cycle iterator
sender_cycle = None
last_sender_update = 0

def get_next_sender():
    global sender_cycle, last_sender_update
    import time
    from itertools import cycle
    
    # Refresh cycle every 5 minutes or if empty
    now = time.time()
    if sender_cycle is None or (now - last_sender_update > 300):
        try:
             db_senders = list(SMTPSender.objects.filter(is_active=True).values_list('email', flat=True))
             if not db_senders:
                 # Fallback to settings
                 db_senders = getattr(settings, 'SMTP_LIST', [])
             
             if db_senders:
                 # Shuffle once on load to randomize start, then cycle
                 random.shuffle(db_senders)
                 sender_cycle = cycle(db_senders)
                 last_sender_update = now
        except:
             pass

    if sender_cycle:
        try:
            return next(sender_cycle)
        except:
            pass
            
    # Fallback to random if cycle fails
    smtp_list = getattr(settings, 'SMTP_LIST', [])
    if smtp_list: return random.choice(smtp_list)
    return None

def check_smtp_detailed(email):
    """Detailed SMTP check returning (is_success, code, message, banner)"""
    try:
        smtp_sender = get_next_sender()
        if not smtp_sender:
             return False, 999, "Configuration Error: No Senders", ""
        
        # PROXY Handling (Simplified for brevity, assumes logic matches check_smtp)
        if proxy_config and proxy_config.value:
            try:
                import socks
                
                # Parse Proxy URL
                p_url = proxy_config.value.strip()
                proxy_type = socks.SOCKS5 # Default
                
                if p_url.startswith("http://"):
                    proxy_type = socks.HTTP
                    p_url = p_url.replace("http://", "")
                elif p_url.startswith("socks4://"):
                    proxy_type = socks.SOCKS4
                    p_url = p_url.replace("socks4://", "")
                elif p_url.startswith("socks5://"):
                    proxy_type = socks.SOCKS5
                    p_url = p_url.replace("socks5://", "")
                
                # Parse Auth/Host
                user, pwd = None, None
                if "@" in p_url:
                    auth, end = p_url.split("@")
                    if ":" in auth:
                        user, pwd = auth.split(":")
                    host, port = end.split(":")
                else:
                    host, port = p_url.split(":")
                
                # Apply Proxy
                socks.set_default_proxy(proxy_type, host, int(port), True, user, pwd)
                socket.socket = socks.socksocket
            except Exception as e:
                # If proxy fails, we fall back to direct connection but SHOULD log it
                print(f"Proxy Config Error: {e}")
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

        server = smtplib.SMTP(timeout=10) # Increased timeout slightly for TLS
        # Capture banner
        connect_code, connect_msg = server.connect(mx_host)
        banner = str(connect_msg)
        
        # Identify with EHLO first for modern servers
        try:
            server.ehlo(helo_host)
        except:
            server.helo(helo_host)

        # Opportunistic TLS
        try:
            if server.has_extn('STARTTLS'):
                import ssl
                # Create loose context - we want to talk, not verify perfect PKI
                context = ssl.create_default_context()
                context.check_hostname = False 
                context.verify_mode = ssl.CERT_NONE
                server.starttls(context=context)
                server.ehlo(helo_host) # Re-identify after TLS
        except Exception:
            # If TLS fails (not supported or handshake error), proceed in plain text
            pass

        server.mail(smtp_sender)
        code, msg = server.rcpt(email)
        server.quit()
        
        # 3. Analyze Response (Pattern Matching)
        msg_str = str(msg).lower()
        if code == 421 or "too many connections" in msg_str or "try again later" in msg_str:
             return False, 421, "Throttled: Server busy or Rate limited", banner
        
        if "policy violation" in msg_str or "spam" in msg_str or "blocked" in msg_str or "blacklisted" in msg_str:
             # It's a block, but the email might exist. 
             # We return code, but msg is specific.
             return False, code, f"Blocked: {msg}", banner

        return code == 250, code, msg, banner
    except (socket.timeout, socket.error, smtplib.SMTPException, dns.exception.Timeout) as e:
        err_str = str(e)
        if "421" in err_str:
             return False, 421, "Throttled: Connection Refused", ""
        return False, 999, err_str, ""
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
    out["is_spammy"] = out["is_disposable"]
    if not out["is_spammy"]:
        try:
            if SpamTrap.objects.filter(email=email).exists():
                out["is_spammy"] = True
        except:
            pass
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
