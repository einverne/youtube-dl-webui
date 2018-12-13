#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask_login


class User(flask_login.UserMixin):
    def __init__(self, id=u'default'):
        self.id = id


class UserLoader(object):

    def __init__(self, dictionary=None):
        if dictionary is None:
            self.dictionary = {}
        else:
            self.dictionary = dictionary

    def get(self, user_id):
        try:
            return self.dictionary[user_id]
        except KeyError:
            return None

    def add(self, user_id, user_object):
        self.dictionary[user_id] = user_object
