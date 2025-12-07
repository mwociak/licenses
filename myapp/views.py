import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .license_logic import register_machine, verify_license, generate_license_key, get_machine_id

@csrf_exempt
@require_http_methods(["POST"])
def verify_license_api(request):
    """
    API Endpoint do weryfikacji licencji.
    Oczekiwany JSON:
    {
        "license_key": "KLUCZ_LICENCJI",
        "machine_id": "ID_MASZYNY"
    }
    """
    try:
        data = json.loads(request.body)
        license_key = data.get('license_key')
        machine_id = data.get('machine_id')

        if not license_key or not machine_id:
            return JsonResponse({'valid': False, 'reason': 'missing_data'}, status=400)

        is_valid, reason, license_obj = verify_license(machine_id, license_key)

        if is_valid:
            response_data = {
                'valid': True,
                'reason': 'ok',
                'license_details': {
                    'expires_at': license_obj.valid_until.isoformat() if license_obj.valid_until else None,
                    'payload': license_obj.payload
                }
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'valid': False, 'reason': reason}, status=403)

    except json.JSONDecodeError:
        return JsonResponse({'valid': False, 'reason': 'invalid_json'}, status=400)
    except Exception as e:
        return JsonResponse({'valid': False, 'reason': f'server_error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def register_and_generate_trial_api(request):
    """
    API Endpoint do rejestracji maszyny i generowania licencji próbnej.
    Oczekiwany JSON:
    {
        "machine_id": "ID_MASZYNY",
        "metadata": { ... } // opcjonalnie
    }
    """
    try:
        data = json.loads(request.body)
        machine_id = data.get('machine_id')
        metadata = data.get('metadata', {})

        if not machine_id:
            return JsonResponse({'success': False, 'reason': 'missing_machine_id'}, status=400)

        # Zarejestruj maszynę
        register_machine(machine_id, metadata)
        
        # Wygeneruj 7-dniową licencję próbną
        trial_license = generate_license_key(machine_id, valid_days=7)

        response_data = {
            'success': True,
            'license_key': trial_license.license_key,
            'expires_at': trial_license.valid_until.isoformat()
        }
        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'reason': 'invalid_json'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'reason': f'server_error: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def get_machine_id_api(request):
    """
    Prosty endpoint pomocniczy do zwracania ID maszyny (jeśli serwer jest lokalny)
    W praktyce ID maszyny będzie generowane po stronie klienta.
    """
    machine_id = get_machine_id()
    return JsonResponse({'machine_id': machine_id})
