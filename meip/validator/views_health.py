import requests
import socket
import dns.resolver
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connections
from django.conf import settings
from .models import SystemConfig

class SystemHealthView(APIView):
    permission_classes = [AllowAny]

    def get_client_ip(self):
        try:
            # External service to get public IP
            return requests.get('https://ifconfig.me/ip', timeout=5).text.strip()
        except:
            return "Unknown"

    def check_dnsbl(self, ip, dnsbl_provider):
        try:
            if ip == "Unknown": return False
            reversed_ip = ".".join(reversed(ip.split(".")))
            query = f"{reversed_ip}.{dnsbl_provider}"
            dns.resolver.resolve(query, "A")
            return True # Listed (Bad)
        except:
            return False # Not Listed (Good)

    def get(self, request):
        health_data = {
            "status": "online",
            "database": "unknown",
            "redis": "unknown",
            "external_ip": "unknown",
            "ip_reputation": {}
        }

        # 1. Database Check
        try:
            cursor = connections['default'].cursor()
            cursor.execute("SELECT 1")
            health_data['database'] = "connected"
        except Exception as e:
            health_data['database'] = f"error: {str(e)}"
            health_data['status'] = "degraded"

        # 2. Redis Check
        try:
            # Simple heuristic: if we can import logic from settings check
            import redis
            r_url = getattr(settings, 'CELERY_BROKER_URL', '')
            if r_url:
                r = redis.from_url(r_url, socket_timeout=3)
                r.ping()
                health_data['redis'] = "connected"
            else:
                health_data['redis'] = "not_configured"
        except Exception as e:
             health_data['redis'] = f"error: {str(e)}"
             # Not always critical if using eager mode, but good to know

        # 3. External IP
        ip = self.get_client_ip()
        health_data['external_ip'] = ip

        # 4. Reputation Check
        if ip != "Unknown":
            # Common DNSBLs
            bls = {
                "Zen Spamhaus": "zen.spamhaus.org",
                "Barracuda": "b.barracudacentral.org",
                "SpamCop": "bl.spamcop.net"
            }
            for name, host in bls.items():
                is_listed = self.check_dnsbl(ip, host)
                health_data['ip_reputation'][name] = "LISTED (BAD)" if is_listed else "CLEAN"
        
        return Response(health_data)
