from django.http import JsonResponse
import json

from django.utils import timezone
from oauth2_provider.models import AccessToken
from django.views.decorators.csrf import csrf_exempt
from foodtaskerapp.serializers import RestaurantSerializer, MealSerializer, OrderSerializer
from foodtaskerapp.models import Restaurant, Meal, Order, OrderDetails

##############################
#Customer
##############################


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
                [{"meal_id":2,"quantity":2},{"meal_id":3, "quantity":3}]
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
            return JsonResponse ({"status":"failed", "error":"Your last order must be completed."})

        #Check Address:
        if not request.POST["address"]:
            return JsonResponse ({"status":"failed", "error":"Address is Required."})

        # Get Order Details
        order_details = json.loads(request.POST["order_details"])

        order_total = 0
        for meal in order_details:
            order_total += Meal.objects.get(id=meal["meal_id"]).price * meal["quantity"]

        # This checks to see if we have more than one Order Details.
        if len(order_details) > 0:

        #Step 1- Create an Order
            order = Order.objects.create(
                customer = customer,
                restaurant_id = request.POST["restaurant_id"],
                total = order_total,
                status = Order.COOKING,
                address = request.POST["address"]
            )

        #Step 2- Create Order Details
            for meal in order_details:
                OrderDetails.objects.create(
                    order = order,
                    meal_id = meal["meal_id"],
                    quantity = meal["quantity"],
                    sub_total = Meal.objects.get(id=meal["meal_id"]).price * meal["quantity"]
                )

            return JsonResponse({"status":"success"})

def customer_get_latest_order(request):
    access_token = AccessToken.objects.get(token=request.GET.get("access_token"),
        expires__gt = timezone.now())

    customer = access_token.user.customer

    order = OrderSerializer(Order.objects.filter(customer = customer).last()).data

    return JsonResponse({"order":order})

##############################
#Restaurant
##############################
def restaurant_order_notification(request, last_request_time):
    notification = Order.objects.filter(restaurant = request.user.restaurant,
        create_at__gt = last_request_time).count()

    return JsonResponse({"notification": notification})

##############################
#Driver
##############################

def driver_get_ready_orders(request):
    orders = OrderSerializer(
        Order.objects.filter(status = Order.READY, driver=None).order_by("-id"),
        many=True
    ).data

    return JsonResponse({"orders":orders})

@csrf_exempt
def driver_pick_order(request):
    #Params: access_token and oreder_id
    if request.method == "POST":
        access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
            expires__gt = timezone.now())
        #Get Driver
        driver = access_token.user.driver

        #Check to see that driver can only pick up one order at a time.
        if Order.objects.filter(driver=driver).exclude(status=Order.ONTHEWAY):
            return JsonResponse({"status":"failed", "error":"You can only pick one order at a time."})

    #Let the Driver see the order they can choose.
        try:
            order = Order.objects.get(
                id = request.POST["order_id"],
                driver = None,
                status = Order.READY
            )
        #This assign the order to the Driver.
            order.driver= driver
            order.status=Order.ONTHEWAY
            order.picked_at=timezone.now()
            order.save()

            return JsonResponse({"status":"success"})

    #This lets other Drivers know that this order as already been taken.
        except Order.DoesNotExist:
            return JsonResponse({"status":"fialed","error":"This order as been picked up by another Driver."})



def driver_get_complete_order(request):
    return JsonResponse({})

def driver_get_latest_order(request):
    return JsonResponse({})

def driver_get_revenue(request):
    return JsonResponse({})
