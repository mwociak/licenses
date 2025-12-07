import hmac
import hashlib
import time
import argparse

SECRET = "TU_WKLEJ_SECRET_Z_BAZY"  # np. z SELECT secret FROM license_secret

def generate_license(machine_id, days_valid=365):
    expires = int(time.time() + days_valid * 86400)
    payload = f"{machine_id}|{expires}"
    signature = hmac.new(
        SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature, expires

def verify_license(machine_id, license_key, expires):
    payload = f"{machine_id}|{expires}"
    expected = hmac.new(
        SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return expected == license_key and time.time() < expires

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("machine_id")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    key, exp = generate_license(args.machine_id, args.days)
    print("License Key:", key)
    print("Expires:", exp)
