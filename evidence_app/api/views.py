from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, FileResponse, Http404

from ..models import Evidence
from ..utils.ai_models import check_tampering
from ..utils.metadata import verify_metadata
from ..utils.imagehash import generate_sha256_hash

# Assuming this exists

import json
import os


class VerifyEvidence(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            image_file = request.FILES.get('image')
            if not image_file:
                return Response({'detail': 'No image provided'}, status=400)

            evidence = Evidence(image=image_file)
            evidence.save()

            img_path = evidence.image.path

            # Log path to confirm image is saved
            print("[DEBUG] Saved image path:", img_path)

            # AI + Metadata
            label, confidence = check_tampering(img_path)
            print("[DEBUG] AI Label:", label, "| Confidence:", confidence)

            metadata = verify_metadata(img_path)
            print("[DEBUG] Metadata:", metadata)

            hash_value = generate_sha256_hash(img_path)
            if not hash_value:
                return Response({'error': 'Hashing failed'}, status=500)

            # Save Results
            evidence.is_authentic = (label == 'Real')
            evidence.confidence = float(confidence)
            evidence.metadata_status = metadata['status']
            evidence.image_hash = hash_value
            evidence.save()

            results = {
                'id': evidence.id,
                'image_url': evidence.image.url,
                'is_authentic': evidence.is_authentic,
                'confidence': evidence.confidence,
                'metadata_status': metadata['status'],
                'metadata_details': metadata.get('details', {}),
                'image_hash': hash_value,
            }
            print("[DEBUG] Response payload:", results)
            return Response(results, status=200)

        except Exception as e:
            import traceback
            print("❌ ERROR in /api/verify:")
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)


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


