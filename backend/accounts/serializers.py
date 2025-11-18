from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only= True)
    confirm_password = serializers.CharField(write_only=True)

    email = serializers.EmailField(
        required= True,
        validators= [UniqueValidator(queryset= User.objects.all())]
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirm_password"]
        extra_kwargs = {
            "password ": {"write_only":True},
            "email": {"requried":True},
        }

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password" :"Passwords don't match"})
            validate_password(data["password"])
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        return user

class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","email"]
        read_only_fields = ["id","username","email"]

class UserUpdateSerializer(serializers.ModelSerializer):
   class Meta:
        model = User
        fields = ["id","username","email",]
        read_only_fields = ["id",] 

class LoginSerializer(serializers.Serializer):
    
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type':'password'})

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError("Must include 'username' and 'password'.")
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_new_password(self, value):
        
        try:
            validate_password(value, user=self.context.get('request').user if self.context.get('request') else None)
        except Exception as e:
    
            raise serializers.ValidationError(list(getattr(e, 'messages', [str(e)])))
        return value

    def validate(self, data):
        user = self.context.get('request').user
        if not user.check_password(data.get('old_password')):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        return data

    def save(self, **kwargs):
        user = self.context.get('request').user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user



