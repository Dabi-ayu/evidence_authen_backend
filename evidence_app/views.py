from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Evidence
from .utils.ai_models import check_tampering
from .utils.metadata import verify_metadata
from .utils.blockchain import log_verification
import os

class VerifyEvidence(APIView):
    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get uploaded image
            image_file = request.FILES['image']
            
            # Save to database
            evidence = Evidence(image=image_file)
            evidence.save()
            
            # Get absolute path
            img_path = evidence.image.path
            
            # Run verification
            label, confidence = check_tampering(img_path)
            metadata_status = verify_metadata(img_path)
            blockchain_hash = log_verification(img_path)
            
            # Update evidence record
            evidence.is_authentic = (label == 'Real')
            evidence.confidence = confidence
            evidence.metadata_status = metadata_status
            evidence.blockchain_hash = blockchain_hash
            evidence.save()
            
            # Prepare results
            results = {
                'id': evidence.id,
                'image_url': evidence.image.url,
                'is_authentic': evidence.is_authentic,
                'confidence': evidence.confidence,
                'metadata_status': metadata_status,
                'blockchain_hash': blockchain_hash,
            }
            return Response(results, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)