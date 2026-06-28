from django.urls import path

from . import views

# プレフィックス: /api/  (config/urls.py 側で include する想定)
# 注意: 静的セグメント (report / track / count / stats 等) を
#       UUID パターンより先に定義する。
urlpatterns = [
    # Conversions (CV 計測)
    path("conversions/points", views.conversion_points_list),
    path("conversions/report", views.conversions_report),
    path("conversions/track", views.conversions_track),
    path("conversions/points/<uuid:id>", views.conversion_point_detail),
    # Affiliates (アフィリエイト)
    path("affiliates", views.affiliates_list),
    path("affiliates/<uuid:id>", views.affiliate_detail),
    path("affiliates/<uuid:id>/report", views.affiliate_report),
    # Scoring (リードスコアリング)
    path("scoring-rules", views.scoring_rules_list),
    path("scoring-rules/<uuid:id>", views.scoring_rule_detail),
    # Entry routes (流入経路)
    path("entry-routes", views.entry_routes_list),
    path("entry-routes/<uuid:id>", views.entry_route_detail),
    path("entry-routes/<uuid:id>/funnel", views.entry_route_funnel),
    # Automations (オートメーション)
    path("automations", views.automations_list),
    path("automations/<uuid:id>", views.automation_detail),
    path("automations/<uuid:id>/logs", views.automation_logs),
    # Segments (セグメント)
    path("segments/count", views.segments_count),
    # Duplicates (重複検出)
    path("duplicates/stats", views.duplicates_stats),
    # Analytics (リファラル/流入 集計)
    path("analytics/ref-summary", views.analytics_ref_summary),
    path("analytics/ref/<str:ref_code>", views.analytics_ref_detail),
]
