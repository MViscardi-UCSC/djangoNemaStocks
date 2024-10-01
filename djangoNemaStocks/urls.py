"""
URL configuration for djangoNemaStocks project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, register_converter, include
from ArribereNemaStocks import views as nema_views
from profiles import views as profile_views

from ArribereNemaStocks.converters import WJAConverter

from django.conf import settings


register_converter(WJAConverter, 'wja')

urlpatterns = [
    # Testing:
    path('send_test_mail/', nema_views.send_test_mail, name='send_test_mail'),
    # Admin:
    path('admin/', admin.site.urls),
    # User Authentication:
    path('login/', profile_views.login_page, name='login_page'),
    path('login/', profile_views.login_page, name='login'),
    path('register/', profile_views.register, name='register'),
    path('user_page/', profile_views.user_page, name='user_page'),
    path('user_page/edit/', profile_views.edit_user_profile, name='edit_user_profile'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/profile/', profile_views.user_page, name='user_page'),
    # Navigation:
    path('', nema_views.index, name='index'),
    path('about/', nema_views.about, name='about'),
    # Strains:
    path('strain_search/', nema_views.strain_search, name='strain_search'),
    path('strain_assignments/', nema_views.strain_assignments, name='strain_assignments'),
    # path('strain_list/', nema_views.strain_list, name='strain_list'),
    path('strain_list_datatable/', nema_views.strain_list_datatable, name='strain_list_datatable'),
    path('new_strain/', nema_views.new_strain, name='new_strain'),
    path('edit_strain/<int:wja>/', nema_views.edit_strain, name='edit_strain'),
    path('strain_details/<int:wja>/', nema_views.strain_details, name='strain_details'),
    #BULK:
    path('bulk_upload_strains/', nema_views.bulk_upload_strains, name='bulk_upload_strains'),
    path('bulk_confirm_strains/', nema_views.bulk_confirm_strains, name='bulk_confirm_strains'),
    # Freeze Groups:
    # path('freeze_group_list/', nema_views.freeze_group_list, name='freeze_group_list'),
    # path('new_freeze_group/', nema_views.new_freeze_group, name='new_freeze_group'),
    # path('edit_freeze_group/<int:freeze_group_id>/', nema_views.edit_freeze_group, name='edit_freeze_group'),
    # path('freeze_group_details/<int:freeze_group_id>/', nema_views.freeze_group_details, name='freeze_group_details'),
    # Make Requests:
    path('freeze_request_form/', nema_views.freeze_request_form, name='freeze_request_form'),
    path('freeze_request_form/confirmation/', nema_views.freeze_request_confirmation, name='freeze_request_confirmation'),
    path('thaw_request_form/', nema_views.thaw_request_form, name='thaw_request_form'),
    path('thaw_request_form/confirmation/', nema_views.thaw_request_confirmation, name='thaw_request_confirmation'),
    # Requests Lists:
    path('outstanding_freeze_requests/', nema_views.outstanding_freeze_requests, name='outstanding_freeze_requests'),
    path('ongoing_freezes/', nema_views.ongoing_freezes, name='ongoing_freezes'),
    path('ongoing_thaws/', nema_views.ongoing_thaws, name='ongoing_thaws'),
    # path('freeze_request_management/requests:<str:freeze_request_ids>/', nema_views.freeze_request_management,
    #      name='freeze_request_management'),
    path('freeze_request_change_confirmation/action=<str:action>/requests=<str:freeze_request_ids>/',
         nema_views.freeze_request_change_confirmation, name='freeze_request_change_confirmation'),
    path('thaw_request_change_confirmation/action=<str:action>/requests=<str:thaw_request_ids>/',
         nema_views.thaw_request_change_confirmation, name='thaw_request_change_confirmation'),
    path('outstanding_thaw_requests/', nema_views.outstanding_thaw_requests, name='outstanding_thaw_requests'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
