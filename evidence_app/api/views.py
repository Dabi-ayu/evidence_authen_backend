from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Evidence
from ..utils.ai_models import check_tampering
from ..utils.metadata import verify_metadata
from ..utils.blockchain import log_verification
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class VerifyEvidence(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({'detail': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        evidence = Evidence(image=image_file)
        evidence.save()

        img_path = evidence.image.path
        label, confidence = check_tampering(img_path)
        metadata = verify_metadata(img_path)
        blockchain_hash = log_verification(img_path)

        evidence.is_authentic = (label == 'Real')
        evidence.confidence = float(confidence)
        evidence.metadata_status = metadata['status']
        evidence.blockchain_hash = blockchain_hash
        evidence.save()

        results = {
            'id': evidence.id,
            'image_url': evidence.image.url,
            'is_authentic': evidence.is_authentic,
            'confidence': evidence.confidence,
            'metadata_status': metadata['status'],
            'metadata_details': metadata.get('details', {}),
            'blockchain_hash': blockchain_hash,
        }
        return Response(results, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def verify_txid(request):
    try:
        body = request.data
        txid = body.get("txid")

        ledger_path = os.path.join(os.path.dirname(__file__), '../utils/blockchain_ledger.json')
        if not os.path.exists(ledger_path):
            return JsonResponse({"status": "error", "message": "Ledger file not found"}, status=404)

        with open(ledger_path, 'r') as f:
            ledger = json.load(f)

        for entry in ledger:
            if entry["txid"] == txid:
                return JsonResponse({
                    "status": "valid",
                    "data": entry
                })

        return JsonResponse({"status": "invalid", "message": "TXID not found in ledger"}, status=404)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
def register_user(request):
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
def login_user(request):
    try:
        data = request.data
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'username': user.username,
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def logout_user(request):
    try:
        # Since JWT is stateless, logout is mostly frontend deleting token,
        # but if you use token blacklisting you can blacklist here.
        # For now, just return success.
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        try:
            data = request.data
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')

            if not username or not email or not password:
                return Response({"message": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(username=username).exists():
                return Response({"message": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email).exists():
                return Response({"message": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password)
            )
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)