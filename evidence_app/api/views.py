from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from ..models import Evidence 
from ..utils.ai_models import check_tampering  
from .utils.metadata import verify_metadata  
from .utils.blockchain import log_verification  

class VerifyEvidence(APIView):  
    def post(self, request):  
        # Get uploaded image from React  
        image_file = request.FILES['image']  
        
        # Save to database  
        evidence = Evidence(image=image_file)  
        evidence.save()  
        
        # Run verification  
        img_path = evidence.image.path  
        label, confidence = check_tampering(img_path)  
        metadata_status = verify_metadata(img_path)  
        blockchain_hash = log_verification(img_path)  
        
        # Update evidence record  
        evidence.is_authentic = (label == 'Real')  
        evidence.confidence = float(confidence)  
        evidence.metadata_status = metadata_status  
        evidence.blockchain_hash = blockchain_hash  
        evidence.save()  
        
        # Prepare results for React  
        results = {  
            'id': evidence.id,  
            'image_url': evidence.image.url,  
            'is_authentic': evidence.is_authentic,  
            'confidence': evidence.confidence,  
            'metadata_status': evidence.metadata_status,  
            'blockchain_hash': evidence.blockchain_hash,  
        }  
        return Response(results, status=status.HTTP_200_OK)  