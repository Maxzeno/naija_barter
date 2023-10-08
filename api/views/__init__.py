from api.views.auth import *
from api.views.views import *

from django.urls import reverse_lazy

from django.views.generic.base import RedirectView


class MyRedirectView(RedirectView):
    url = reverse_lazy('swagger-ui')
    permanent = True
