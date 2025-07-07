# evidence_app/models.py
from django.db import models

class Evidence(models.Model):
    image = models.ImageField(upload_to='evidence/')
    is_authentic = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)
    metadata_status = models.CharField(max_length=100, blank=True)
    blockchain_hash = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence {self.id} - {'Authentic' if self.is_authentic else 'Tampered'}"