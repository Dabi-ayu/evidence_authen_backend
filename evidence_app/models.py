from django.db import models
from .utils.blockchain import generate_ots

class Evidence(models.Model):
    title = models.CharField(max_length=255, default="Untitled")
    image = models.ImageField(upload_to='evidence/')
    is_authentic = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)
    metadata_status = models.CharField(max_length=100, blank=True)
    blockchain_hash = models.CharField(max_length=256, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Step 1: Save image to disk

        if is_new and self.image:
            # Step 2: Generate OTS and store hash
            from .utils.blockchain import generate_ots
            ots_path, hash_value = generate_ots(self.image.path)

            if hash_value:
                self.blockchain_hash = hash_value
                super().save(update_fields=["blockchain_hash"])  # Step 3: Save hash only
