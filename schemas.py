# Importing all needed modules.
from marshmallow import Schema, fields, ValidationError


# Defining the Latency Schema.
class LatencySchema(Schema):
    # Defining the required schema fields.
    lock_time = fields.Number(required=True)
    queue_waiting_time = fields.Number(required=True)
    actual_processing = fields.Number(required=True)
    task_service_time = fields.Number(required=True)
    database_response_time = fields.Number(required=True)

    def validate_json(self, json_data : dict):
        '''
            This function validates the requests body.
                :param json_data: dict
                    The request body.
                :returns: dict, int
                    Returns the validated json or the errors in the json
                    and the status code.
        '''
        try:
            result = self.load(json_data)
        except ValidationError as err:
            return err.messages, 400
        return result, 200


# Defining the Saturation Schema.
class SaturationSchema(Schema):
    # Defining the required schema fields.
    cpu_utilization = fields.Number(required=True)
    ram_utilization = fields.Number(required=True)
    waiting_queue_length = fields.Number(required=True)
    thread_capacity = fields.Number(required=True)

    def validate_json(self, json_data : dict):
        '''
            This function validates the requests body.
                :param json_data: dict
                    The request body.
                :returns: dict, int
                    Returns the validated json or the errors in the json
                    and the status code.
        '''
        try:
            result = self.load(json_data)
        except ValidationError as err:
            return err.messages, 400
        return result, 200


# Defining the Errors Schema.
class ErrorsSchema(Schema):
    # Defining the required schema fields.
    request_status = fields.Integer(required=True)
    request_reason = fields.Str(required=True)
    db_error = fields.Str(required=True, allow_none=True)

    def validate_json(self, json_data : dict):
        '''
            This function validates the requests body.
                :param json_data: dict
                    The request body.
                :returns: dict, int
                    Returns the validated json or the errors in the json
                    and the status code.
        '''
        try:
            result = self.load(json_data)
        except ValidationError as err:
            return err.messages, 400
        return result, 200


# Defining the Traffic Schema.
class TrafficSchema(Schema):
    # Defining the required schema fields.
    write_query = fields.Integer(required=True)
    read_query = fields.Integer(required=True)

    def validate_json(self, json_data : dict):
        '''
            This function validates the requests body.
                :param json_data: dict
                    The request body.
                :returns: dict, int
                    Returns the validated json or the errors in the json
                    and the status code.
        '''
        try:
            result = self.load(json_data)
        except ValidationError as err:
            return err.messages, 400
        return result, 200


# Defining the Metrics Schema.
class MetricsSchema(Schema):
    # Defining the required schema fields.
    correlation_id = fields.Str(required=True)
    service_name = fields.Str(required=True)
    latency = fields.Nested(LatencySchema, required=False)
    saturation = fields.Nested(SaturationSchema, required=False)
    errors = fields.Nested(ErrorsSchema, required=True)
    traffic = fields.Nested(TrafficSchema, required=False)

    def validate_json(self, json_data : dict):
        '''
            This function validates the requests body.
                :param json_data: dict
                    The request body.
                :returns: dict, int
                    Returns the validated json or the errors in the json
                    and the status code.
        '''
        try:
            result = self.load(json_data)
        except ValidationError as err:
            return err.messages, 400
        return result, 200