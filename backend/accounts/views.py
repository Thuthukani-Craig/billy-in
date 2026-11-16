from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant, TenantMembership


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(memberships__user=self.request.user, memberships__is_active=True).distinct()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(username=serializer.validated_data['username'], password=serializer.validated_data['password'])
        if user is None:
            return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        memberships = list(user.tenant_memberships.filter(is_active=True).select_related('tenant').values('tenant_id', 'tenant__name', 'role'))
        return Response({
            'detail': 'Login successful.',
            'user': {'id': user.id, 'username': user.username, 'email': user.email, 'is_staff': user.is_staff},
            'tenants': memberships,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Logout successful.'})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = list(request.user.tenant_memberships.filter(is_active=True).select_related('tenant').values('tenant_id', 'tenant__name', 'role'))
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_staff': request.user.is_staff,
            'tenants': memberships,
        })


class FounderRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)


class FounderRegistrationView(APIView):
    permission_classes = []

    def post(self, request):
        if User.objects.exists():
            if not request.user.is_authenticated:
                return Response({'detail': 'Registration is restricted to the founder during local testing.'}, status=status.HTTP_403_FORBIDDEN)
            if not request.user.is_superuser:
                return Response({'detail': 'Only the platform owner may create additional users.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = FounderRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        if User.objects.filter(username=username).exists():
            return Response({'detail': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password, is_staff=True)
        tenant = Tenant.objects.create(name='Founder Tenant', slug='founder-tenant', is_platform_tenant=True)
        TenantMembership.objects.create(user=user, tenant=tenant, role=TenantMembership.ROLE_OWNER)
        return Response({'detail': 'Platform owner created.', 'user': {'id': user.id, 'username': user.username}}, status=status.HTTP_201_CREATED)
