from django.urls import path
from .views import VerifyEvidence, verify_txid, register_user, login_user, logout_user

app_name = 'evidence_api'

urlpatterns = [
    path('verify/', VerifyEvidence.as_view(), name='verify_evidence'),
    path('verify-txid/', verify_txid, name='verify_txid'),

    # Authentication endpoints
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
]
