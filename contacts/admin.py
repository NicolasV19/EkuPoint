from django.contrib import admin
from contacts.models import User, Angkatan, Aktivitas, Pelanggaran, Merit, Demerit, Prodi


class AngkatanAdmin(admin.ModelAdmin):
    list_display = ('angkatan', 'modal_poin')
    # list_filter = ('angkatan', 'modal_poin')
    search_fields = ('angkatan', 'modal_poin')

class ProdiAdmin(admin.ModelAdmin):
    list_display = ('prodi', 'strata')
    list_filter = ('prodi', 'strata')
    search_fields = ('prodi', 'strata')

class AktivitasAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'aturan_merit__bidang', 'aturan_merit__aktivitas', 'aturan_merit__jenis', 'aturan_merit__lingkup', 'aturan_merit__poin', 'created_at')
    list_filter = ('user', 'aturan_merit')
    search_fields = ('user__username', 'aturan_merit__bidang', 'aturan_merit__aktivitas')
    ordering = ('-created_at',)

class PelanggaranAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'aturan_demerit__pelanggaran', 'aturan_demerit__lingkup', 'aturan_demerit__poin', 'created_at')
    list_filter = ('user', 'aturan_demerit')
    search_fields = ('user__username', 'aturan_demerit__pelanggaran', 'aturan_demerit__lingkup')
    ordering = ('-created_at',)

class MeritAdmin(admin.ModelAdmin):
    list_display = ('bidang', 'aktivitas', 'jenis', 'lingkup', 'poin')
    list_filter = ('bidang', 'jenis', 'lingkup')
    search_fields = ('bidang', 'aktivitas', 'jenis', 'lingkup')

class DemeritAdmin(admin.ModelAdmin):
    list_display = ('pelanggaran', 'lingkup', 'poin')
    list_filter = ('pelanggaran','lingkup')
    search_fields = ('bidang', 'pelanggaran', 'lingkup')

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'date_joined')
    list_filter = ('username', 'first_name', 'last_name', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'date_joined')


    
# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Angkatan, AngkatanAdmin)
admin.site.register(Aktivitas, AktivitasAdmin)
admin.site.register(Pelanggaran, PelanggaranAdmin)
admin.site.register(Merit, MeritAdmin)
admin.site.register(Demerit, DemeritAdmin)
admin.site.register(Prodi, ProdiAdmin)