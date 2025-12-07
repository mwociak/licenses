from django.db import models
import uuid

class Machine(models.Model):
    id = models.BigAutoField(primary_key=True)
    machine_id = models.TextField(unique=True, null=False)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return self.machine_id

class License(models.Model):
    id = models.BigAutoField(primary_key=True)
    license_key = models.TextField(unique=True, null=False)
    machine = models.ForeignKey(Machine, to_field='machine_id', on_delete=models.CASCADE, related_name='licenses')
    created_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    payload = models.JSONField(default=dict)
    signature = models.TextField(null=False)

    def __str__(self):
        return f"License {self.license_key} for {self.machine.machine_id}"

class LicenseAudit(models.Model):
    id = models.BigAutoField(primary_key=True)
    event_time = models.DateTimeField(auto_now_add=True)
    event_type = models.TextField(null=False)
    machine_id = models.TextField(null=True)
    license_key = models.TextField(null=True)
    details = models.JSONField(default=dict)

