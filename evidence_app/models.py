from django.db import models
from .utils.imagehash import generate_sha256_hash  # ✅ Renamed utility function

class Evidence(models.Model):
    title = models.CharField(max_length=255, default="Untitled")
    image = models.ImageField(upload_to='evidence/')
    is_authentic = models.BooleanField(default=False)
    confidence = models.FloatField(default=0.0)
    metadata_status = models.CharField(max_length=100, blank=True)
    image_hash = models.CharField(max_length=256, null=True, blank=True)  # ✅ Just a hash now

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Save image first to get the path

        if is_new and self.image:
            # ✅ Generate SHA256 hash for the image and store it
            hash_value = generate_sha256_hash(self.image.path)

            if hash_value:
                self.image_hash = hash_value
                super().save(update_fields=["image_hash"])
