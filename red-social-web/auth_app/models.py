from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    ID_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
        ('TI', 'Tarjeta de Identidad'),
    ]

    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    type_identification = models.CharField(
        max_length=2,
        choices=ID_CHOICES,
        blank=True,
        null=True,
        verbose_name="Tipo de Identificación"
    )
    identification = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número de Identificación"
    )
    photoprofile_path = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # Agregar otro campo que se requiera

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'type_identification', 'identification']

    def __str__(self):
        return self.email