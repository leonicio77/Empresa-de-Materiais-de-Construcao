from .permissoes import areas_do_usuario


def permissoes(request):
    return {"areas": areas_do_usuario(request.user)}