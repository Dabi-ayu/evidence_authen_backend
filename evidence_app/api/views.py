from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Evidence
from ..utils.ai_models import check_tampering
from ..utils.metadata import verify_metadata

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

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from evidence_app.models import Evidence
from evidence_app.utils.blockchain import generate_ots

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
       

        evidence.is_authentic = (label == 'Real')
        evidence.confidence = float(confidence)
        evidence.metadata_status = metadata['status']
        
        evidence.save()

        hash_value = generate_ots(img_path)
        evidence.blockchain_hash = hash_value
        evidence.save()

        results = {
            'id': evidence.id,
            'image_url': evidence.image.url,
            'is_authentic': evidence.is_authentic,
            'confidence': evidence.confidence,
            'metadata_status': metadata['status'],
            'metadata_details': metadata.get('details', {}),
            'blockchainHash': hash_value,
           
        }
        return Response(results, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def verify_txid(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            txid = body.get('txid')

            # Match this with actual file path
            ots_path = f"media/ots_files/{txid}.ots"  # Update this path as needed

            result = verify_ots(ots_path)

            if result['valid']:
                return JsonResponse({'status': 'valid', 'data': result})
            else:
                return JsonResponse({'status': 'invalid', 'message': result.get('message', 'Verification failed')})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})


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

@api_view(['POST'])
def upload_image(request):
    image = request.FILES.get('image')
    title = request.data.get('title', 'Untitled')

    if not image:
        return Response({'status': 'error', 'message': 'No image uploaded'}, status=400)

    evidence = Evidence.objects.create(title=title, image=image)

    return Response({
        'status': 'complete',
        'message': 'Image uploaded successfully',
        'blockchainHash': evidence.blockchain_hash,
        'imageUrl': evidence.image.url
    })
