import hmac
import hashlib
import time
import argparse

SECRET = "wzkL258k0tPdIAfpu1nwBKoLQQv+dZHby9tvrth7xI8="  # np. z SELECT secret FROM license_secret

def generate_license(machine_id, days_valid=365):
    expires = int(time.time() + days_valid * 86400)
    payload = f"{machine_id}|{expires}"
    signature = hmac.new(
        SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{signature}.{expires}"

def verify_license(machine_id, license_string):
    try:
        signature, expires_str = license_string.split('.')
        expires = int(expires_str)
    except ValueError:
        return False  # Invalid license format

    payload = f"{machine_id}|{expires}"
    expected_signature = hmac.new(
        SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature) and time.time() < expires

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("machine_id")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    license_key = generate_license(args.machine_id, args.days)
    print("License Key:", license_key)
