from django.urls import path
from . import views

urlpatterns = [
    path(
        '_SIMULATION_/<str:INVESTMENT_TYPE>/<int:INITIAL_INVESTMENT_AMOUNT>/<int:PERIODIC_INVESTMENT_AMOUNT>/<str:PERIODIC_OPTIONS>/<int:HISTORY>/<str:HISTORY_OPTIONS>/<str:INTEREST_RATE>/<str:COMPOUND_FREQUENCY>/<str:EQUITIES>/<int:REOCCURING_AMOUNT>/<str:REOCCURING_FREQUENCY>/<str:INDEPEDENT_INVESTMENTS>/',
        views.simulation_view,
        name='simulation',
    ),

]

