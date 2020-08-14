from django.urls import path,re_path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'codeblog'

urlpatterns = [
    path('', views.index, name='index'),
    re_path('^user/(?P<username>[a-zA-Z0-9]+)/$', views.profile, name='profile'),
    re_path('^trending/$', views.trending_snippets, name='trending_snippets'),
    re_path('^trending/(?P<language_slug>[\w]+)/$', views.trending_snippets, name='trending_snippets'),
    re_path('^(?P<snippet_slug>[\d]+)/$', views.snippet_detail, name='snippet_detail'),
    re_path('^tag/(?P<tag>[\w-]+)/$', views.tag_list, name='tag_list'),
    re_path('^download/(?P<snippet_slug>[\d]+)/$', views.download_snippet, name='download_snippet'),
    re_path('^raw/(?P<snippet_slug>[\d]+)/$', views.raw_snippet, name='raw_snippet'),
    re_path('^contact/$', views.contact, name='contact'),
    re_path('^login/$', views.login, name='login'),
    re_path('^logout/$', views.logout, name='logout'),
    re_path('^user_details/$', views.user_details, name='user_details'),
    re_path('^delete/(?P<snippet_slug>[\d]+)/$', views.delete_snippet, name='delete_snippet'),
    re_path('^search/$', views.search, name='search'),
    re_path('^signup/$', views.signup, name='signup'),
    re_path('^activate/'
            '(?P<uid64>[0-9A-Za-z_\-]+)/'
            '(?P<token>[0-9A-Za-z]{1,13}'
            '-[0-9A-Za-z]{1,20})/$',
            views.activate_account, name='activate'),

    #password reset urls - views name are different in newer version and also include .as_view() after view name
    # also changes like success_url , reverse_lazy .....
    # parameters should be passed in as_view...

    re_path('^password-reset/$', auth_views.PasswordResetView.as_view(template_name= 'codeblog/password_reset.html',
     email_template_name= 'codeblog/email/password_reset_email.txt',
     subject_template_name= 'codeblog/email/password_reset_subject.txt',
     success_url= reverse_lazy('codeblog:password_reset_done')),
            name = 'password_reset'),

    re_path('^password-reset-done/$', auth_views.PasswordResetDoneView.as_view(template_name= 'codeblog/password_reset_done.html',),
            name = 'password_reset_done'),

    re_path('^password-reset-confirm/'
            '(?P<uid64>[0-9A-Za-z_\-]+)/'
            '(?P<token>[0-9A-Za-z]{1,13}'
            '-[0-9A-Za-z]{1,20})/$',
            auth_views.PasswordResetConfirmView.as_view(template_name= 'codeblog/password_reset_confirm.html',
            success_url= reverse_lazy('password_reset_complete'),),
            name = 'password_reset_confirm'),

    re_path('password-reset-complete/$',
            auth_views.PasswordResetCompleteView.as_view(template_name= 'codeblog/password_reset_complete.html'),
            name = 'password_reset_complete'),

    #password change urls

    re_path('^password-change/$', auth_views.PasswordChangeView.as_view(template_name= 'codeblog/password_change.html',
            success_url= reverse_lazy('codeblog:password_change_done'),),
            name = 'password_change'),

    re_path('^password-change/$', auth_views.PasswordChangeDoneView.as_view(template_name= 'codeblog/password_change_done.html'),
            name = 'password_change_done'),

    #settings url
    re_path('^settings/$', views.settings, name='settings'),
]
