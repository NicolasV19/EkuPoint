def user_groups(request):
    if request.user.is_authenticated:
        return {
            'is_student': request.user.groups.filter(name='Student').exists(),
            'is_admin': request.user.is_superuser,
            'is_staff': request.user.is_staff,
            'user_groups': list(request.user.groups.values_list('name', flat=True))
        }
    return {}