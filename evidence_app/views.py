from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework import status  
from ..models import Evidence 
from ..utils.ai_models import check_tampering  
from ..utils.metadata import verify_metadata  
from ..utils.blockchain import log_verification  # <-- updated to OpenTimestamps version
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import os
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class VerifyEvidence(APIView): 
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self, request):  
        image_file = request.FILES['image']  
        evidence = Evidence(image=image_file)  
        evidence.save()  

        img_path = evidence.image.path  
        label, confidence = check_tampering(img_path)  
        metadata = verify_metadata(img_path)
        blockchain_data = log_verification(img_path)  # <- returns dict now

        ots_file_path = blockchain_data.get("ots_file")
        if ots_file_path:
            relative_ots_path = os.path.relpath(ots_file_path, settings.MEDIA_ROOT)
            ots_url = settings.MEDIA_URL + relative_ots_path.replace('\\', '/')
        else:
            ots_url = None

        evidence.is_authentic = (label == 'Real')  
        evidence.confidence = float(confidence)  
        evidence.metadata_status = metadata['status']  
        evidence.blockchain_hash = blockchain_data.get("hash")
        evidence.ots_file = relative_ots_path if ots_file_path else None
        evidence.save()  

        results = {  
            'id': evidence.id,  
            'image_url': evidence.image.url,  
            'is_authentic': evidence.is_authentic,  
            'confidence': evidence.confidence,  
            'metadata_status': metadata['status'],  
            'metadata_details': metadata['details'],
            'blockchain_hash': blockchain_data.get("hash"),
            'ots_url': ots_url
        }  
        return Response(results, status=status.HTTP_200_OK)


@csrf_exempt
def verify_txid(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
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
    else:
        return JsonResponse({"status": "error", "message": "POST request required"}, status=400)
