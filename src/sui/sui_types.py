"""Sui Types."""

from numbers import Number
from typing import TypeVar
from abstracts import ClientObjectDescriptor, ClientType, ClientPackage, ClientAbstractType


#   Constants
SUI_KEYPAIR_LEN = 88
SUI_ADDRESS_STRING_LEN = 42
# B64_KEYPAIR_LEN = 87
ED25519_KEYPAIR_BYTES_LEN = 64
ED25519_PUBLICKEY_BYTES_LEN = 32
ED25519_PRIVATEKEY_BYTES_LEN = 32

SECP256K1_KEYPAIR_BYTES_LEN = 65
SECP256K1_PUBLICKEY_BYTES_LEN = 33
SECP256K1_PRIVATEKEY_BYTES_LEN = 32


class SuiType(ClientAbstractType):
    """Base most SUI type."""


class SuiObjectDescriptor(ClientObjectDescriptor, SuiType):
    """Base SUI Type Descriptor."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base descriptor."""
        super().__init__(indata["objectId"])
        self._version = indata["version"]
        self._owner = indata["owner"]["AddressOwner"]
        self._digest = indata["digest"]
        self._previous_txn = indata["previousTransaction"]
        self._type_signature = indata["type"]

    @property
    def identifer(self) -> str:
        """Return the type identifer."""
        return self._identifier

    @property
    def version(self) -> int:
        """Return the types version."""
        return self._version

    @property
    def owner(self):
        """Return the types instance owner."""
        return self._owner

    @property
    def type_signature(self):
        """Return the types type."""
        return self._type_signature


class SuiDataDescriptor(SuiObjectDescriptor):
    """Sui Data base type."""


class SuiNftDescriptor(SuiObjectDescriptor):
    """Sui NFT base type."""


class SuiCoinDescriptor(SuiObjectDescriptor):
    """Sui Coin but not necessarily gas."""


class SuiNativeCoinDescriptor(SuiCoinDescriptor):
    """Sui gas is a coin."""


class SuiObjectType(ClientType, SuiType):
    """Base SUI Type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base type data."""
        super().__init__(indata["fields"]["id"]["id"])
        self._type_signature = indata["type"]
        self._data_type = indata["dataType"]
        self._is_transferable = indata["has_public_transfer"]

    @property
    def identifer(self) -> str:
        """Return the type identifer."""
        return self._identifier

    @property
    def data_type(self) -> str:
        """Return the data type."""
        return self._data_type

    @property
    def type_signature(self):
        """Return the types type."""
        return self._type_signature

    @property
    def is_transferable(self) -> bool:
        """Return the types transferability."""
        return self._is_transferable


class SuiNftType(SuiObjectType):
    """Sui NFT base type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base Nft type."""
        super().__init__(indata)
        self._description = indata["fields"]["description"]
        self._name = indata["fields"]["name"]
        self._url = indata["fields"]["url"]

    @property
    def name(self) -> str:
        """Get name for Nft."""
        return self._name

    @property
    def description(self) -> str:
        """Get description for Nft."""
        return self._description

    @property
    def url(self) -> str:
        """Get Url for Nft."""
        return self._url


DT = TypeVar("DT", bound="SuiDataType")


class SuiDataType(SuiObjectType):
    """Sui Data type."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base Data type."""
        super().__init__(indata)
        self._children = []
        self._data = {}
        split = self.type_signature.split("::", 2)
        self._data_definition = dict(zip(["package", "module", "structure"], split))
        for key, value in indata["fields"].items():
            if not key == "id":
                self._data[key] = value

    @property
    def data_definition(self) -> dict:
        """Get the data definition meta data."""
        return self._data_definition

    @property
    def package(self) -> str:
        """Get the data objects owning package id."""
        return self.data_definition["package"]

    @property
    def module(self) -> str:
        """Get the data objects owning module id."""
        return self.data_definition["module"]

    @property
    def structure(self) -> str:
        """Get the data objects structure id."""
        return self.data_definition["structure"]

    @property
    def data(self) -> dict:
        """Get the actual objects data."""
        return self._data

    @property
    def children(self) -> list[DT]:
        """Get the children of this data."""
        return self._children

    def add_child(self, child: DT) -> None:
        """Store data child owned by self."""
        self.children.append(child)


class SuiCoinType(SuiObjectType):
    """Sui Coin type but not necessarily gas type."""


class SuiGasType(SuiCoinType):
    """Sui gas is a coin."""

    def __init__(self, indata: dict) -> None:
        """Initialize the base type."""
        super().__init__(indata)
        self._balance = indata["fields"]["balance"]

    @property
    def balance(self) -> Number:
        """Get the balance for this coin object."""
        return self._balance


class SuiPackage(ClientPackage):
    """Sui package."""

    def __init__(self, package_id: str, blob) -> None:
        """Initialize a package construct."""
        super().__init__()
        self._package_id = package_id
        self._blob = blob

    @property
    def package_id(self) -> str:
        """Get the packages id."""
        return self._package_id


def parse_sui_object_descriptors(indata: dict) -> SuiObjectDescriptor:
    """Parse an inbound JSON string to a Sui type."""
    split = indata["type"].split("::", 2)
    if split[0] == "0x2":
        match split[1]:
            case "coin":
                split2 = split[2][5:-1].split("::")
                if split2[2] == "SUI":
                    return SuiNativeCoinDescriptor(indata)
                return SuiCoinDescriptor(indata)
            case "devnet_nft":
                if split[2] == "DevNetNFT":
                    return SuiNftDescriptor(indata)
    else:
        if len(split) == 3:
            return SuiDataDescriptor(indata)

    return SuiObjectDescriptor(indata)


def parse_sui_object_type(indata: dict) -> SuiObjectType:
    """Parse an inbound JSON string to a Sui type."""
    split = indata["type"].split("::", 2)

    if split[0] == "0x2":
        match split[1]:
            case "coin":
                split2 = split[2][5:-1].split("::")
                if split2[2] == "SUI":
                    return SuiGasType(indata)
                return SuiCoinType(indata)
            case "devnet_nft":
                if split[2] == "DevNetNFT":
                    return SuiNftType(indata)
    else:
        if len(split) == 3:
            return SuiDataType(indata)
    return SuiObjectType(indata)
