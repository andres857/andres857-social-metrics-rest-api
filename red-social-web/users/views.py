from auth_app.models import CustomUser as User
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

from rest_framework import status, authentication, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView

from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from .serializers import UserSerializer, CreateUserSerializer, UpdateUserSerializer

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError


    
    
    
class ListUsers(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    #authentication_classes = [authentication.TokenAuthentication]
    #permission_classes = [permissions.IsAdminUser]

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    

class CreateUser(APIView):
    #permission_classes = [IsAdminUser]  # Solo los administradores pueden crear usuarios

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    "message": "Usuario creado exitosamente",
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({
                    "message": "El usuario ya existe",
                    "error": "Un usuario con este nombre de usuario o correo electrónico ya está registrado"
                }, status=status.HTTP_409_CONFLICT)
            except Exception as e:
                return Response({
                    "message": "Error interno al crear usuario",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({
            "message": "Error en los datos proporcionados",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        

class DeleteUser(APIView):
    #permission_classes = [IsAdminUser]

    def delete(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Evitar que un admin se elimine a sí mismo
            if user == request.user:
                raise PermissionDenied("No puedes eliminarte a ti mismo")

            name = user.first_name + ' ' + user.last_name
            user.delete()
            return Response({
                "message": f"Usuario '{name}' eliminado exitosamente"
            }, status=status.HTTP_200_OK)
        
        except PermissionDenied as e:
            return Response({
                "message": "Operación no permitida",
                "error": str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        
        except Exception as e:
            return Response({
                "message": "Error al eliminar usuario",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

class UpdateUser(APIView):
    #permission_classes = [IsAdminUser]

    def put(self, request, user_id):
        try:
            user = get_object_or_404(User, id=user_id)
            serializer = UpdateUserSerializer(user, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "message": "Usuario actualizado exitosamente",
                    "user": serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "Error en los datos proporcionados",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError as e:
            return Response({
                "message": "Error de integridad",
                "error": "El username o email ya está en uso"
            }, status=status.HTTP_409_CONFLICT)
        
        except Exception as e:
            return Response({
                "message": "Error al actualizar usuario",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, user_id):
        return self.put(request, user_id)