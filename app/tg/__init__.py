# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint

bp = Blueprint('tg', __name__)

from app.tg import routes