import json
from typing import Any, Dict, List, Tuple, Union
from kybra import Opt

MethodType = str
ParamsType = Opt[Union[List[Any], Tuple[Any, ...], Dict[Any, Any]]]
IdType     = Opt[Union[int, str]]
DataType   = Dict[str, Any]
ResultType = Any

class JsonRpcError:
    def __init__(self, code: int, message: str, data: Opt[DataType] = None):
        self._data: DataType = dict()
        self.code    = code
        self.message = message
        self.data    = data

    @property
    def code(self) -> int:
        return self._data["code"]

    @code.setter
    def code(self, value: int):
        self._data["code"] = value

    @property
    def message(self) -> str:
        return self._data["message"]

    @message.setter
    def message(self, value: str):
        self._data["message"] = value

    @property
    def data(self) -> Opt[DataType]:
        return self._data.get("data")

    @data.setter
    def data(self, value: Opt[DataType]):
        if value is not None:
            self._data["data"] = value

    @classmethod
    def from_json(cls, json_data: Union[str, bytes, DataType]) -> "JsonRpcError":
        if isinstance(json_data, bytes):
            json_data = json_data.decode("utf-8")

        if isinstance(json_data, str):
            data: DataType = json.loads(json_data)
        else:
            data = json_data
        return cls(
            code=data["code"], message=data["message"], data=data.get("data"))

    @property
    def json(self) -> str:
        return json.dumps(self._data)

class JsonRpcRequest:
    version = "2.0"

    def __init__(self, method: MethodType, params: ParamsType = None,
                 id: IdType = None, is_notification: bool = False):
        self._data: DataType = dict()
        self.method = method
        self.params = params
        self.id     = id
        self.is_notification: bool = is_notification

    @property
    def data(self) -> DataType:
        data = dict(
            (k, v) for k, v in self._data.items()
            if not (k == "id" and self.is_notification)
        )
        data["jsonrpc"] = self.version
        return data

    @data.setter
    def data(self, value: DataType):
        self._data = value

    @property
    def method(self) -> MethodType:
        return self._data.get("method") or ""

    @method.setter
    def method(self, method: MethodType):
        self._data["method"] = method

    @property
    def params(self) -> ParamsType:
        return self._data.get("params")

    @params.setter
    def params(self, value: ParamsType):
        value = list(value) if isinstance(value, tuple) else value
        if value is not None:
            self._data["params"] = value

    @property
    def id(self) -> IdType:
        return self._data.get("id")

    @id.setter
    def id(self, value: IdType):
        self._data["id"] = value

    @property
    def json(self) -> str:
        return json.dumps(self.data)

    @property
    def bytes(self) -> bytes:
        return self.json.encode("utf-8")

class JsonRpcResponse:
    version = "2.0"

    def __init__(self, data: DataType):

        if "jsonrpc" not in data:
            raise ValueError("Missing version in response JSON RPC response")

        if data["jsonrpc"] != self.version:
            raise ValueError("Invalid version in JSON RPC response")

        if 'result' not in data and 'error' not in data:
            raise ValueError("Missing result or error field in JSON RPC response")

        if 'error' in data and not isinstance(data['error'], Union[dict, JsonRpcError]):
            raise ValueError("Invalid error data in JSON RPC response")

        self._data: DataType = data

    @property
    def data(self) -> DataType:
        data = dict((k, v) for k, v in self._data.items())
        return data

    @data.setter
    def data(self, value: DataType):
        self._data = value

    @property
    def result(self) -> ResultType:
        return self._data.get("result")

    @result.setter
    def result(self, value: ResultType):
        self._data.pop('error', None)
        self._data["result"] = value

    @property
    def error(self) -> Opt[JsonRpcError]:
        err = self._data.get("error")
        if err is isinstance(err, dict):
            return JsonRpcError.from_json(err)
        return err

    @error.setter
    def error(self, value: JsonRpcError):
        self._data.pop('value', None)
        if value:
            self._data["error"] = value

    @property
    def id(self):
        return self._data.get("id")

    @id.setter
    def id(self, value: IdType):
        self._data["id"] = value

    @classmethod
    def from_json(cls, json_data: Union[str, bytes]) -> "JsonRpcResponse":
        if isinstance(json_data, bytes):
            json_data = json_data.decode("utf-8")
        data: DataType = json.loads(json_data)
        return cls(data)