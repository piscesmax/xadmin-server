#!/usr/bin/env python
# -*- coding:utf-8 -*-
# project : xadmin-server
# filename : utils
# author : ly_13
# date : 3/6/2024
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from rest_framework.utils import encoders


@async_to_sync
async def push_message(user_obj, message):
    room_group_name = f"{settings.CACHE_KEY_TEMPLATE.get('user_websocket_key')}_{user_obj.pk}"
    channel_layer = get_channel_layer()
    await channel_layer.group_send(room_group_name, {
        'type': 'push_message',
        'data': message if not isinstance(message, dict) else json.dumps(message, cls=encoders.JSONEncoder,
                                                                         ensure_ascii=False)
    })
@async_to_sync
async def check_message(user_obj, message):
    room_group_name = f"{settings.CACHE_KEY_TEMPLATE.get('user_websocket_key')}_{user_obj.pk}"
    channel_layer = get_channel_layer()
    group_channel = channel_layer._get_group_channel_name(room_group_name)
    group_channels = channel_layer.groups.get(group_channel, set())
    print(group_channels,group_channel)