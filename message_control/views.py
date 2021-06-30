from rest_framework.viewsets import ModelViewSet
from .serializers import GenericFileUpload, GenericFileUploadSerializer

class GenericFiledUploadView(ModelViewSet):
    queryset = GenericFileUpload.objects.all()
    serializer_class = GenericFileUploadSerializer