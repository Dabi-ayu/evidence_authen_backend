from django.urls import path  
from .views import VerifyEvidence  

urlpatterns = [  
    path('verify/', VerifyEvidence.as_view(), name='verify_evidence'),  
]  