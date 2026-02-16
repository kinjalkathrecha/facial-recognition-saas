from django.utils import timezone
import datetime
from django.shortcuts import render
from django.contrib.auth import get_user_model,authenticate
from django.conf import settings
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK,HTTP_400_BAD_REQUEST
from .image_detection import detect_faces
from .serializers import (
    ChangeEmailSerializer,
    ChangePasswordSerializer,
    FileSerializer,
    TokenSerializer,
    SubscribeSerializer
    )
from .permissions import IsMember
from .models import TrackedRequest,Payment
import stripe
User = get_user_model()
STRIPE_PLAN_ID = settings.STRIPE_PRICE_ID
stripe.api_key=settings.STRIPE_SECRET_KEY
def get_user_from_token(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION")
    if not auth_header:
        return None
    try:
        parts = auth_header.split(' ')
        if len(parts) != 2:
            return None
        key = parts[1]
        token = Token.objects.get(key=key)
        return User.objects.get(id=token.user_id)
    except (Token.DoesNotExist, User.DoesNotExist):
        return None

class FileUploadView(APIView):
    permission_classes=(AllowAny,)
    def post(self,request,*args,**kwargs):

        content_length=request.META.get('CONTENT_LENGTH') #bytes
        if int(content_length) > 5000000:
            return Response({"message":"Image size is greater that 5MB"},status=HTTP_400_BAD_REQUEST)


        recognition = {"safely_executed": False, "error_value": "Incorrect data received"}
        file_serializer = FileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_serializer.save()
            image_path = file_serializer.data.get('file')
            recognition = detect_faces(image_path)
            return Response(recognition, status=HTTP_200_OK)
        return Response(recognition, status=HTTP_400_BAD_REQUEST)

class UserEmailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self,request,*args,**kwargs):
        user=get_user_from_token(request)
        obj={'email':user.email}
        return Response(obj)    

class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        email_serializer = ChangeEmailSerializer(data=request.data)
        if email_serializer.is_valid():
            print(email_serializer.data)
            email = email_serializer.data.get('email')
            confirm_email = email_serializer.data.get('confirm_email')
            if email == confirm_email:
                user.email = email
                user.save()
                return Response({"email": email}, status=HTTP_200_OK)
            return Response({"message": "The emails did not match"}, status=HTTP_400_BAD_REQUEST)
        return Response({"message": "Did not receive the correct data"}, status=HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        password_serializer = ChangePasswordSerializer(data=request.data)
        if password_serializer.is_valid():
            password = password_serializer.data.get('password')
            confirm_password = password_serializer.data.get('confirm_password')
            current_password = password_serializer.data.get('current_password')
            auth_user = authenticate(
                username=user.username,
                password=current_password
            )
            if auth_user is not None:
                if password == confirm_password:
                    auth_user.set_password(password)
                    auth_user.save()
                    return Response(status=HTTP_200_OK)
                else:
                    return Response({"message": "The passwords did not match"}, status=HTTP_400_BAD_REQUEST)
            return Response({"message": "Incorrect user details"}, status=HTTP_400_BAD_REQUEST)
        return Response({"message": "Did not receive the correct data"}, status=HTTP_400_BAD_REQUEST)
    
class UserDetailsView(APIView):
        permission_classes = (IsAuthenticated, )

        def get(self,request,*args,**kwargs):
            user = get_user_from_token(request)
            membership = user.membership
            today = datetime.datetime.now()
            month_start = datetime.date(today.year,today.month,1)
            tracked_request_count = TrackedRequest.objects \
                .filter(user=user,timestamp__gte=month_start) \
                .count()
            obj = {
                'membershipType' :  membership.get_type_display(),
                'free_trial_end_date': membership.end_date,
                'api_request_count' : tracked_request_count
            }
            return Response(obj)
        
class SubscribeView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        membership = user.membership

        try:
            # Handle Customer retrieval/creation
            try:
                if user.stripe_customer_id:
                    customer = stripe.Customer.retrieve(user.stripe_customer_id)
                else:
                    raise stripe.error.InvalidRequestError("No customer ID", None)
            except stripe.error.InvalidRequestError as e:
                if "No such customer" in str(e) or "No customer ID" in str(e):
                    customer = stripe.Customer.create(email=user.email)
                    user.stripe_customer_id = customer.id
                    user.save()
                else:
                    raise e
            
            serializer = SubscribeSerializer(data=request.data)
            
            if serializer.is_valid():
                stripe_token = serializer.data.get('stripeToken')

                # Attach payment source
                stripe.Customer.modify(
                    customer.id,
                    source=stripe_token
                )

                if not STRIPE_PLAN_ID:
                    return Response({'message': "Configuration Error: STRIPE_PRICE_ID is missing."}, status=HTTP_400_BAD_REQUEST)

                # Create subscription
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{"price": STRIPE_PLAN_ID}]
                )
                
                # Update membership with timezone-aware datetimes
                membership.stripe_subscription_id = subscription.id
                membership.type = 'M'
                membership.start_date = timezone.now()
                
                # Handle end_date safely from subscription
                period_end_timestamp = subscription.get('current_period_end')
                if period_end_timestamp:
                    membership.end_date = timezone.make_aware(datetime.datetime.fromtimestamp(period_end_timestamp))
                else:
                    membership.end_date = timezone.now() + datetime.timedelta(days=30)
                
                membership.save()
                
                # Update user status
                user.is_member = True
                user.on_free_trial = False
                user.save()

                # Create payment record
                payment = Payment()
                # Safely get amount from subscription items
                try:
                    price_data = subscription['items']['data'][0]['price']
                    payment.amount = price_data['unit_amount'] / 100
                except (KeyError, IndexError):
                    payment.amount = 0 # Fallback
                
                payment.user = user
                payment.timestamp = timezone.now()
                payment.save()

                return Response({'message': "success"}, status=HTTP_200_OK)

            else:
                return Response({'message': "Incorrect data received", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST)

        except stripe.error.CardError as e:
            print(f"Stripe Card Error: {str(e)}")
            return Response({'message': f"Your card has been declined: {str(e)}"}, status=HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
            print(f"Stripe API Error: {str(e)}")
            return Response({'message': f"Stripe Error: {str(e)}"}, status=HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Unhandled Exception: {str(e)}")
            return Response({"message": f"Unexpected error: {str(e)}"}, status=HTTP_400_BAD_REQUEST)


    
class ImageRecognitionView(APIView):
    permission_classes=(IsMember,)

    def post(self,request,*args,**kwargs):
        user = request.user
        file_serializer =FileSerializer(data=request.data)

        # keep track of the requests a user makes
        tracked_request = TrackedRequest(user=user)
        tracked_request.endpoint = '/api/image-recognition/'
        tracked_request.save()

        # limit the content length to 5MB
        content_length=request.META.get('CONTENT_LENGTH') #bytes
        if int(content_length) > 5000000:
            return Response({"message":"Image size is greater that 5MB"},status=HTTP_400_BAD_REQUEST)

        if file_serializer.is_valid():
            file_serializer.save()
            image_path = file_serializer.data.get('file')
            recognition = detect_faces(image_path)
            return Response(recognition, status=HTTP_200_OK)
        return Response({"message": "Received incorrect data"}, status=HTTP_400_BAD_REQUEST)
    

class APIKeyView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user = get_user_from_token(request)
        token_qs = Token.objects.filter(user=user)
        if token_qs.exists():
            token_serializer = TokenSerializer(token_qs, many=True)
            try:
                return Response(token_serializer.data, status=HTTP_200_OK)
            except:
                return Response({"message": "Did not receive correct data"}, status=HTTP_400_BAD_REQUEST)
        return Response({"message": "User does not exist"}, status=HTTP_400_BAD_REQUEST)