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
from django.urls import path, register_converter
from ArribereNemaStocks import views as nema_views
from ArribereNemaStocks.converters import WJAConverter

register_converter(WJAConverter, 'wja')

urlpatterns = [
    # Admin:
    path('admin/', admin.site.urls),
    # Navigation:
    path('', nema_views.index, name='index'),
    path('about/', nema_views.about, name='about'),
    # Strains:
    path('strain_list/', nema_views.strain_list, name='strain_list'),
    # path('new_strain/', views.new_strain, name='new_strain'),
    path('edit_strain/<int:wja>/', nema_views.edit_strain, name='edit_strain'),
    path('strain_details/<int:wja>/', nema_views.strain_details, name='strain_details'),
    # Tubes:
    path('tube_list/', nema_views.tube_list, name='tube_list'),
    # path('new_tube/', nema_views.new_tube, name='new_tube'),
    # path('edit_tube/<int:tube_id>/', nema_views.edit_tube, name='edit_tube'),
    # path('tube_details/<int:tube_id>/', nema_views.tube_details, name='tube_details'),
    # Boxes:
    # path('box_list/', nema_views.box_list, name='box_list'),
    # path('new_box/', nema_views.new_box, name='new_box'),
    # path('edit_box/<int:box_id>/', nema_views.edit_box, name='edit_box'),
    # path('box_details/<int:box_id>/', nema_views.box_details, name='box_details'),
    # Freeze Groups:
    # path('freeze_group_list/', nema_views.freeze_group_list, name='freeze_group_list'),
    # path('new_freeze_group/', nema_views.new_freeze_group, name='new_freeze_group'),
    # path('edit_freeze_group/<int:freeze_group_id>/', nema_views.edit_freeze_group, name='edit_freeze_group'),
    # path('freeze_group_details/<int:freeze_group_id>/', nema_views.freeze_group_details, name='freeze_group_details'),
    # Make Requests:
    path('thaw_request/', nema_views.thaw_request_view, name='thaw_request'),
    # Other:
    path('load_data_from_json/', nema_views.load_data_from_json, name='load_data_from_json'),
]
