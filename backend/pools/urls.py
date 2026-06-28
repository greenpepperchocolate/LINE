from django.urls import path

from . import views

# プレフィックス: /api/ (config/urls.py 側で include する想定)。
# path 先頭にスラッシュは付けない (crm.urls と同方針)。
urlpatterns = [
    # Traffic pools
    path("traffic-pools", views.traffic_pools_list),
    path("traffic-pools/<uuid:id>", views.traffic_pool_detail),
    path("traffic-pools/<uuid:id>/accounts", views.pool_accounts_list),
    path(
        "traffic-pools/<uuid:id>/accounts/<uuid:account_id>",
        views.pool_account_detail,
    ),
    # Image upload
    path("images", views.upload_image),
]
