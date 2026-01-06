import dns.resolver
import requests
import socket

DNSBL_LIST = [
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "b.barracudacentral.org",
    "dnsbl.sorbs.net",
    "psbl.surriel.com",
    "bl.spamcannibal.org"
]

def get_public_ip(proxy_url=None):
    """
    Fetches the public IP address. 
    If proxy is configured, uses it to see what the world sees.
    """
    try:
        proxies = {}
        if proxy_url:
            proxies = {'http': proxy_url, 'https': proxy_url}
        
        # Use a reliable IP echo service
        resp = requests.get('https://api.ipify.org', proxies=proxies, timeout=5)
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        pass
    return None

def check_ip_reputation(ip_address):
    """
    Checks the IP against common DNSBLs.
    Returns a list of dicts: {'scanner': 'Spamhaus', 'status': 'Listed'/'Clean'}
    """
    results = []
    
    if not ip_address:
        return [{'scanner': 'System', 'status': 'Error: Could not determine Public IP'}]

    # Reverse IP for DNSBL lookup (1.2.3.4 -> 4.3.2.1)
    try:
        reversed_ip = ".".join(reversed(ip_address.split(".")))
    except:
        return [{'scanner': 'System', 'status': 'Error: Invalid IP format'}]

    for bl in DNSBL_LIST:
        query = f"{reversed_ip}.{bl}"
        try:
            dns.resolver.resolve(query, "A")
            # If resolve succeeds, it is listed
            results.append({'scanner': bl, 'status': 'LISTED (Blacklisted)', 'is_bad': True})
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            # If resolve fails, it is clean
            results.append({'scanner': bl, 'status': 'Clean', 'is_bad': False})
        except:
            results.append({'scanner': bl, 'status': 'Timeout/Error', 'is_bad': False})
            
    return results
