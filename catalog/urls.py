from django.urls import path
from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # path("api/irrigation/", views.irrigation_api, name="irrigation_api"),
    path("api/fields/<int:field_id>/fetch-et0/", views.fetch_et0_for_field, name = "fetch_et0_for_field"),
    path("api/fields/<int:field_id>/et0/", views.et0_history, name = "et0_history"),
    path("api/fields/", views.fields_list, name = "fields_list"),
    path("api/fields/<int:field_id>/irrigation/today/", views.irrigation_today),
    path("api/crops/", views.crops_list),
    path("api/fields/<int:field_id>/weather/current/", views.weather_current),
    path("api/sensors/moisture/", views.moisture_sensor_ingest, name="moisture_sensor_ingest"),
    path("api/fields/<int:field_id>/soil-moisture/latest/", views.latest_soil_moisture, name="latest_soil_moisture"),
]