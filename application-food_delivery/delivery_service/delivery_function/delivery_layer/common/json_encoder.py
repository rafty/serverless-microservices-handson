import json
from decimal import Decimal
import datetime
import time


class JSONEncoder(json.JSONEncoder):
    def default(self, obj) -> object:
        if isinstance(obj, Decimal):
            if int(obj) == obj:
                return int(obj)
            else:
                return float(obj)
        # elif isinstance(obj, Binary):
        #     return obj.value
        elif isinstance(obj, bytes):
            return obj.decode()
        elif isinstance(obj, set):
            return list(obj)
        # Any other serializer
        return super(JSONEncoder, self).default(obj)


class OldJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return str(obj)
        if isinstance(obj, datetime.date):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, time.struct_time):
            return datetime.datetime.fromtimestamp(time.mktime(obj))
        # Any other serializer
        return super(OldJSONEncoder, self).default(obj)

