import os
import django
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

# Konfiguracja środowiska Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
try:
    django.setup()
except RuntimeError:
    # Django has already been configured
    pass

from myapp.models import Machine, License, LicenseAudit

# Klucz symetryczny do podpisywania licencji.
# W prawdziwej aplikacji powinien być przechowywany bezpiecznie, np. w zmiennej środowiskowej.
SECRET_KEY = "your-super-secret-key-that-no-one-will-guess"
SIGNATURE_ALGO = 'sha256'

def get_machine_id():
    """Generuje unikalny identyfikator maszyny (taki sam jak w starym skrypcie)."""
    import platform
    machine_info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
    return hashlib.md5(machine_info.encode()).hexdigest()[:16]

def register_machine(machine_id: str, metadata: dict = None) -> Machine:
    """
    Rejestruje nową maszynę lub aktualizuje datę ostatniego 'widzenia'.
    Odpowiednik funkcji register_machine z SQL.
    """
    machine, created = Machine.objects.update_or_create(
        machine_id=machine_id,
        defaults={'last_seen': datetime.now(timezone.utc), 'metadata': metadata or {}}
    )

    LicenseAudit.objects.create(
        event_type='register_machine',
        machine_id=machine_id,
        details={'created': created, 'metadata': metadata or {}}
    )
    return machine

def _create_signature(machine_id: str, valid_from: datetime, valid_until: datetime, payload: dict) -> str:
    """Tworzy podpis HMAC dla danych licencji."""
    valid_from_str = valid_from.isoformat()
    valid_until_str = valid_until.isoformat() if valid_until else 'NULL'
    payload_str = str(payload)
    
    raw_data = f"{machine_id}|{valid_from_str}|{valid_until_str}|{payload_str}"
    
    signature = hmac.new(SECRET_KEY.encode(), raw_data.encode(), SIGNATURE_ALGO)
    return signature.hexdigest()

def generate_license_key(machine_id: str, valid_days: int = None, payload: dict = None) -> License:
    """
    Generuje nowy klucz licencyjny dla danej maszyny.
    Odpowiednik funkcji generate_license z SQL.
    """
    machine = Machine.objects.filter(machine_id=machine_id).first()
    if not machine:
        machine = register_machine(machine_id)

    valid_from = datetime.now(timezone.utc)
    valid_until = None
    if valid_days:
        valid_until = valid_from + timedelta(days=valid_days)
        
    license_key = f"MCP-{uuid.uuid4().hex.upper()}"
    payload = payload or {}

    signature = _create_signature(machine_id, valid_from, valid_until, payload)

    license_obj = License.objects.create(
        license_key=license_key,
        machine=machine,
        valid_from=valid_from,
        valid_until=valid_until,
        payload=payload,
        signature=signature
    )

    LicenseAudit.objects.create(
        event_type='generate_license',
        machine_id=machine_id,
        license_key=license_key,
        details={'valid_until': valid_until.isoformat() if valid_until else 'NULL', 'payload': payload}
    )
    
    return license_obj

def verify_license(machine_id: str, license_key: str) -> (bool, str, License | None):
    """
    Weryfikuje klucz licencyjny dla danej maszyny.
    Odpowiednik funkcji verify_license z SQL.
    """
    license_obj = License.objects.filter(license_key=license_key).first()

    if not license_obj:
        return False, 'license_not_found', None

    if license_obj.machine.machine_id != machine_id:
        return False, 'machine_mismatch', None

    if not license_obj.is_active:
        return False, 'license_inactive', None

    if license_obj.valid_until and license_obj.valid_until < datetime.now(timezone.utc):
        return False, 'license_expired', None
        
    # Weryfikacja podpisu
    expected_signature = _create_signature(
        license_obj.machine.machine_id,
        license_obj.valid_from,
        license_obj.valid_until,
        license_obj.payload
    )

    if not hmac.compare_digest(expected_signature, license_obj.signature):
        return False, 'signature_mismatch', None

    LicenseAudit.objects.create(
        event_type='verify_license',
        machine_id=machine_id,
        license_key=license_key,
        details={'ok': True}
    )

    return True, 'ok', license_obj
