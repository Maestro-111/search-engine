
def health_check(request):

    """
    Health checkpoint for webserver container

    :param request:
    :return:

    """

    all_healthy = True

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

    if all_healthy:
        from django.http import HttpResponse
        return HttpResponse("OK")
    else:
        from django.http import HttpResponseServerError
        return HttpResponseServerError("Unhealthy")