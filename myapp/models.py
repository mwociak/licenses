from django.db import models

class Machine(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine_id = models.CharField(max_length=64, unique=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return self.machine_id

class License(models.Model):
    id = models.BigAutoField(primary_key=True)
    license_key = models.CharField(max_length=128, unique=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='licenses')
    created_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    payload = models.JSONField(default=dict)
    signature = models.CharField(max_length=256)

    def __str__(self):
        return f"License {self.license_key} for {self.machine.machine_id}"

class LicenseAudit(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_time = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=64)
    machine_id = models.CharField(max_length=64, null=True, blank=True)
    license_key = models.CharField(max_length=128, null=True, blank=True)
    details = models.JSONField(default=dict)