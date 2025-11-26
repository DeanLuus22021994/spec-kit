"""
SOAP Client Library for 3rd Party API Integration
Python 3.14 with modern syntax and typing

Example usage:
    from soap import SoapClient

    async with SoapClient("https://api.example.com/service?wsdl") as client:
        result = await client.call("Operation", param1="value1")
"""

from .client import SoapClient, SoapError, WsdlError
from .config import SoapConfig
from .models import SoapRequest, SoapResponse

__all__ = [
    "SoapClient",
    "SoapError",
    "WsdlError",
    "SoapConfig",
    "SoapRequest",
    "SoapResponse",
]
__version__ = "1.0.0"
