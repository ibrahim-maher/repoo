# users/urls.py
from django.urls import path
from .views import user_views

app_name = 'users'

urlpatterns = [
    path('login/', user_views.login_view, name='login'),
    path('logout/', user_views.logout_view, name='logout'),
    path('edit_profile/', user_views.edit_profile_view, name='edit_profile'),
    path('profile/', user_views.profile_view, name='profile'),
    path('role_redirect/', user_views.role_based_dashboard, name='role_based_dashboard'),
    path('register/', user_views.register_view, name='register'),

    path("users/<int:user_id>/edit_permissions/", user_views.edit_permissions_view, name="edit_permissions"),

    path("users/", user_views.user_list_view, name="user_list"),
    path("users/<str:role>/", user_views.user_list_view, name="user_list_by_role"),
    path("/create/<str:role>", user_views.create_user, name="create_user"),
    path("users/<int:user_id>/edit/", user_views.edit_user, name="edit_user"),
    path("users/<int:user_id>/delete/", user_views.delete_user, name="delete_user"),
    path("users/import/", user_views.import_users_csv, name="import_users"),
    path("users/import/<str:role>/", user_views.import_users_csv, name="import_users_by_role"),
    path("users/export/", user_views.export_users_csv, name="export_users"),
    path("users/export/<str:role>/", user_views.export_users_csv, name="export_users_by_role"),
]
