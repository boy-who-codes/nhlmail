import smtplib
import dns.resolver
import socket
import sys

def check_connectivity(target_email="test@gmail.com"):
    print(f"[-] Starting connectivity check for {target_email}...")
    
    try:
        domain = target_email.split("@")[1]
        print(f"[-] Resolving MX records for {domain}...")
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_records = sorted(mx_records, key=lambda x: x.preference)
        mx_host = str(mx_records[0].exchange)
        print(f"[+] Found MX: {mx_host}")
    except Exception as e:
        print(f"[!] DNS Resolution Failed: {e}")
        return

    print(f"[-] Attempting to connect to {mx_host}:25...")
    try:
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(1)
        server.connect(mx_host, 25)
        print(f"[+] Connection Established!")
        server.helo()
        server.quit()
        print(f"[+] SMTP Handshake Successful.")
    except socket.timeout:
        print("[!] ERROR: Connection Timed Out.")
        print("    -> LIKELY CAUSE: ISP Blocking Port 25 (common in residential connections).")
        print("    -> SOLUTION: Use a VPN, Proxy, or deploy to a Cloud Server (AWS/DigitalOcean).")
    except ConnectionRefusedError:
        print("[!] ERROR: Connection Refused.")
        print("    -> CAUSE: Firewall or Server blocking IP.")
    except Exception as e:
        print(f"[!] ERROR: {e}")

if __name__ == "__main__":
    check_connectivity()
