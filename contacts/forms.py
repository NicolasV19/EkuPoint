from django import forms
from .models import Aktivitas, Pelanggaran, User, Angkatan, Prodi
#from .views import is_reviewer
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .context_processors import user_groups


User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        #fields = ("username", "email", "password1", "password2")
        fields = ("username", "first_name", "last_name", "password1", "password2", "nim", "prodi", "angkatan")
    
    #def clean_email(self):
    #    email = self.cleaned_data.get('email')
    #    if User.objects.filter(email=email).exists():
    #        raise ValidationError("A user with this email already exists.")
    #    return email
    
        # prodi = forms.ModelChoiceField(
        # queryset=Prodi.objects.all().order_by('-prodi'), # Gets all Angkatan objects
        # required=True,
        # empty_label="Pilih Program Studi...", # This is the "disabled selected" option
        # label="Program Studi",
        # # This helps Django render it with the right ID for your label
        # widget=forms.Select(attrs={'id': 'id_prodi', 'class': 'form-select'}) 
        # )

        # angkatan = forms.ModelChoiceField(
        # queryset=Angkatan.objects.all().order_by('-angkatan'), # Gets all Angkatan objects
        # required=True,
        # empty_label="Pilih angkatan...", # This is the "disabled selected" option
        # label="Angkatan",
        # # This helps Django render it with the right ID for your label
        # widget=forms.Select(attrs={'id': 'id_angkatan', 'class': 'form-select'}) 
        # )

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Confirm Password'
            }),
            'nim': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'NIM'
            }),
            'prodi': forms.Select(attrs={
                'class': 'form-select',
            }),
            'angkatan': forms.Select(attrs={
                'class': 'form-select',
            })
        }


class AktivitasForm(forms.ModelForm):
    class Meta:
        model = Aktivitas
        # We only need the user to fill out the keterangan.
        # The 'user' will be set automatically, and 'aturan_merit' will be chosen via dropdowns.
        #fields = ['aktivitas', 'jenis', 'lingkup', 'kuantitas', 'file', 'status', 'keterangan']
        fields = [ 'aturan_merit', 'kuantitas', 'file', 'status', 'keterangan',]
        widgets = {
            'aturan_merit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'kuantitas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'keterangan': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Keterangan (opsional)',
                'rows': 3
            }),
            'file': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    # A better check: Hide the field for any user who is NOT staff.
    # This covers students and any other non-admin user types.
        if not user or not user.is_staff:
            self.fields.pop('status', None)

        if self.instance and self.instance.pk:
            user = kwargs.get("user")
            if self.instance.status == 'rejected':
                # Make fields readonly/disabled
                self.fields['aturan_merit'].disabled = True
                self.fields['aturan_merit'].widget.attrs['class'] = 'form-control bg-light'

                self.fields['kuantitas'].widget.attrs['readonly'] = True
                self.fields['kuantitas'].widget.attrs['class'] = 'form-control bg-light'

                self.fields['file'].widget.attrs['readonly'] = True
                self.fields['file'].widget.attrs['class'] = 'form-control bg-light'

                self.fields['keterangan'].widget.attrs['readonly'] = True
                self.fields['keterangan'].widget.attrs['class'] = 'form-control bg-light'

                    # self.fields['status'].widget.attrs['disable'] = True
                    # self.fields['status'].widget.attrs['class'] = 'form-control bg-light'
                self.fields.pop('status', None)

        # if self.instance and self.instance.pk:
        #     user = kwargs.get("user")
        #     if user and (user.is_staff or user.is_superuser):
        #         # Make fields readonly/disabled
        #         self.fields['aturan_merit'].disabled = True
        #         self.fields['aturan_merit'].widget.attrs['class'] = 'form-control bg-light'

        #         self.fields['kuantitas'].widget.attrs['readonly'] = True
        #         self.fields['kuantitas'].widget.attrs['class'] = 'form-control bg-light'

        #         self.fields['file'].widget.attrs['readonly'] = True
        #         self.fields['file'].widget.attrs['class'] = 'form-control bg-light'


class PelanggaranForm(forms.ModelForm):
    # user = forms.ModelChoiceField(queryset=User.objects.all())
    # We create the user field explicitly to make it a dropdown of all users.
    #user = forms.ModelChoiceField(queryset=User.objects.all(), label="Pilih Mahasiswa")
    class Meta:
        model = Pelanggaran
        # The admin will select the user and provide a reason.
        #fields = ['pelanggaran', 'lingkup', 'aturan_demerit', 'kuantitas', 'keterangan']
        fields = ['user', 'aturan_demerit', 'kuantitas', 'keterangan']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'aturan_demerit': forms.Select(attrs={
                'class': 'form-select'
            }),
            'kuantitas': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 1
            }),
            'keterangan': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Keterangan (opsional)',
                'rows': 3
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['user'].label_from_instance = lambda obj: obj.get_full_name() or obj.username
        self.fields['user'].queryset = User.objects.filter(groups=1).order_by('first_name', 'last_name')
        
    def clean_user(self):
        user = self.cleaned_data['user']
        full_name = user.get_full_name()
        # ... further processing or validation
        return user