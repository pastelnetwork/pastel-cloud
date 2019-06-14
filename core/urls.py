from django.conf.urls import url
from django.urls import include

from core.api.v1.core import UserProfileView, PastelProfileView
from core.api.v1.router import router

urlpatterns = [
    url(r'^user_profile/$', UserProfileView.as_view()),
    url(r'^pastel_profile/$', PastelProfileView.as_view()),
    url(r'', include(router.urls)),
]
