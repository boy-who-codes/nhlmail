import smtplib
import ssl

def test_587(target_email="test@gmail.com"):
    mx_host = "gmail-smtp-msa.l.google.com" # Gmail's Submission Server often used for 587
    # Note: Real MX records (gmail-smtp-in.l.google.com) usually DON'T listen on 587.
    # We have to check if the MX *or* the Submission server allows unauthenticated validation.
    
    # Let's try the actual MX first, just in case.
    mx_real = "gmail-smtp-in.l.google.com"
    
    print(f"[-] Testing 587 on MX: {mx_real}...")
    try:
        server = smtplib.SMTP(mx_real, 587, timeout=5)
        server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.mail("test@example.com")
        code, msg = server.rcpt(target_email)
        print(f"[+] Result: {code} {msg}")
        server.quit()
    except Exception as e:
        print(f"[!] Failed on MX 587: {e}")

    print(f"\n[-] Testing 587 on MSA (Submission): {mx_host}...")
    try:
        server = smtplib.SMTP(mx_host, 587, timeout=5)
        server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.mail("test@example.com")
        code, msg = server.rcpt(target_email)
        print(f"[+] Result: {code} {msg}")
        server.quit()
    except Exception as e:
        print(f"[!] Failed on MSA 587: {e}")

if __name__ == "__main__":
    test_587()
