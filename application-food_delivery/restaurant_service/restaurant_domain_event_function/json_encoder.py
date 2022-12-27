import json
from decimal import Decimal
from boto3.dynamodb.types import Binary


class JSONEncoder(json.JSONEncoder):
    def default(self, obj) -> object:
        if isinstance(obj, Decimal):
            if int(obj) == obj:
                return int(obj)
            else:
                return float(obj)
        elif isinstance(obj, Binary):
            return obj.value
        elif isinstance(obj, bytes):
            return obj.decode()
        elif isinstance(obj, set):
            return list(obj)
        # Any other serializer
        return super(JSONEncoder, self).default(obj)
