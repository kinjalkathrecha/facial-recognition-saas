import stripe
from stripe import StripeClient
from django.utils import timezone
import datetime
import math
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.shortcuts import render
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from .image_detection import detect_faces
from .models import TrackedRequest, Payment
from .permissions import IsMember
from .serializers import (
    ChangeEmailSerializer,
    ChangePasswordSerializer,
    FileSerializer,
    TokenSerializer,
    SubscribeSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY
client = StripeClient(settings.STRIPE_SECRET_KEY)
User = get_user_model()


class FileUploadView(APIView):
    permission_classes = (AllowAny, )
    throttle_scope = 'demo'

    def post(self, request, *args, **kwargs):

        content_length = request.META.get('CONTENT_LENGTH')  # bytes
        if int(content_length) > 5000000:
            return Response({"message": "Image size is greater than 5MB"}, status=HTTP_400_BAD_REQUEST)

        file_serializer = FileSerializer(data=request.data)
        if file_serializer.is_valid():
            file_obj = file_serializer.save()
            image_path = file_obj.file.path
            recognition = detect_faces(image_path)

            usage_record_id = None
            if request.user.is_authenticated:
                # Add Stripe usage reporting for members
                if request.user.is_member and not request.user.on_free_trial:
                    try:
                        membership = request.user.membership
                        try:
                            # Use Meter Events API for new billing system
                            event = client.billing.meter_events.create(
                                params={
                                    "event_name": settings.STRIPE_METER_EVENT_NAME,
                                    "payload": {
                                        "stripe_customer_id": request.user.stripe_customer_id,
                                        "value": "1"
                                    }
                                }
                            )
                            print(f"Meter event recorded via Client: {event.identifier}")
                        except stripe.error.StripeError as e:
                            print(f"Stripe Meter Event Error: {e}")
                    except Exception as e:
                        print(f"Stripe Demo Charge Error: {e}")

                # Track the request in DB
                TrackedRequest.objects.create(
                    user=request.user,
                    usage_record_id=usage_record_id,
                    endpoint='/api/demo/'
                )

            return Response(recognition, status=HTTP_200_OK)
        return Response(file_serializer.errors, status=HTTP_400_BAD_REQUEST)


class UserEmailView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user = request.user
        obj = {'email': user.email}
        return Response(obj)


class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = request.user
        email_serializer = ChangeEmailSerializer(data=request.data)
        if email_serializer.is_valid():
            email = email_serializer.validated_data.get('email')
            confirm_email = email_serializer.validated_data.get('confirm_email')
            if email == confirm_email:
                user.email = email
                user.save()
                return Response({"email": email}, status=HTTP_200_OK)
            return Response({"message": "The emails did not match"}, status=HTTP_400_BAD_REQUEST)
        return Response(email_serializer.errors, status=HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = request.user
        password_serializer = ChangePasswordSerializer(data=request.data)
        if password_serializer.is_valid():
            password = password_serializer.validated_data.get('password')
            confirm_password = password_serializer.validated_data.get('confirm_password')
            current_password = password_serializer.validated_data.get('current_password')
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
            return Response({"message": "Incorrect current password"}, status=HTTP_400_BAD_REQUEST)
        return Response(password_serializer.errors, status=HTTP_400_BAD_REQUEST)


class UserDetailsView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # 1. Safely check if membership exists
        try:
            membership = user.membership
        except AttributeError:
            # This handles the 'User has no membership' error
            return Response({"message": "No membership found for this user."}, status=404)

        # 2. Setup your dates with timezone awareness
        today = timezone.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ensure month_start is aware
        if timezone.is_naive(month_start):
            from django.utils.timezone import make_aware
            month_start = make_aware(month_start)

        tracked_request_count = TrackedRequest.objects \
            .filter(user=user, timestamp__gte=month_start) \
            .count()
            
        amount_due = 0
        next_billing_date = membership.end_date
        
        # 3. Stripe Logic
        if user.is_member and user.stripe_customer_id and membership.stripe_subscription_id:
            try:
                upcoming_invoice = client.invoices.create_preview(
                    params={
                        "customer": user.stripe_customer_id,
                        "subscription": membership.stripe_subscription_id
                    }
                )
                amount_due = upcoming_invoice.amount_due / 100
            except Exception as e:
                print(f"Error fetching upcoming invoice preview: {e}")
                amount_due = 0

        obj = {
            'membershipType': membership.get_type_display() if membership else "None",
            'free_trial_end_date': membership.end_date if membership else None,
            'next_billing_date': next_billing_date,
            'api_request_count': tracked_request_count,
            'amount_due': amount_due
        }
        return Response(obj)

class SubscribeView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = request.user
        # get the user membership
        try:
            membership = user.membership
        except AttributeError:
             return Response({"message": "No membership found for this user."}, status=404)

        try:
            # get the stripe customer
            customer = stripe.Customer.retrieve(user.stripe_customer_id)
            serializer = SubscribeSerializer(data=request.data)

            # serialize post data (stripeToken)
            if serializer.is_valid():
                # create the stripe subscription
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{"plan": settings.STRIPE_PLAN_ID}]
                )

                # update the membership
                membership.stripe_subscription_id = subscription.get('id')
                
                # Get subscription item ID safely
                items = subscription.get('items', {}).get('data', [])
                if items:
                    item = items[0]
                    membership.stripe_subscription_item_id = item.get('id')
                    user.stripe_subscription_item_id = item.get('id') # Also save to user/membership logic if needed
                    print(f"Debug: Saved Subscription Item ID: {item.get('id')}")

                    # Set payment amount from plan/price
                    plan = item.get('plan') or item.get('price')
                    amount = (plan.get('amount') or plan.get('unit_amount') or 0) / 100
                else:
                    amount = 0

                membership.type = 'M'
                membership.start_date = timezone.now()
                
                period_end = subscription.get('current_period_end')
                if period_end:
                    membership.end_date = datetime.datetime.fromtimestamp(
                        period_end, tz=datetime.timezone.utc
                    )
                membership.save()

                # update the user
                user.is_member = True
                user.on_free_trial = False
                user.save()

                # create the payment
                payment = Payment()
                payment.amount = amount
                payment.user = user
                payment.save()

                return Response({'message': "success"}, status=HTTP_200_OK)

            else:
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        except stripe.error.CardError as e:
            return Response({'message': "Your card has been declined"}, status=HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
            return Response({'message': "There was an error with Stripe. You have not been billed."}, status=HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"message": f"An unexpected error occurred: {str(e)}"}, status=HTTP_400_BAD_REQUEST)



class CancelSubscription(APIView):
    permission_classes = (IsMember, )

    def post(self, request, *args, **kwargs):
        user = request.user
        membership = user.membership

        # update the stripe subscription
        try:
            client.subscriptions.cancel(membership.stripe_subscription_id)
        except Exception as e:
            return Response({"message": f"Stripe cancellation error: {str(e)}"}, status=HTTP_400_BAD_REQUEST)

        # update the user
        user.is_member = False
        user.save()

        # update the membership
        membership.type = "N"
        membership.save()

        return Response({'message': "Your subscription has been cancelled."}, status=HTTP_200_OK)


class ImageRecognitionView(APIView):
    permission_classes = (IsMember, )

    def post(self, request, *args, **kwargs):
        user = request.user
        membership = user.membership
        file_serializer = FileSerializer(data=request.data)

        if file_serializer.is_valid():
            file_obj = file_serializer.save()
            recognition = detect_faces(file_obj.file.path)

            usage_record_id = None
            if user.is_member and not user.on_free_trial:
                try:
                    # Use Meter Events API for new billing system
                    event = client.billing.meter_events.create(
                        params={
                            "event_name": settings.STRIPE_METER_EVENT_NAME,
                            "payload": {
                                "stripe_customer_id": user.stripe_customer_id,
                                "value": "1"
                            }
                        }
                    )
                    usage_record_id = event.identifier
                    print(f"Meter event recorded via Client: {usage_record_id}")
                except stripe.error.StripeError as e:
                    print(f"Stripe Meter Event Error: {e}")

            # Track the request in DB AFTER successful processing
            TrackedRequest.objects.create(
                user=user,
                usage_record_id=usage_record_id,
                endpoint='/api/image-recognition/'
            )

            return Response(recognition, status=HTTP_200_OK)
        return Response(file_serializer.errors, status=HTTP_400_BAD_REQUEST)

class APIKeyView(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, *args, **kwargs):
        user = request.user
        token_qs = Token.objects.filter(user=user)
        if token_qs.exists():
            token_serializer = TokenSerializer(token_qs, many=True)
            try:
                return Response(token_serializer.data, status=HTTP_200_OK)
            except:
                return Response({"message": "Did not receive correct data"}, status=HTTP_400_BAD_REQUEST)
        return Response({"message": "User does not exist"}, status=HTTP_400_BAD_REQUEST)