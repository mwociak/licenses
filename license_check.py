import requests
import hmac
import hashlib
import time

SECRET = "wzkL258k0tPdIAfpu1nwBKoLQQv+dZHby9tvrth7xI8="

import requests

import hmac

import hashlib

import time



SECRET = "wzkL258k0tPdIAfpu1nwBKoLQQv+dZHby9tvrth7xI8="



def verify_license_local(machine_id, license_string):

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



def verify_license_server(machine_id, license_string):

    try:

        signature, expires_str = license_string.split('.')

        expires = int(expires_str)

    except ValueError:

        print("Błąd: Nieprawidłowy format klucza licencji.")

        return None



    try:

        resp = requests.post(

            "https://license-server-django.onrender.com/verify",

            json={"machine_id": machine_id, "license_key": signature, "expires": expires},

            timeout=5

        )

        if resp.status_code == 200:

            data = resp.json()

            return data.get("valid", False)

        else:

            print(f"Serwer zwrócił błąd: {resp.status_code}")

            return None

    except Exception as e:

        print(f"Błąd komunikacji z serwerem: {e}")

        return None



def verify_with_fallback(machine_id, license_string):

    result = verify_license_server(machine_id, license_string)

    if result is True:

        print("✅ Licencja zweryfikowana przez serwer.")

        return True

    elif result is None:

        print("⚠️ Serwer niedostępny – sprawdzam lokalnie...")

        if verify_license_local(machine_id, license_string):

            print("✅ Licencja poprawna (tryb offline).")

            return True

        else:

            print("❌ Licencja niepoprawna.")

            return False

    else:

        print("❌ Licencja odrzucona przez serwer.")

        return False



if __name__ == "__main__":

    machine_id = "8357154650f182c1"

    # Nowy format: klucz.czas_wygaśnięcia

    license_string = "d877e6a76511a547a42a8b9818814529323f66343513b6480112184282583a21.1796762031"



    verify_with_fallback(machine_id, license_string)
