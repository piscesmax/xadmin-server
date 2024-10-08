#!/usr/bin/env python
# -*- coding:utf-8 -*-
# project : server
# filename : user
# author : ly_13
# date : 6/16/2023
import logging

from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action

from common.base.utils import AESCipherV2
from common.core.filter import BaseFilterSet
from common.core.modelset import BaseModelSet, UploadFileAction, ImportExportDataAction
from common.core.response import ApiResponse
from settings.utils.password import check_password_rules
from settings.utils.security import LoginBlockUtil
from system.models import UserInfo
from system.serializers.user import UserSerializer
from system.utils import notify
from system.utils.modelset import ChangeRolePermissionAction

logger = logging.getLogger(__name__)


class UserFilter(BaseFilterSet):
    username = filters.CharFilter(field_name='username', lookup_expr='icontains')
    nickname = filters.CharFilter(field_name='nickname', lookup_expr='icontains')
    phone = filters.CharFilter(field_name='phone', lookup_expr='icontains')

    class Meta:
        model = UserInfo
        fields = ['username', 'nickname', 'phone', 'email', 'is_active', 'gender', 'pk', 'mode_type', 'dept']


class UserView(BaseModelSet, UploadFileAction, ChangeRolePermissionAction, ImportExportDataAction):
    """用户管理"""
    FILE_UPLOAD_FIELD = 'avatar'
    queryset = UserInfo.objects.all()
    serializer_class = UserSerializer

    ordering_fields = ['date_joined', 'last_login', 'created_time']
    filterset_class = UserFilter

    def perform_destroy(self, instance):
        if instance.is_superuser:
            raise Exception(_("The super administrator disallows deletion"))
        return instance.delete()

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['pks'],
        properties={'pks': openapi.Schema(description='主键列表', type=openapi.TYPE_ARRAY,
                                          items=openapi.Schema(type=openapi.TYPE_STRING))}
    ), operation_description='批量删除')
    @action(methods=['post'], detail=False, url_path='batch-delete')
    def batch_delete(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(is_superuser=False)
        return super().batch_delete(request, *args, **kwargs)

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['password'],
        properties={'password': openapi.Schema(description='新密码', type=openapi.TYPE_STRING)}
    ), operation_description='管理员重置用户密码')
    @action(methods=['post'], detail=True, url_path='reset-password')
    def reset_password(self, request, *args, **kwargs):
        instance = self.get_object()
        password = request.data.get('password')
        password = AESCipherV2(instance.username).decrypt(password)
        if not check_password_rules(password, instance.is_superuser):
            return ApiResponse(code=1001, detail=_('Password does not match security rules'))
        if instance and password:
            instance.set_password(password)
            instance.modifier = request.user
            instance.save(update_fields=['password', 'modifier'])
            notify.notify_error(users=instance, title="密码重置成功",
                                message="密码被管理员重置成功")
            return ApiResponse()
        return ApiResponse(code=1002)

    @action(methods=["post"], detail=True)
    def unblock(self, request, *args, **kwargs):
        instance = self.get_object()
        LoginBlockUtil.unblock_user(instance.username)
        return ApiResponse()
