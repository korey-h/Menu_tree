from django.shortcuts import render


def start_view(request, *args, **kwargs):
    return render(request, 'base.html', )
