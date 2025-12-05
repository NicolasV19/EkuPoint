from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator
from django.db.models import F


class Angkatan(models.Model):
    angkatan = models.CharField(max_length=4, blank=True, null=True)
    modal_poin = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.angkatan}"
    
class Prodi(models.Model):
    prodi = models.CharField(max_length=50, blank=True, null=True)
    strata = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return f"{self.prodi} {self.strata}"
    


class User(AbstractUser):
    #def save(self, *args, **kwargs):
    #      self.set_password(self.password)
    #      super().save(*args, **kwargs)
    nim = models.CharField(max_length=10, blank=True, null=True)
    prodi = models.ForeignKey(Prodi, on_delete=models.SET_NULL, blank=True, null=True, related_name='users_prodi')
    angkatan = models.ForeignKey(Angkatan, on_delete=models.SET_NULL, blank=True, null=True, related_name='users')

    @property
    def modal_poin_awal(self):
        if self.angkatan:
            return self.angkatan.modal_poin
        
        return 100
    
    def __str__(self):
        return f"{self.username}"



class Merit(models.Model):

    AKT_LINGKUP_CHOICES = (
        ('internal', 'Internal'),
        ('eksternal', 'Eksternal'),
    )
    

    bidang = models.TextField()
    aktivitas = models.TextField()
    jenis = models.TextField()
    lingkup = models.TextField(max_length=25, choices=AKT_LINGKUP_CHOICES, default='internal')
    poin = models.IntegerField()

    def __str__(self):
        return f"{self.bidang}: {self.aktivitas} - {self.jenis} dalam lingkup {self.lingkup} = {self.poin} points"
    

class Demerit(models.Model):
        
    AKT_LINGKUP_CHOICES = (
        ('internal', 'Internal'),
        ('eksternal', 'Eksternal'),
    )
    pelanggaran = models.TextField()
    lingkup = models.TextField(max_length=25, choices=AKT_LINGKUP_CHOICES, default='internal')
    poin = models.IntegerField()

    def __str__(self):
        return f"Pelanggaran: {self.pelanggaran} dalam lingkup {self.lingkup} = {self.poin} points"



class Aktivitas(models.Model):
    AKT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    # The user who performed the activity
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aktivitas_records', blank=True, null=True)
    
    # This is the KEY: A single link to the specific rule in the Merit "rulebook"
    aturan_merit = models.ForeignKey(Merit, on_delete=models.CASCADE, related_name='instances', blank=True, null=True)

    # Alternatif; dibuat per detail, bukan langsung seperti di atas
    aktivitas = models.ForeignKey(Merit, on_delete=models.CASCADE, related_name='aktivitas_detail', blank=True, null=True)
    jenis = models.ForeignKey(Merit, on_delete=models.CASCADE, related_name='jenis_detail', blank=True, null=True)
    lingkup = models.ForeignKey(Merit, on_delete=models.CASCADE, related_name='lingkup_detail', blank=True, null=True)
    poin = models.ForeignKey(Merit, on_delete=models.CASCADE, related_name='poin_detail', blank=True, null=True)    
    
    # Details for THIS SPECIFIC instance (e.g., notes, proof)
    kuantitas = models.IntegerField(default=1)
    keterangan = models.TextField(blank=True, null=True)
    file = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=AKT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    @property
    def poin(self):
        """Calculates the total points dynamically from the chosen rule."""
        if self.aturan_merit:
            return self.aturan_merit.poin * self.kuantitas
        return 0

    def __str__(self):
        # We can get all the details from the linked rule!
        return f"{self.user.username} - {self.aturan_merit.aktivitas} ({self.aturan_merit.jenis})"


class Pelanggaran(models.Model):
    # The user who committed the violation
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pelanggaran_records', blank=True, null=True)
    
    # A single link to the specific demerit rule
    aturan_demerit = models.ForeignKey(Demerit, on_delete=models.CASCADE, related_name='instances', blank=True, null=True)

    # Alternatif; dibuat per detail, bukan langsung seperti di atas
    pelanggaran = models.ForeignKey(Demerit, on_delete=models.CASCADE, related_name='pelanggaran_detail', blank=True, null=True)
    lingkup = models.ForeignKey(Demerit, on_delete=models.CASCADE, related_name='lingkup_detail', blank=True, null=True)
    poin = models.ForeignKey(Demerit, on_delete=models.CASCADE, related_name='poin_detail', blank=True, null=True)

    # Details for THIS SPECIFIC instance
    kuantitas = models.IntegerField(default=1)
    keterangan = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    @property
    def poin(self):
        """Calculates the total demerit points dynamically."""
        if self.aturan_demerit:
            return self.aturan_demerit.poin * self.kuantitas
        return 0
    
    def get_user_full_name(self):
        return self.user.get_full_name()

    def __str__(self):
        return f"{self.user.username} - {self.aturan_demerit.pelanggaran}"
    


    
