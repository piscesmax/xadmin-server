#!/usr/bin/env python
# -*- coding:utf-8 -*-
# project : server
# filename : userinfo
# author : ly_13
# date : 6/16/2023
import logging

from django.utils.translation import gettext_lazy as _
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action

from common.base.magic import cache_response
from common.base.utils import get_choices_dict, AESCipherV2
from common.core.modelset import OwnerModelSet, UploadFileAction
from common.core.response import ApiResponse
from common.utils.verify_code import TokenTempCache
from settings.utils.password import check_password_rules
from settings.utils.security import ResetBlockUtil
from system.models import UserInfo
from system.serializers.userinfo import UserInfoSerializer
from system.utils.auth import verify_sms_email_code

logger = logging.getLogger(__name__)


class UserInfoView(OwnerModelSet, UploadFileAction):
    """用户个人信息管理"""
    serializer_class = UserInfoSerializer
    FILE_UPLOAD_FIELD = 'avatar'
    choices_models = [UserInfo]

    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return UserInfo.objects.filter(pk=self.request.user.pk)

    def get_cache_key(self, view_instance, view_method, request, args, kwargs):
        func_name = f'{view_instance.__class__.__name__}_{view_method.__name__}'
        return f"{func_name}_{request.user.pk}"

    @cache_response(timeout=600, key_func='get_cache_key')
    def retrieve(self, request, *args, **kwargs):
        data = super().retrieve(request, *args, **kwargs).data
        return ApiResponse(**data, choices_dict=get_choices_dict(UserInfo.GenderChoices.choices))

    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['old_password', 'sure_password'],
        properties={'old_password': openapi.Schema(description='旧密码', type=openapi.TYPE_STRING),
                    'sure_password': openapi.Schema(description='新密码', type=openapi.TYPE_STRING)}
    ), operation_description='修改个人密码')
    @action(methods=['post'], detail=False, url_path='reset-password')
    def reset_password(self, request, *args, **kwargs):
        old_password = request.data.get('old_password')
        sure_password = request.data.get('sure_password')
        if old_password and sure_password:
            instance = self.get_object()
            sure_password = AESCipherV2(instance.username).decrypt(sure_password)
            old_password = AESCipherV2(instance.username).decrypt(old_password)
            if not instance.check_password(old_password):
                return ApiResponse(code=1001, detail=_("Old password verification failed"))
            if not check_password_rules(sure_password, instance.is_superuser):
                return ApiResponse(code=1002, detail=_('Password does not match security rules'))
            instance.set_password(sure_password)
            instance.modifier = request.user
            instance.save(update_fields=['password', 'modifier'])
            return ApiResponse()
        return ApiResponse(code=1003)

    @action(methods=['post'], detail=False, url_path='bind')
    def bind(self, request, *args, **kwargs):
        query_key, target, verify_token = verify_sms_email_code(request, ResetBlockUtil)
        instance = UserInfo.objects.filter(**{query_key: target}).first()
        if instance:
            setattr(instance, query_key, '')
            instance.save(update_fields=(query_key,))
        setattr(request.user, query_key, target)
        request.user.save(update_fields=(query_key,))
        TokenTempCache.expired_cache_token(verify_token)
        return ApiResponse()
