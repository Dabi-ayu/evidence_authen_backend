from django.urls import path
from .views import (
    VerifyEvidence,
    verify_txid,
    register_user,
    login_user,
    logout_user,
    upload_image,         # ✅ Include if you use this endpoint
    RegisterView          # ✅ Include if you're using class-based registration view
)

app_name = 'evidence_api'

urlpatterns = [
    # Core Evidence API
    path('verify/', VerifyEvidence.as_view(), name='verify_evidence'),
    path('verify-txid/', verify_txid, name='verify_txid'),

    # Image upload (optional but useful)
    path('upload/', upload_image, name='upload_image'),

    # Authentication (function-based)
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),

    # OR Class-based register view (if needed)
    path('register-view/', RegisterView.as_view(), name='register_view'),
]
