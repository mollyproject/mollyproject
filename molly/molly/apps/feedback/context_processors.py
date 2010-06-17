def full_path(request):
    return {
        'full_path': request.get_full_path(),
    }