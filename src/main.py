import base64
import hashlib
from jrpc import JsonRpcRequest, JsonRpcResponse
from enum import IntFlag

from kybra import (
    Async,
    CallResult,
    ic,
    init,
    nat,
    nat8,
    Opt,
    Principal,
    Record,
    StableBTreeMap,
    text,
    query,
    update,
    void
)

from kybra.canisters.management import (
    HttpResponse,
    management_canister,
)

class AttestationFlag(IntFlag):
    NotAttested   = 0
    PassiveAuthn  = 1 # Account has valid passive authentication. i.e.: valid path EF.SOD track => DSC => CSCA
    ActiveAuthn   = 2 # Account has genuine passport chip attestation. i.e.: data for performing passive authn was not cloned.

ATTESTATION_MASK = AttestationFlag.PassiveAuthn | AttestationFlag.ActiveAuthn

class ActiveAuthnInfo(Record):
    count: nat8
    last_authn: text

class AuthnInfo(Record):
    attestation: nat
    country: text
    expires: text
    aa: Opt[ActiveAuthnInfo]

stable_storage = StableBTreeMap[text, text](
    memory_id=3, max_key_size=20, max_value_size=1_000
)

@init
def init_(owner: Principal) -> void:
    stable_storage.insert("owner", owner.to_str())

@query
def get_owner() -> Principal:
    return Principal.from_str(stable_storage.get("owner") or "")

@update
def set_owner(owner: Principal) -> void:
    if (ic.caller() != get_owner()):
        ic.trap("Only owner can set new owner")
    stable_storage.insert("owner", owner.to_str())

@query
def get_url() -> Opt[str]:
    return stable_storage.get("url")

@update
def set_url(url: str) -> void:
    if (ic.caller().bytes != get_owner().bytes):
        ic.trap("Only owner can set URL")
    stable_storage.insert("url", url.strip())

@update
def get_attestation(user: Principal) -> Async[Opt[AuthnInfo]]:
    url = get_url()
    if url is None:
        ic.trap("No URL set")

    def compute_sha2561(user: Principal):
        prinipalStr = user.to_str()
        byteData = prinipalStr.upper().encode()
        hash = hashlib.sha256(byteData).digest()[0:15]
        firstEnvelope = base64.b64encode(hash)
        secondEnvelope = base64.b64encode(firstEnvelope).decode('utf-8')
        ic.print("After double base64 encoding:")
        ic.print(secondEnvelope)
        return secondEnvelope

    def get_uid(user: Principal) -> str:
        #hash = hashlib.sha256(user.bytes).digest()[0:20]
        #return base64.b64encode(hash).decode('utf-8')
        #return is based on byte string of ascii presentation of the principal
        return compute_sha2561(user)

    rpcreq = JsonRpcRequest(
        method="port.get_account",
        params={"uid": get_uid(user)},
        id=67,
    )

    result: CallResult[HttpResponse] = yield management_canister.http_request(
        {
            "url": f"{url}",
            "max_response_bytes": 2_000,
            "method": {"post": None},
            "headers": [{"name":"Content-Type", "value":"application/json"}],
            "body": rpcreq.bytes,
            "transform": None,
        }
    ).with_cycles(90_000_000)

    if result.Err is not None:
        ic.trap(result.Err)

    rpcresp = JsonRpcResponse.from_json(result.Ok["body"])
    if rpcresp.error:
        ic.print(rpcresp.error)
        return None
    return AuthnInfo(rpcresp.result)

@update
def is_attested(user: Principal) -> Async[bool]:
    ai: Opt[AuthnInfo] = yield get_attestation(user)
    return ai is not None and (ai["attestation"] and ATTESTATION_MASK) != 0