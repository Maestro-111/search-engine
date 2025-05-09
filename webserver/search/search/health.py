# In your views.py
def health_check(request):
    # Check critical dependencies
    all_healthy = True

    # Check database connection
    try:
        from django.db import connections
        for name in connections:
            cursor = connections[name].cursor()
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row is None:
                all_healthy = False
    except:
        all_healthy = False

    # Return appropriate status code
    if all_healthy:
        from django.http import HttpResponse
        return HttpResponse("OK")
    else:
        from django.http import HttpResponseServerError
        return HttpResponseServerError("Unhealthy")