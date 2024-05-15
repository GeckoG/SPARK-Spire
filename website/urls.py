from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('register2/', views.register_userProfile, name='register2'),
    path('record/<int:pk>', views.individual_record, name='record'),
    path('delete_record/<int:pk>', views.delete_record, name='delete_record'),
    path('add_record/', views.add_record, name='add_record'),
    path('update_record/<int:pk>', views.update_record, name='update_record'),
    path('add_battery/', views.add_battery, name='add_battery'),
    path('load_positions/', views.load_positions, name="load_positions"),
    path('add_sport_position/', views.add_sport_position, name="add_sport_position"),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('get_usernames/', views.get_usernames, name='get_usernames'),
    path('get_assessment_units/', views.GetAssessmentUnitsView.as_view(), name='get_assessment_units'),

]