from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from .views import (
    VerifyEvidence,

    register_user,
    login_user,
    logout_user,
           # ✅ Include if you use this endpoint
    RegisterView          # ✅ Include if you're using class-based registration view
)

app_name = 'evidence_api'

urlpatterns = [
    # Core Evidence API
    path('verify/', VerifyEvidence.as_view(), name='verify_evidence'),
   
     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
  

    # Authentication (function-based)
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),

    # OR Class-based register view (if needed)
    path('register-view/', RegisterView.as_view(), name='register_view'),
]
