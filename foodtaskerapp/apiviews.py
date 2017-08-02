from django.http import JsonResponse
import json

from django.utils import timezone
from oauth2_provider.models import AccessToken
from django.views.decorators.csrf import csrf_exempt
from foodtaskerapp.serializers import RestaurantSerializer, MealSerializer
from foodtaskerapp.models import Restaurant, Meal, Order, OrderDetails

def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
    Restaurant.objects.all().order_by("-id"),
    many = True,
    context = {"request":request}
    ).data

    return JsonResponse ({"restaurants":restaurants})

def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
    Meal.objects.filter(restaurant_id=restaurant_id).order_by("-id"),
    many= True,
    context = {"request":request}
    ).data

    return JsonResponse({"meals":meals})

@csrf_exempt
def customer_add_order(request):
    """
        params:
            access_token
            restaurant_id
            address
            order_details (json format. order_details example:)
                ({"meal":1,"quantity:2"}{"meal":2, "quantity":3})
            stride_token

    return JsonResponse ({"status":"success"})

    """
    if request.method == "POST":

        #Get Access Token
        access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
            expires__gt = timezone.now())

        #Get Porfile
        customer = access_token.user.customer

        #Check weather customer has any orders that is not delivered.
        if Order.objects.filter(customer = customer).exclude(status = Order.DELIVERED):
            return JsonResponse ({"status":"Failed", "error":"Your last order must be completed."})

        #Check Address:
        if not request.POST["address"]:
            return JsonResponse ({"status":"Failed", "error":"Address is Required."})

        # Get Order Details
        order_details = json.loads(request.POST["order_details"])

        order_total = 0
        for meal in order_details:
            order_total = Order.objects.get(id=meal["meal_id"]).price * meal["quantity"]

        # This checks to see if we have more than one Order Details.
        if len(order_details)> 0:

        #Step 1- Create an Order
            order= Order.objects.create(
            customer = customer,
            restaurant_id = request.POST["restaurant_id"],
            status = Order.COOKING,
            address = request.POST["address"]
            )

        #Step 2- Create Order Details
            for meal in order_details:
                order_details = OrderDetails.objects.create(
                order = order,
                meal_id = meal["meal_id"],
                quantity = meal["quantity"],
                sub_total = Meal.objects.get(
                id=meal["meal_id"]).price * meal["quantity"]
                )


            return JsonResponse({"status":"success"})

def customer_get_latest_order(request):
    return JsonResponse({})
