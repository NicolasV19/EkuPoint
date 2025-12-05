from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required # gatekeeper halaman bagi yg blm login
from django.http import JsonResponse, HttpResponseForbidden, FileResponse
import io
from django.db.models import Q # querying, biasanya dipake untuk filtering
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout # biar bs logout
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Aktivitas, Merit, Pelanggaran, Demerit, Angkatan, Prodi # import dri models.py
from .forms import AktivitasForm, PelanggaranForm # import dri forms.py
from django.contrib.auth import login # biar bs login
from django.contrib.auth.views import LoginView 
from django.urls import reverse
import json
from django.contrib.auth.models import Group
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db.models import F
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Frame, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from django.utils import timezone
import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line

# Create your views here.
#@login_required
#def index(request):
#    contacts = request.user.contacts.all().order_by('-created_at')
#    context = {
#        'contacts': contacts,
#        'form': ContactForm()
#        }
#    return render(request, 'contacts.html', context)

User = get_user_model()


def index(request):
    aktivitas_records = Aktivitas.objects.all().order_by('-created_at')
    status = Aktivitas.status
    context = {'aktivitas_records': aktivitas_records, 'status': status}
    user = request.user
    is_student = request.user.groups.filter(name="Student").exists()
    if user.is_superuser or user.is_staff:
        # Admin sees everything
        aktivitas_records = Aktivitas.objects.all().order_by('-created_at')

    elif is_student:
        # Students:
        # 1. Can see approved records from anyone
        # 2. Can see their own records, even if Rejected or Pending
        aktivitas_records = Aktivitas.objects.filter(
            Q(status="approved")
        ).order_by('-created_at')

    else:
        # fallback, if you have other groups
        aktivitas_records = Aktivitas.objects.filter(status="approved").order_by('-created_at')

    aktivitas_count = aktivitas_records.count()
    pelanggaran_count = Pelanggaran.objects.count()
    total_mhs = User.objects.filter(groups=1).count()
    context = {'aktivitas_records': aktivitas_records, 'status': status, 'aktivitas_count': aktivitas_count, 'pelanggaran_count': pelanggaran_count, 'total_mhs': total_mhs}
    if request.user.is_authenticated:
        # if is_student:
        #     return redirect('aktivitas')
        # else:
        # # User is logged in - redirect to dashboard
            return redirect('dashboard')
    # if request.user.is_authenticated:
    #     if user.is_superuser or user.is_staff:
    #         return render(request, 'dashboard.html', context)
    #     else:
    #     # User is logged in - redirect to dashboard
    #         return render(request, 'aktivitas_list.html', context)
    else:
        # User is not logged in - show homepage
        return render(request, 'homepage.html', context)



@login_required
def logout_view(request):
    logout(request)
    return redirect('/') # Redirect to your login page or homepage after logout


class CustomLoginView(LoginView):
    template_name = "contacts/login.html"

    def dispatch(self, request, *args, **kwargs):
        # If already logged in, don’t show login again
        if request.user.is_authenticated:
#            if request.user.is_staff:
#                return redirect(reverse('admin:index'))
                return redirect('/dashboard/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/dashboard/'

#    def get_success_url(self):
#        user = self.request.user
#        if user.is_staff:
#            return reverse('admin:index')  # staff → admin
#        return '/'  # normal users → your site


#EKUPOINT
@login_required
def aktivitas_list(request):
    # deklarasi bbrp variable
    status = Aktivitas.status
    user = request.user
    is_student = request.user.groups.filter(name="Student").exists()

    # mhs gabisa liat data akt mhs lain kalo blm di approve 
    # kecuali admin (developer) sama admin (kemahasiswaan)
    # UPDATE: kalo statusnya Rejected hanya bisa dilihat oleh pemilik data itu doang
    # old code:
    # if is_student:
    #     aktivitas_records = Aktivitas.objects.filter(status="approved").order_by('-created_at')
    # elif user.is_superuser or user.is_staff:
    #     aktivitas_records = Aktivitas.objects.all().order_by('-created_at')

    if user.is_superuser or user.is_staff:
        # Admin sees everything
        aktivitas_records = Aktivitas.objects.all().order_by('-created_at')

    elif is_student:
        # Students:
        # 1. Can see approved records from anyone
        # 2. Can see their own records, even if Rejected or Pending
        aktivitas_records = Aktivitas.objects.filter(
            Q(user=user)
        ).order_by('-created_at')

    else:
        # fallback, if you have other groups
        aktivitas_records = Aktivitas.objects.filter(status="approved").order_by('-created_at')

    context = {'aktivitas_records': aktivitas_records, 'status': status}
    return render(request, 'aktivitas_list.html', context)

@login_required
def aktivitas_add(request):
    """Handles the form for adding a new Aktivitas."""
    user = request.user
    if request.method == 'POST':
        form = AktivitasForm(request.POST, user=request.user)
        merit_id = request.POST.get('aturan_merit')
        
        if form.is_valid() and merit_id:
            merit_rule = Merit.objects.get(pk=merit_id)
            
            # Create the instance but don't save to DB yet
            new_aktivitas = form.save(commit=False)
            
            # Add the logged-in user and the selected rule
            new_aktivitas.user = request.user # Assumes user is logged in
            new_aktivitas.aturan_merit = merit_rule
            new_aktivitas.save()
            
            return redirect('aktivitas_list')

    # For a GET request, show the empty form
    form = AktivitasForm()
    bidang_options = Merit.objects.values_list('bidang', flat=True).distinct().order_by('bidang')
    context = {
        'form': form,
        'bidang_options': bidang_options,
    }
    return render(request, 'aktivitas_add.html', context)

@login_required
def aktivitas_edit(request, pk):
    aktivitas = get_object_or_404(Aktivitas, pk=pk)
    user = request.user

    # --- NEW PERMISSION CHECK ---
    # Allow if user is the creator, an assigned reviewer, or an admin.
    if not (user or user.is_superuser):
        return HttpResponseForbidden("You don't have permission to edit this proposal.")

    if request.method == 'POST':
        form = AktivitasForm(request.POST, request.FILES, instance=aktivitas, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('aktivitas_list')
    else:
        form = AktivitasForm(instance=aktivitas, user=request.user)

    return render(request, 'aktivitas_add.html', {
        'form': form,
        'title': 'Edit Aktivitas',
        'aktivitas': aktivitas
    })

@login_required
def aktivitas_delete(request, pk):
    aktivitas = get_object_or_404(Aktivitas, pk=pk)
    user = request.user
    
    # --- NEW PERMISSION CHECK ---
    # Only the creator or an admin should be able to delete.
    if not (user or user.is_superuser):
        return HttpResponseForbidden("You don't have permission to delete this proposal.")

    if request.method == 'POST':
        aktivitas.delete()
        return redirect('aktivitas_list')

    return render(request, 'aktivitas_confirm_delete.html')

# --- HTMX Partial Views for Aktivitas ---

def get_aktivitas_options(request):
    bidang = request.GET.get('bidang')
    aktivitas_options = Merit.objects.filter(bidang=bidang).values_list('aktivitas', flat=True).distinct().order_by('aktivitas')
    context = {'aktivitas_options': aktivitas_options}
    return render(request, 'partials/aktivitas_options.html', context)

def get_jenis_options(request):
    bidang = request.GET.get('bidang')
    aktivitas = request.GET.get('aktivitas')
    jenis_options = Merit.objects.filter(bidang=bidang, aktivitas=aktivitas).values_list('jenis', flat=True).distinct().order_by('jenis')
    context = {'jenis_options': jenis_options}
    return render(request, 'partials/jenis_options.html', context)

def get_lingkup_options(request):
    bidang = request.GET.get('bidang')
    aktivitas = request.GET.get('aktivitas')
    jenis = request.GET.get('jenis')
    # Get the final Merit objects that match
    rules = Merit.objects.filter(bidang=bidang, aktivitas=aktivitas, jenis=jenis)
    context = {'rules': rules}
    return render(request, 'partials/lingkup_options.html', context)


# ========== PELANGGARAN VIEWS ==========

@login_required
def pelanggaran_list(request):
    user = request.user

    # jika user superadmin / admin semua data keliatan
    if user.is_superuser or user.is_staff:
        pelanggaran_records = Pelanggaran.objects.all()
    # jika user bukan admin (alias mahasiswa) cuma bisa liat datanya dia doang, yg lain kgk
    else:
        pelanggaran_records = Pelanggaran.objects.filter(
            Q(user=user)
        ).distinct() # Use .distinct() to avoid duplicates

    # Order by creation date (newest first)
    pelanggaran_records = pelanggaran_records.order_by('-created_at')

    context = {
        'pelanggaran_records': pelanggaran_records,
        'form': PelanggaranForm(),
    }
    return render(request, 'pelanggaran_list.html', context)

@login_required
def pelanggaran_add(request):
    """Handles the form for adding a new Aktivitas."""
    if request.method == 'POST':
        form = PelanggaranForm(request.POST)
        demerit_id = request.POST.get('aturan_demerit')
        
        if form.is_valid() and demerit_id:
            demerit_rule = Demerit.objects.get(pk=demerit_id)
            
            # Create the instance but don't save to DB yet
            new_pelanggaran = form.save(commit=False)
            
            # Add the logged-in user and the selected rule
            # new_pelanggaran.user = request.user # Assumes user is logged in
            new_pelanggaran.aturan_demerit = demerit_rule
            new_pelanggaran.save()
            
            return redirect('pelanggaran_list')

    # For a GET request, show the empty form
    form = PelanggaranForm()
    # bidang_options = Demerit.objects.values_list('bidang', flat=True).distinct().order_by('bidang')
    context = {
        'form': form,
        #'bidang_options': bidang_options,
    }
    return render(request, 'pelanggaran_add.html', context)

@login_required
def pelanggaran_edit(request, pk):
    pelanggaran = get_object_or_404(Pelanggaran, pk=pk)
    user = request.user
 # --- NEW PERMISSION CHECK ---
    # Allow if user is the creator, an assigned reviewer, or an admin.
    if not (user or user.is_superuser):
        return HttpResponseForbidden("You don't have permission to edit this proposal.")

    if request.method == 'POST':
        form = PelanggaranForm(request.POST, request.FILES, instance=pelanggaran, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('pelanggaran_list')
    else:
        form = PelanggaranForm(instance=pelanggaran, user=request.user)

    return render(request, 'pelanggaran_add.html', {
        'form': form,
        'title': 'Edit Pelanggaran',
        'pelanggaran': pelanggaran
    })


@login_required
def pelanggaran_delete(request, pk):
    pelanggaran = get_object_or_404(Pelanggaran, pk=pk)
    if request.method == 'POST':
        pelanggaran.delete()
        return redirect('pelanggaran_list')

    # For a GET request, show the empty form
    form = PelanggaranForm()
    pelanggaran_options = Demerit.objects.values_list('pelanggaran', flat=True).distinct().order_by('pelanggaran')
    context = {
        'form': form,
        'pelanggaran_options': pelanggaran_options,
    }
    return render(request, 'pelanggaran_confirm_delete.html', context)

# --- HTMX Partial Views for Pelanggaran ---

def get_demerit_lingkup_options(request):
    pelanggaran = request.GET.get('pelanggaran')
    rules = Demerit.objects.filter(pelanggaran=pelanggaran)
    context = {'rules': rules}
    return render(request, 'partials/demerit_lingkup_options.html', context)







def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        print(f"Form is valid: {form.is_valid()}")  # Debug
        print(f"Form errors: {form.errors}")  # Debug
        
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            #user.groups.add(Group.objects.get(name='Student'))  # Assign to 'Student' group
            user.save()
            #login(request, user)
            
            # Now that the user is saved, you can add them to a group
            try:
                student_group = Group.objects.get(name='Student')
                user.groups.add(student_group)
            except Group.DoesNotExist:
                # Handle case where 'Student' group doesn't exist yet
                # You might want to create it or log an error
                pass


            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': True, 
                    'message': 'Registration successful!',
                    'redirect_url': '/dashboard/'
                })
            return redirect('/dashboard/')
        else:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                })
    
    form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})




    

@login_required
def dashboard(request):
    user=request.user
    status = Aktivitas.status
    angkatan_mhs = user.angkatan
    kuantitas_akt = Aktivitas.kuantitas
    kuantitas_pel = Pelanggaran.kuantitas
    is_student = request.user.groups.filter(name="Student").exists()
    if user.is_superuser or user.is_staff:
        # admin liat smuanya
        aktivitas_records = Aktivitas.objects.all().order_by('-created_at')

    elif is_student:
        # cuma bs liat yg udah di approve
        aktivitas_records = Aktivitas.objects.filter(
            Q(status="approved")
        ).order_by('-created_at')

    else:
        # fallback, if you have other groups
        aktivitas_records = Aktivitas.objects.filter(status="approved").order_by('-created_at')

    modal_poin = user.modal_poin_awal

    total_mhs = User.objects.filter(groups=1).count()

    aktivitas_count = aktivitas_records.count()
    pelanggaran_count = Pelanggaran.objects.count()


    total_aktivitas_mhs = Aktivitas.objects.filter(user=user, status="approved").count()
    total_aktivitas = Aktivitas.objects.count()
    total_poin = Aktivitas.objects.aggregate(total=Sum('aturan_merit__poin'))['total'] or 0
    total_pelanggaran_mhs = Pelanggaran.objects.filter(user=user).count() 
    total_pelanggaran = Pelanggaran.objects.count()
    total_demerit = Pelanggaran.objects.aggregate(total=Sum('aturan_demerit__poin'))['total'] or 0
    net_poin = total_poin - total_demerit
    total_pelanggaran_mhs_real = Pelanggaran.objects.filter(user=user).aggregate(total=Sum(F('aturan_demerit__poin') * F('kuantitas')))['total'] or 0
    total_pelanggaran_real = Pelanggaran.objects.aggregate(total=Sum(F('aturan_demerit__poin') * F('kuantitas')))['total'] or 0
    total_aktivitas_mhs_real = Aktivitas.objects.filter(user=user, status="approved").aggregate(total=Sum(F('aturan_merit__poin') * F('kuantitas')))['total'] or 0
    total_aktivitas_real = Aktivitas.objects.filter(status="approved").aggregate(total=Sum(F('aturan_merit__poin') * F('kuantitas')))['total'] or 0
    total_poin2 = total_aktivitas_mhs_real - total_pelanggaran_mhs_real + modal_poin # 100 sebagai modal poin awal
    total_poin_admin = total_aktivitas_real - total_pelanggaran_real + modal_poin # 100 sebagai modal poin awal
    pending_count = Aktivitas.objects.filter(status='pending').count()
    rejected_count = Aktivitas.objects.filter(user=user, status='rejected').count()

    context = {
        'aktivitas_records': aktivitas_records,
        'total_aktivitas': total_aktivitas,
        'total_poin': total_poin,
        'total_pelanggaran': total_pelanggaran,
        'total_demerit': total_demerit,
        'net_poin': net_poin,
        'total_poin2': total_poin2,
        'total_aktivitas_mhs': total_aktivitas_mhs,
        'total_pelanggaran_mhs': total_pelanggaran_mhs,
        'total_poin_admin': total_poin_admin,
        'pending_count': pending_count,
        'status': status,
        'rejected_count': rejected_count,
        'total_pelanggaran_mhs_real': total_pelanggaran_mhs_real,
        'total_pelanggaran_real': total_pelanggaran_real,
        'total_aktivitas_mhs_real': total_aktivitas_mhs_real,
        'total_aktivitas_real': total_aktivitas_real,
        'modal_poin': modal_poin,
        'total_mhs': total_mhs,
        'aktivitas_count': aktivitas_count,
        'pelanggaran_count': pelanggaran_count,
        }
    return render(request, 'dashboard.html', context)

@login_required
def rekap(request):
    """
    This view calculates the points for every user and prepares a list 
    of data for the template.
    """
    sort_type = request.GET.get('sort', 'angkatan')
    ordering_map = {
        'first_name': 'first_name',
        'prodi': 'prodi',
        'angkatan': '-angkatan'
    }
    order_field = ordering_map.get(sort_type, 'first_name')

    # all_users = User.objects.filter(groups=1).order_by('-angkatan').all() # semuanya kecuali 
    all_users = User.objects.filter(groups=1).order_by(order_field).all()
    
    # This will be the final list we send to the template.
    user_rekap_list = [] 
    user_rekap_list_by_prodi = [] 
    user_rekap_list_by_angkatan = [] 

    # Loop through each user to perform calculations.
    for u in all_users:
        # Calculate total 'Aktivitas' points for this specific user.
        aktivitas_points = Aktivitas.objects.filter(user=u, status="approved").aggregate(
            total=Sum(F('aturan_merit__poin') * F('kuantitas'), default=0)
        )['total']
        
        # Calculate total 'Pelanggaran' points for this specific user.
        pelanggaran_points = Pelanggaran.objects.filter(user=u).aggregate(
            total=Sum(F('aturan_demerit__poin') * F('kuantitas'), default=0)
        )['total']

        modal_poin = u.modal_poin_awal

        # Calculate the final total points, starting with a base of 100.
        total_points = (aktivitas_points or 0) - (pelanggaran_points or 0) + modal_poin
        
        # Append a dictionary with this user's complete data to our list.
        user_rekap_list.append({
            'user_obj': u,
            'aktivitas': aktivitas_points,
            'pelanggaran': pelanggaran_points,
            'total': total_points,
            'modal_poin': modal_poin
        })

    # The context now only needs to contain our clean, processed list.
    context = {
        'user_rekap_list': user_rekap_list,
    }
    # print(f"Sort type: {sort_type}, Order field: {order_field}")
    # print(f"All users count: {all_users.count()}")
    # print(f"First user: {all_users.first()}")   
    # return render(request, 'rekap.html', context)
    if request.headers.get('HX-Request'):
        return render(request, 'partials/rekap_table.html', context)

    return render(request, 'rekap.html', context)

@login_required
def user_rekap(request, user_id):
    # user=request.user
    aktivitas_records = Aktivitas.objects.order_by('-created_at').filter(user__id=user_id, status="approved")
    pelanggaran_records = Pelanggaran.objects.order_by('-created_at').filter(user__id=user_id)
    user_obj = get_object_or_404(User, id=user_id)
    user_akt_total = aktivitas_records.filter(status="approved").aggregate(total=Sum(F('aturan_merit__poin') * F('kuantitas')))['total'] or 0
    user_pel_total = pelanggaran_records.aggregate(total=Sum(F('aturan_demerit__poin') * F('kuantitas')))['total'] or 0
    modal_poin = user_obj.modal_poin_awal
    user_net_total = user_akt_total - user_pel_total + modal_poin  # poin modal tergantung angkatan




    context = {'aktivitas_records': aktivitas_records, 'user_obj': user_obj, 'pelanggaran_records': pelanggaran_records, 
               'user_akt_total': user_akt_total, 'user_pel_total': user_pel_total, 'user_net_total': user_net_total,
               'modal_poin': modal_poin}
    return render(request, 'rekap_details.html', context)




@login_required
def generate_pdf(request): 
    buf = io.BytesIO()

    # If user_id provided, limit to that user's records and set filename accordingly
    sort_type = request.GET.get('sort', 'angkatan')
    ordering_map = {
        'first_name': 'first_name',
        'prodi': 'prodi',
        'angkatan': '-angkatan'
    }
    order_field = ordering_map.get(sort_type, 'first_name')
    # all_users = User.objects.filter(groups=1).order_by('-angkatan').all() # semuanya kecuali admin
    all_users = User.objects.filter(groups=1).order_by(order_field).all() # semuanya kecuali admin
    filename = 'ekupoint_report_table.pdf'
    
    # This will be the final list we send to the template.
    user_rekap_list = []  

    # Loop through each user to perform calculations.
    for u in all_users:
        # Calculate total 'Aktivitas' points for this specific user.
        aktivitas_points = Aktivitas.objects.filter(user=u, status="approved").aggregate(
            total=Sum(F('aturan_merit__poin') * F('kuantitas'), default=0)
        )['total']
        
        # Calculate total 'Pelanggaran' points for this specific user.
        pelanggaran_points = Pelanggaran.objects.filter(user=u).aggregate(
            total=Sum(F('aturan_demerit__poin') * F('kuantitas'), default=0)
        )['total']

        modal_poin = u.modal_poin_awal

        # Calculate the final total points, starting with a base of 100.
        total_points = (aktivitas_points or 0) - (pelanggaran_points or 0) + modal_poin
        
        # Append a dictionary with this user's complete data to our list.
        user_rekap_list.append({
            'user_obj': u,
            'aktivitas': aktivitas_points,
            'pelanggaran': pelanggaran_points,
            'total': total_points,
            'modal_poin': modal_poin
        })

    doc = SimpleDocTemplate(buf, pagesize=(595, 842))
    flowables = []

    styles = getSampleStyleSheet()


    # styling
    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Times-Roman'
)
    
    center_style_small = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=8,
        fontName='Times-Roman'
)

    title_style = ParagraphStyle(
        'TitleStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"
        fontSize=24,                # "Really big" size
        alignment=TA_CENTER,        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    heading_style = ParagraphStyle(
        'HeadingStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"              # "Really big" size        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    times_nr = ParagraphStyle(
        'TimesNewRoman',
        fontName='Times-Bold'
    )

    kopsurat_nama_institusi = ParagraphStyle(
        'KopSuratNamaInstitusi',
        parent=styles['Normal'],
        fontSize=24,
        leading=24,
        alignment=TA_CENTER,
        fontName='Times-Roman',
        textColor="#5A0303"
    )
    available_width = doc.width

    separator = Drawing(available_width, 2)

    line = Line(
        x1=1, y1=1,
        x2=available_width, y2=1,
        strokeColor=colors.HexColor("#510000"),
        strokeWidth=1
    )

    separator.add(line)
    
    # kopsurat versi gambar
    kop_surat = os.path.join(settings.BASE_DIR, 'media/ekupoint/kopsurat.jpg')

    # logo STTE, buat rekreasi kopsurat
    logo = os.path.join(settings.BASE_DIR, 'media/ekupoint/logo-stte-jakarta-bwt-kopsurat.png')

    # setting gambar
    kopsur = Image(kop_surat)
    logo_stte = Image(logo, width=120, height=90)
    
    # kopsurat yang diambil dari dokumen2 lain; kalo mau dipake tinggal di uncomment
    # flowables.append(kopsur)

    header_text = "REKAP EKUPOINT"
    akt_text_raw = "Aktivitas Mahasiswa:"
    pel_text_raw = "Pelanggaran Mahasiswa:"
    akt_text = Paragraph(akt_text_raw, times_nr)
    pel_text = Paragraph(pel_text_raw, times_nr)
    # header_2 = f"Nama: {user_obj.get_full_name()}"
    # header_3 = f"NIM: {user_obj.nim}"
    # header_4 = f"Prodi: {user_obj.prodi}"
    # header_5 = f"Angkatan: {user_obj.angkatan}"
    header = Paragraph(header_text, title_style)
    # header_dua = Paragraph(header_2)
    # header_tiga = Paragraph(header_3)
    # header_empat = Paragraph(header_4)
    # header_lima = Paragraph(header_5)

    # data2 rekreasi kop surat
    kop_left_content = [
        logo_stte,
    ]

    kop_right_content = [
        Paragraph("SEKOLAH TINGGI TEOLOGI EKUMENE JAKARTA", kopsurat_nama_institusi),
        Spacer(1, 4),
        Paragraph("Mall Artha Gading Lantai 3, Jl. Artha Gading Sel. No. 3, Kelapa Gading, Jakarta Utara, Indonesia 14240", center_style_small),
        Paragraph("+628197577740      institusi.stte@sttekumene.ac.id      sttekumene.ac.id", center_style_small),
    ]

    kopsurat_data_1 = [
        [kop_left_content, kop_right_content],
    ]

    kopsurat_table = Table(kopsurat_data_1, colWidths=[100, 400])

    kopsurat_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFFFF"), # No grid
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Align labels (col 0) to the left
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
            ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
        ]))
    # rekreasi kop surat
    flowables.append(kopsurat_table)
    flowables.append(separator)
    # flowables.append(Spacer(1, 24))
    
    # judul ("EKUPOINT REPORT")
    flowables.append(header)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_dua)
    flowables.append(Spacer(1, 24))
    # flowables.append(header_tiga)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_empat)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_lima)
    # flowables.append(Spacer(1, 12))

    # not functional
    # title_data = [
    #         ["EKUPOINT REPORT", ""]
    #     ]
    
    # title_table = Table(title_data, colWidths=[100, 740])

    # title_table.setStyle(TableStyle([
    #         ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
    #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #         ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
    #         ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
    #         ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'), # Make labels bold
    #     ]))
    
    # table format, biar rapi

    


    # Aktivitas table
    # styles = getSampleStyleSheet()
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, leading=10, fontName='Times-Roman', splitLongWords=1, wordWrap='LTR')
    # headers_aktivitas = ["Aktivitas", "Jenis", "Lingkup", "Poin", "Kuantitas", "Keterangan", "File", "Status", "Tanggal"]
    headers_mhs = ["Nama Lengkap", "NIM", "Prodi", "Angkatan", "Merit", "Demerit", "Total"]
    total = Sum(total_points + modal_poin)
    

    data_mhs = [headers_mhs]
    for obj in user_rekap_list:
        data_row = [
            # obj.user.get_full_name() if obj.user else '',
            # str(obj.aturan_merit) if obj.aturan_merit else '',
            obj['user_obj'].get_full_name() or '',
            obj['user_obj'].nim or '',
            obj['user_obj'].prodi or '',
            obj['user_obj'].angkatan or '',
            obj['aktivitas'] or 0,
            obj['pelanggaran'] or 0,
            obj['total'] or 0
        ]
        data_mhs.append(data_row)

    table_aktivitas = Table(data_mhs, repeatRows=1)
    table_aktivitas.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, '#000000'),
        ('BACKGROUND', (0,0), (-1,0), '#eeeeee'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman')
    ]))
    flowables.append(table_aktivitas)


    sig_left_content = [
        Paragraph("Dosen Wali", center_style),
        Paragraph("Akademik", center_style),
        Spacer(1, 80),  
        Paragraph("(_________________)", center_style),
    ]

    sig_right_content = [
        Paragraph(f"Jakarta, {timezone.now().strftime('%d %B %Y')}", center_style,),
        Paragraph("Wakil Ketua Bidang Kemahasiswaan, ", center_style),
        Paragraph("Alumni, dan Kerja Sama", center_style),
        Spacer(1, 60), # 60-point gap for signature
        Paragraph("(_________________)", center_style),
    ]

    footer_data_1 = [
        [sig_left_content,'  ', sig_right_content],
    ]

    footer1_table = Table(footer_data_1)

    footer1_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
            ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
        ]))
    flowables.append(Spacer(1, 24))
    flowables.append(footer1_table)
    flowables.append(Spacer(1, 24))

    doc.build(flowables)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=filename)







def about_user(request):
    user= request.user
    angkatan_mhs = user.angkatan
    modal_poin = user.modal_poin_awal
    context = {
        'modal_poin': modal_poin,
    }
    return render(request, 'about.html', context)











def generate_user_table_pdf(request, user_id=None):
    buf = io.BytesIO()

    # If user_id provided, limit to that user's records and set filename accordingly
    if user_id:
        user_obj = get_object_or_404(User, id=user_id)
        contactdata = Aktivitas.objects.filter(user=user_obj, status="approved").select_related('user', 'aturan_merit')
        pelanggaran = Pelanggaran.objects.filter(user=user_obj).select_related('user', 'aturan_demerit')
        modal_poin = user_obj.modal_poin_awal
        filename = f'ekupoint_report_table_{user_obj.username}.pdf'
    else:
        contactdata = Aktivitas.objects.all().select_related('user', 'aturan_merit')
        pelanggaran = Pelanggaran.objects.all().select_related('user', 'aturan_demerit')
        filename = 'ekupoint_report_table.pdf'

    doc = SimpleDocTemplate(buf, pagesize=(595, 842))
    flowables = []

    styles = getSampleStyleSheet()

    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Times-Roman'
)
    
    center_style_small = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=8,
        fontName='Times-Roman'
)

    title_style = ParagraphStyle(
        'TitleStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"
        fontSize=24,                # "Really big" size
        alignment=TA_CENTER,        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    heading_style = ParagraphStyle(
        'HeadingStyle',             # A name for the style
        parent=styles['Heading3'],  # Base it on the default "Heading1"              # "Really big" size        # Center the text
        fontName='Times-Bold'   # Make sure it's bold
    )

    times_nr = ParagraphStyle(
        'TimesNewRoman',
        fontName='Times-Bold'
    )

    kopsurat_nama_institusi = ParagraphStyle(
        'KopSuratNamaInstitusi',
        parent=styles['Normal'],
        fontSize=24,
        leading=24,
        alignment=TA_CENTER,
        fontName='Times-Roman',
        textColor="#5A0303"
    )
    available_width = doc.width

    separator = Drawing(available_width, 2)

    line = Line(
        x1=1, y1=1,
        x2=available_width, y2=1,
        strokeColor=colors.HexColor("#510000"),
        strokeWidth=1
    )

    separator.add(line)
    
    # kopsurat versi gambar
    kop_surat = os.path.join(settings.BASE_DIR, 'media/ekupoint/kopsurat.jpg')

    # logo STTE, buat rekreasi kopsurat
    logo = os.path.join(settings.BASE_DIR, 'media/ekupoint/logo-stte-jakarta-bwt-kopsurat.png')

    # setting gambar
    kopsur = Image(kop_surat)
    logo_stte = Image(logo, width=120, height=90)
    
    # kopsurat yang diambil dari dokumen2 lain; kalo mau dipake tinggal di uncomment
    # flowables.append(kopsur)

    header_text = "EKUPOINT REPORT"
    akt_text_raw = "Aktivitas Mahasiswa:"
    pel_text_raw = "Pelanggaran Mahasiswa:"
    akt_text = Paragraph(akt_text_raw, times_nr)
    pel_text = Paragraph(pel_text_raw, times_nr)
    # header_2 = f"Nama: {user_obj.get_full_name()}"
    # header_3 = f"NIM: {user_obj.nim}"
    # header_4 = f"Prodi: {user_obj.prodi}"
    # header_5 = f"Angkatan: {user_obj.angkatan}"
    header = Paragraph(header_text, title_style)
    # header_dua = Paragraph(header_2)
    # header_tiga = Paragraph(header_3)
    # header_empat = Paragraph(header_4)
    # header_lima = Paragraph(header_5)

    # data2 rekreasi kop surat
    kop_left_content = [
        logo_stte,
    ]

    kop_right_content = [
        Paragraph("SEKOLAH TINGGI TEOLOGI EKUMENE JAKARTA", kopsurat_nama_institusi),
        Spacer(1, 4),
        Paragraph("Mall Artha Gading Lantai 3, Jl. Artha Gading Sel. No. 3, Kelapa Gading, Jakarta Utara, Indonesia 14240", center_style_small),
        Paragraph("+628197577740      institusi.stte@sttekumene.ac.id      sttekumene.ac.id", center_style_small),
    ]

    kopsurat_data_1 = [
        [kop_left_content, kop_right_content],
    ]

    kopsurat_table = Table(kopsurat_data_1, colWidths=[100, 400])

    kopsurat_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFFFF"), # No grid
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Align labels (col 0) to the left
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
            ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
        ]))
    # rekreasi kop surat
    flowables.append(kopsurat_table)
    flowables.append(separator)
    # flowables.append(Spacer(1, 24))
    
    # judul ("EKUPOINT REPORT")
    flowables.append(header)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_dua)
    flowables.append(Spacer(1, 24))
    # flowables.append(header_tiga)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_empat)
    # flowables.append(Spacer(1, 12))
    # flowables.append(header_lima)
    # flowables.append(Spacer(1, 12))

    # not functional
    # title_data = [
    #         ["EKUPOINT REPORT", ""]
    #     ]
    
    # title_table = Table(title_data, colWidths=[100, 740])

    # title_table.setStyle(TableStyle([
    #         ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
    #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #         ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
    #         ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
    #         ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'), # Make labels bold
    #     ]))
    
    # table format, biar rapi
    if user_id:
        header_data = [
            ['Nama: ', user_obj.get_full_name()],
            ['NIM: ', user_obj.nim],
            ['Prodi: ', user_obj.prodi],
            ['Angkatan: ', user_obj.angkatan]
        ]

    header_table = Table(header_data, colWidths=[100, 300])

    header_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'), # Make labels bold
            ('FONTNAME', (1, 0), (1, -1), 'Times-Roman')
        ]))
    
    # data2 mahasiswa
    flowables.append(header_table)
    flowables.append(Spacer(1, 24))


    # Aktivitas table
    # styles = getSampleStyleSheet()
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, leading=10, fontName='Times-Roman', splitLongWords=1, wordWrap='LTR')
    # headers_aktivitas = ["Aktivitas", "Jenis", "Lingkup", "Poin", "Kuantitas", "Keterangan", "File", "Status", "Tanggal"]
    headers_aktivitas = ["Aktivitas", "Poin", "Kuantitas", "Keterangan", "Tanggal"]
    aktivitas_total = contactdata.aggregate(
        total=Sum(F('aturan_merit__poin') * F('kuantitas'))
    )['total'] or 0
    

    pelanggaran_total = pelanggaran.aggregate(
        total=Sum(F('aturan_demerit__poin') * F('kuantitas'))
    )['total'] or 0
    data_aktivitas = [headers_aktivitas]
    for obj in contactdata:
        aturan_aktv = Paragraph(str(obj.aturan_merit) if obj.aturan_merit else '', small)
        aktivitas_aktv = Paragraph(obj.aturan_merit.aktivitas or '', small)
        jenis_aktv = Paragraph(obj.aturan_merit.jenis or '', small)
        lingkup_aktv = Paragraph(obj.aturan_merit.lingkup or '', small)
        created_at = Paragraph(obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else '', small)
        keterangan_aktv = Paragraph(obj.keterangan or '', small)
        # file_link = Paragraph(obj.file or '', small)
        file_link = Paragraph(obj.file or '', small)
        # url_with_breaks = url.replace('/', '/ ') \
        #                  .replace('?', '? ') \
        #                  .replace('&', '& ') \
        #                  .replace('_', '_ ') \
        #                  .replace('=', '= ')
        data_row = [
            # obj.user.get_full_name() if obj.user else '',
            # str(obj.aturan_merit) if obj.aturan_merit else '',
            aturan_aktv,
            # aktivitas_aktv,
            # obj.aktivitas or '',
            # jenis_aktv,
            # lingkup_aktv,
            getattr(obj, 'poin', '') or '',
            obj.kuantitas or '',
            # obj.keterangan or '',
            keterangan_aktv,
            # file_link,
            # obj.status or '',
            created_at
        ]
        data_aktivitas.append(data_row)

    table_aktivitas = Table(data_aktivitas, repeatRows=1)
    table_aktivitas.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, '#000000'),
        ('BACKGROUND', (0,0), (-1,0), '#eeeeee'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman')
    ]))
    flowables.append(akt_text)
    flowables.append(table_aktivitas)

    total_para_text = f"<b>Total Aktivitas:</b> {aktivitas_total}"
    # total_para = Paragraph(f"<b>Total Aktivitas:</b> {aktivitas_total}", styles['Normal'])
    total_para = Paragraph(total_para_text, times_nr)
    flowables.append(Spacer(1, 6))
    flowables.append(total_para)

    # Spacer between tables
    flowables.append(Spacer(1, 24))

    # Pelanggaran table
    # styles = getSampleStyleSheet()
    # small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, leading=10)
    # headers_pelanggaran = ["Pelanggaran", "Lingkup", "Poin", "Kuantitas", "Keterangan", "Tanggal"]
    headers_pelanggaran = ["Pelanggaran", "Poin", "Kuantitas", "Keterangan", "Tanggal"]
    data_pelanggaran = [headers_pelanggaran]
    for obj in pelanggaran:
        aturan_para = Paragraph(str(obj.aturan_demerit) if obj.aturan_demerit else '', small)
        pelanggaran_para = Paragraph(obj.aturan_demerit.pelanggaran or '', small)
        keterangan_para = Paragraph(obj.keterangan or '', small)
        lingkup_para = Paragraph(obj.aturan_demerit.lingkup or '', small)
        kuantitas_para = Paragraph(str(obj.kuantitas) or '', small)
        created_at_para = Paragraph(obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else '', small)
        data_row = [
            # obj.user.get_full_name() if obj.user else '',
            aturan_para,
            # pelanggaran_para,
            # obj.aturan_demerit.lingkup or '',
            getattr(obj, 'poin', '') or '',
            kuantitas_para,
            keterangan_para,
            created_at_para,
        ]
        data_pelanggaran.append(data_row)

    colWidths = [80, 180, 200, 60, 40, 40, 160, 80, 50, 80]

    table_pelanggaran = Table(data_pelanggaran, repeatRows=1)
    table_pelanggaran.setStyle(TableStyle([
        # ('BOX', (0, 0), (-1, 0), 1.1, '#000000'),
        ('GRID', (0,0), (-1,-1), 0.5, '#000000'),
        ('BACKGROUND', (0,0), (-1,0), '#eeeeee'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman')
    ]))
    flowables.append(pel_text)
    flowables.append(table_pelanggaran)

        # add Pelanggaran total
    total_pel_para_text = f"<b>Total Pelanggaran:</b> {pelanggaran_total}"
    # total_pel_para = Paragraph(f"<b>Total Pelanggaran:</b> {pelanggaran_total}", styles['Normal'])
    total_pel_para = Paragraph(total_pel_para_text, times_nr)
    flowables.append(Spacer(1, 6))
    flowables.append(total_pel_para)

    # grand total
    grand_total = aktivitas_total - pelanggaran_total + modal_poin
    grand_para_text = f"<b>Total (+ Modal Poin {modal_poin}):</b> {grand_total}"
    # grand_para = Paragraph(f"<b>Total (+ Modal Poin {modal_poin}):</b> {grand_total}", styles['Heading3'])
    grand_para = Paragraph(grand_para_text, times_nr)
    flowables.append(Spacer(1, 12))
    flowables.append(grand_para)

    sig_left_content = [
        Paragraph("Dosen Wali", center_style),
        Paragraph("Akademik", center_style),
        Spacer(1, 80),  
        Paragraph("(_________________)", center_style),
    ]

    sig_right_content = [
        Paragraph(f"Jakarta, {timezone.now().strftime('%d %B %Y')}", center_style,),
        Paragraph("Wakil Ketua Bidang Kemahasiswaan, ", center_style),
        Paragraph("Alumni, dan Kerja Sama", center_style),
        Spacer(1, 60), # 60-point gap for signature
        Paragraph("(_________________)", center_style),
    ]

    footer_data_1 = [
        [sig_left_content,'  ', sig_right_content],
    ]

    footer1_table = Table(footer_data_1)

    footer1_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, "#FFFFFF"), # No grid
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Align labels (col 0) to the left
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Align values (col 1) to the left
            ('FONTNAME', (0, 0), (0, -1), 'Times-Roman') # Make labels bold
        ]))
    flowables.append(Spacer(1, 24))
    flowables.append(footer1_table)
    flowables.append(Spacer(1, 24))

    doc.build(flowables)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=filename)



