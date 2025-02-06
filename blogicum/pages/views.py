from django.shortcuts import render
from django.views.generic import TemplateView


class RulesPage(TemplateView):
    template_name = 'pages/rules.html'


class AboutPage(TemplateView):
    template_name = 'pages/about.html'


def page_not_found(request, exception):
    template = 'pages/404.html'
    return render(request, template, status=404)


def server_error(request):
    template = 'pages/500.html'
    return render(request, template, status=500)


def csrf_failure(request, reason=''):
    return render(request, 'pages/403csrf.html', status=403)
