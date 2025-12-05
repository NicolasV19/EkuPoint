from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', CustomLoginView.as_view(), name='login'),

    # Aktivitas URLs
    path('aktivitas/', views.aktivitas_list, name='aktivitas_list'),
    path('aktivitas/add/', views.aktivitas_add, name='aktivitas_add'), # New URL
    path('aktivitas/<int:pk>/edit/', views.aktivitas_edit, name='aktivitas_edit'), # Edit URL
    path('aktivitas/<int:pk>/delete/', views.aktivitas_delete, name='aktivitas_delete'), # Delete URL
    
    # Pelanggaran URLs
    path('pelanggaran/', views.pelanggaran_list, name='pelanggaran_list'),
    path('pelanggaran/add/', views.pelanggaran_add, name='pelanggaran_add'), # New URL
    path('pelanggaran/<int:pk>/edit/', views.pelanggaran_edit, name='pelanggaran_edit'), # Edit URL
    path('pelanggaran/<int:pk>/delete/', views.pelanggaran_delete, name='pelanggaran_delete'), # Delete URL

    # HTMX partial URLs (no changes here)
    path('htmx/get-aktivitas-options/', views.get_aktivitas_options, name='get_aktivitas_options'),
    path('htmx/get-jenis-options/', views.get_jenis_options, name='get_jenis_options'),
    path('htmx/get-lingkup-options/', views.get_lingkup_options, name='get_lingkup_options'),
    path('htmx/get-demerit-lingkup-options/', views.get_demerit_lingkup_options, name='get_demerit_lingkup_options'),

    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('rekap/', views.rekap, name='rekap'),
    path('rekap/<int:user_id>/', views.user_rekap, name='user_rekap'),
    path('gen_pdf/', views.generate_pdf, name='generate_pdf'),
    path('generate_table_pdf/<int:user_id>/', views.generate_user_table_pdf, name='generate_user_table_pdf'),
    path('about_user/', views.about_user, name='about_user')
]
