from django.db import models

# Create your models here.

# -----------------users registration-----------------
class userProfile(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    confirm_password = models.CharField(max_length=255)  # Not recommended to store, use validation
    mobile = models.CharField(max_length=15, unique=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    status = models.CharField(max_length=10,  default='waiting')

    def __str__(self):
        return self.name
    




