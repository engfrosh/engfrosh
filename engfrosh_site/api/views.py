from rest_framework import permissions, authentication, status
from rest_framework.views import APIView
from .serializers import VerificationPhotoSerializer
from rest_framework.response import Response
from common_models.models import VerificationPhoto


class VerificationPhotoAPI(APIView):
    authentication_classes = {authentication.SessionAuthentication, authentication.BasicAuthentication}
    permission_classes = {permissions.IsAuthenticated}

    def post(self, request, format=None):
        if not request.user.has_perm('common_models.photo_api'):
            return Response("{\"Error\": \"Forbidden\"}", status=status.HTTP_403_FORBIDDEN)
        photo = VerificationPhoto()
        serializer = VerificationPhotoSerializer(photo, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response("{\"id\": " + str(photo.id) + "}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
