import os
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class CalculationResult(models.Model):
    filename = models.CharField(max_length=255)  # The name of the file
    file_content = models.BinaryField(blank=True, null=True)  # The binary content of the file (Excel/CSV)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Tracks the user who uploaded/created the file
    created_by_username = models.CharField(max_length=255, blank=True, null=True)  # Store the username as a string

    def save(self, *args, **kwargs):
        if self.created_by and not self.created_by_username:
            self.created_by_username = self.created_by.username  # Set the username field
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename} by {self.created_by_username or 'Unknown'}"


class GptResult(models.Model):
    prefix = models.CharField(max_length=10)  # New field for project code like TIPA or TIPX
    filename = models.CharField(max_length=255)  # The name of the GPT result file
    file_content = models.BinaryField(blank=True, null=True)  # The binary content of the file
    prompt = models.TextField()  # Store the GPT prompt
    model_used = models.CharField(max_length=255, blank=True, null=True)  # The GPT model used
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Tracks the user who uploaded/created the file
    created_by_username = models.CharField(max_length=255, blank=True, null=True)  # Store the username as a string

    def save(self, *args, **kwargs):
        if self.created_by and not self.created_by_username:
            self.created_by_username = self.created_by.username  # Set the username field
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.filename} by {self.created_by_username or 'Unknown'}"

