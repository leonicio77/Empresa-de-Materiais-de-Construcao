from .permissoes import areas_do_usuario


def permissoes(request):
    rota = getattr(request, "resolver_match", None)
    nome = (rota.url_name or "") if rota else ""
    return {
        "areas": areas_do_usuario(request.user),
        "secao": nome.split("_")[0],
    }