from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class BaseSalesforceRequest:
    """
    Base class for all Salesforce request payloads.
    Provides helper methods for serialization and validation.
    """

    content_type: str = "JSON"
    line_ending: str = "LF"

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the dataclass to a dictionary, excluding None values.
        """
        return {k: v for k, v in asdict(self).items() if v is not None}

    def validate(self):
        """
        Placeholder for subclasses to implement custom validation logic.
        Raise ValueError if required fields are missing or invalid.
        """
        pass
